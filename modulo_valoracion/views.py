import csv
from collections import Counter, defaultdict
from urllib.parse import quote

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from user.jwt_utils import get_user_from_request
from user.models import AREA_CHOICES, TIPO_USUARIO_CHOICES, Usuario

from .models import (
    Competencia,
    Pregunta,
    CicloEvaluacion,
    AsignacionEvaluacion,
    RespuestaEvaluacion,
    ResultadoEvaluacion,
    PlanAccion,
    ConfiguracionValoracion,
    TIPO_EVALUACION_CHOICES,
    TIPO_PREGUNTA_CHOICES,
    ESTADO_CICLO_CHOICES,
    ESTADO_PLAN_ACCION_CHOICES,
    ROL_EVALUADOR_CHOICES,
    SEMAFORO_CHOICES,
    ESCALA_LIKERT_CHOICES,
    calcular_semaforo,
)


# Orden y presentacion del semaforo organizacional
SEMAFORO_ORDEN = ["referente", "consolidado", "desarrollo", "acompanamiento", "intervencion"]
SEMAFORO_EMOJI = {
    "referente": "\U0001F7E2",       # verde
    "consolidado": "\U0001F7E1",     # amarillo
    "desarrollo": "\U0001F7E0",      # naranja
    "acompanamiento": "\U0001F534",  # rojo
    "intervencion": "⚫",        # negro
}


VALORACION_GROUP = "modulovaloracion"


# ----------------------------------------
# Auth helpers
# ----------------------------------------

def _require_login(request):
    user = get_user_from_request(request)
    if user is None:
        return None, redirect("login")
    return user, None


def _es_admin_global(user):
    if user is None:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    return getattr(user, "tipo_usuario", None) == "admin"


def _es_admin_people(user):
    """Admin People: acceso total al modulo (gestion de ciclos, preguntas, asignaciones)."""
    if _es_admin_global(user):
        return True
    return (
        getattr(user, "area", None) == "people"
        and getattr(user, "tipo_usuario", None) in {"admin", "lider"}
    )


def _es_bi_tech(user):
    """BI / Tech: configuracion tecnica (preguntas, competencias)."""
    if _es_admin_global(user):
        return True
    return getattr(user, "area", None) in {"bi", "tecnologia"}


def _es_ceo(user):
    """CEO: visibilidad total (lectura)."""
    if _es_admin_global(user):
        return True
    return (
        getattr(user, "area", None) == "ceo"
        or getattr(user, "tipo_usuario", None) == "admin"
    )


def _es_lider(user):
    if user is None:
        return False
    if _es_admin_global(user):
        return True
    if getattr(user, "tipo_usuario", None) == "lider":
        return True
    return Usuario.objects.filter(jefe_directo=user).exists()


def _puede_configurar(user):
    """Puede gestionar competencias, preguntas y ciclos."""
    return _es_admin_people(user) or _es_bi_tech(user)


def _puede_ver_todo(user):
    """Visibilidad total de resultados (CEO + Admin People)."""
    return _es_admin_people(user) or _es_ceo(user)


def _puede_ver_dashboard(user):
    """Dashboard de metricas e informes: Admin / People / CEO / BI / Tech."""
    return _puede_ver_todo(user) or _es_bi_tech(user)


def _puede_gestionar_planes(user):
    """Crear y dar seguimiento a planes de mejoramiento."""
    return _puede_ver_dashboard(user) or _es_lider(user)


# Areas que pueden habilitar/bloquear Mis Resultados y Planes de Accion.
# Cualquier persona de estas areas puede hacerlo, sin importar su rol.
AREAS_PUBLICACION_RESULTADOS = {"people", "bi", "tecnologia"}


def _puede_publicar_resultados(user):
    """People / Data (BI) / Tech / Admin: habilitan o bloquean los resultados."""
    if user is None:
        return False
    if _es_admin_global(user):
        return True
    return getattr(user, "area", None) in AREAS_PUBLICACION_RESULTADOS


def _resultados_publicados():
    return ConfiguracionValoracion.get_solo().resultados_publicados


def _puede_ver_resultados(user):
    """Mis Resultados y Planes de Accion estan bloqueados para el equipo
    hasta que People / Data / Tech / Admin los habilite."""
    if _puede_publicar_resultados(user):
        return True
    return _resultados_publicados()


def _progreso_evaluaciones():
    """Avance de respuestas de los ciclos activos (para habilitar al 100%)."""
    qs = AsignacionEvaluacion.objects.filter(activa=True, ciclo__estado="activo")
    total = qs.count()
    completadas = qs.filter(estado="completada").count()
    porcentaje = round(completadas * 100.0 / total, 1) if total else 0.0
    return {
        "total": total,
        "completadas": completadas,
        "pendientes": total - completadas,
        "porcentaje": porcentaje,
        "completo": total > 0 and completadas == total,
    }


def _bloqueo_resultados(request, user, seccion):
    """Devuelve la pantalla de bloqueo si el usuario aun no puede ver resultados."""
    if _puede_ver_resultados(user):
        return None
    ctx = {"seccion": seccion, "progreso": _progreso_evaluaciones()}
    ctx.update(_context_perms(user))
    return render(request, "valoracion_bloqueado.html", ctx, status=403)


def _require_role(request, predicate):
    user, redir = _require_login(request)
    if redir:
        return None, redir
    if not predicate(user):
        return user, render(request, "acceso_no_permitido.html", status=403)
    return user, None


def _context_perms(user):
    return {
        "es_admin_people": _es_admin_people(user),
        "es_bi_tech": _es_bi_tech(user),
        "es_ceo": _es_ceo(user),
        "es_lider": _es_lider(user),
        "puede_configurar": _puede_configurar(user),
        "puede_ver_todo": _puede_ver_todo(user),
        "puede_ver_dashboard": _puede_ver_dashboard(user),
        "puede_gestionar_planes": _puede_gestionar_planes(user),
        "puede_publicar_resultados": _puede_publicar_resultados(user),
        "resultados_publicados": _resultados_publicados(),
        "puede_ver_resultados": _puede_ver_resultados(user),
    }


# ----------------------------------------
# Home
# ----------------------------------------

def home_modulo_valoracion(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    asignaciones_pendientes = AsignacionEvaluacion.objects.filter(
        evaluador=user, estado__in=["pendiente", "en_progreso"], activa=True
    ).count()
    mis_resultados = ResultadoEvaluacion.objects.filter(evaluado=user).count()

    config = ConfiguracionValoracion.get_solo()
    ctx = {
        "asignaciones_pendientes": asignaciones_pendientes,
        "mis_resultados": mis_resultados,
        "config_valoracion": config,
        "progreso": _progreso_evaluaciones(),
        "publicacion_msg": request.session.pop("valoracion_publicacion_ok", None),
    }
    ctx.update(_context_perms(user))
    return render(request, "home_valoracion.html", ctx)


def toggle_publicacion_resultados(request):
    """Habilita o bloquea Mis Resultados y Planes de Accion para todo el equipo.
    Solo People / Data (BI) / Tech / Admin."""
    user, resp = _require_role(request, _puede_publicar_resultados)
    if resp:
        return resp
    if request.method != "POST":
        return redirect("modulo_valoracion:home_modulo_valoracion")

    habilitar = request.POST.get("accion") == "habilitar"
    config = ConfiguracionValoracion.get_solo()
    config.resultados_publicados = habilitar
    config.fecha_publicacion = timezone.now() if habilitar else None
    config.actualizado_por = user
    config.save()

    request.session["valoracion_publicacion_ok"] = (
        "Mis Resultados y Planes de Accion quedaron habilitados para todo el equipo."
        if habilitar else
        "Mis Resultados y Planes de Accion quedaron bloqueados para el equipo."
    )
    return redirect("modulo_valoracion:home_modulo_valoracion")


# ----------------------------------------
# Competencias
# ----------------------------------------

def gestionar_competencias(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    competencias = Competencia.objects.all()
    success = request.session.pop("valoracion_competencia_ok", None)
    return render(request, "valoracion_competencias.html", {
        "competencias": competencias,
        "success": success,
        **_context_perms(user),
    })


def crear_competencia(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    error = None
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        orden_raw = request.POST.get("orden", "0").strip()
        activa = request.POST.get("activa") == "on"

        if not codigo or not nombre:
            error = "Codigo y nombre son obligatorios."
        else:
            try:
                orden = int(orden_raw) if orden_raw else 0
                Competencia.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    orden=orden,
                    activa=activa,
                )
                request.session["valoracion_competencia_ok"] = "Competencia creada."
                return redirect("modulo_valoracion:gestionar_competencias")
            except ValueError:
                error = "El orden debe ser un numero entero."

    return render(request, "valoracion_competencia_form.html", {
        "error": error,
        "competencia": None,
        **_context_perms(user),
    })


def editar_competencia(request, competencia_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    competencia = get_object_or_404(Competencia, pk=competencia_id)
    error = None
    if request.method == "POST":
        competencia.codigo = request.POST.get("codigo", "").strip()
        competencia.nombre = request.POST.get("nombre", "").strip()
        competencia.descripcion = request.POST.get("descripcion", "").strip()
        orden_raw = request.POST.get("orden", "0").strip()
        competencia.activa = request.POST.get("activa") == "on"

        if not competencia.codigo or not competencia.nombre:
            error = "Codigo y nombre son obligatorios."
        else:
            try:
                competencia.orden = int(orden_raw) if orden_raw else 0
                competencia.save()
                request.session["valoracion_competencia_ok"] = "Competencia actualizada."
                return redirect("modulo_valoracion:gestionar_competencias")
            except ValueError:
                error = "El orden debe ser un numero entero."

    return render(request, "valoracion_competencia_form.html", {
        "error": error,
        "competencia": competencia,
        **_context_perms(user),
    })


def eliminar_competencia(request, competencia_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    if request.method == "POST":
        competencia = get_object_or_404(Competencia, pk=competencia_id)
        if competencia.preguntas.exists():
            request.session["valoracion_competencia_ok"] = (
                "No se puede eliminar: hay preguntas asociadas."
            )
        else:
            competencia.delete()
            request.session["valoracion_competencia_ok"] = "Competencia eliminada."
    return redirect("modulo_valoracion:gestionar_competencias")


# ----------------------------------------
# Preguntas
# ----------------------------------------

def gestionar_preguntas(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    filtro_tipo = request.GET.get("tipo", "")
    preguntas = Pregunta.objects.select_related("competencia")
    if filtro_tipo in {k for k, _ in TIPO_EVALUACION_CHOICES}:
        preguntas = preguntas.filter(tipo_evaluacion=filtro_tipo)
    success = request.session.pop("valoracion_pregunta_ok", None)
    return render(request, "valoracion_preguntas.html", {
        "preguntas": preguntas,
        "filtro_tipo": filtro_tipo,
        "tipo_choices": TIPO_EVALUACION_CHOICES,
        "success": success,
        **_context_perms(user),
    })


def _guardar_pregunta(pregunta, post):
    """Asigna datos del POST a la pregunta. Retorna (ok, error)."""
    competencia_id = post.get("competencia", "")
    enunciado = post.get("enunciado", "").strip()
    tipo_evaluacion = post.get("tipo_evaluacion", "")
    tipo_pregunta = post.get("tipo_pregunta", "likert")
    peso_raw = post.get("peso", "1").strip()
    orden_raw = post.get("orden", "0").strip()
    obligatoria = post.get("obligatoria") == "on"
    activa = post.get("activa") == "on"

    tipos_eval_validos = {k for k, _ in TIPO_EVALUACION_CHOICES}
    tipos_preg_validos = {k for k, _ in TIPO_PREGUNTA_CHOICES}

    if not all([competencia_id, enunciado, tipo_evaluacion]):
        return False, "Competencia, enunciado y tipo de evaluacion son obligatorios."
    if tipo_evaluacion not in tipos_eval_validos:
        return False, "Tipo de evaluacion no valido."
    if tipo_pregunta not in tipos_preg_validos:
        return False, "Tipo de pregunta no valido."

    try:
        competencia = Competencia.objects.get(pk=int(competencia_id))
    except (Competencia.DoesNotExist, ValueError):
        return False, "Competencia no valida."

    try:
        peso = float(peso_raw)
        orden = int(orden_raw) if orden_raw else 0
    except ValueError:
        return False, "Peso debe ser numero y orden entero."

    pregunta.competencia = competencia
    pregunta.enunciado = enunciado
    pregunta.tipo_evaluacion = tipo_evaluacion
    pregunta.tipo_pregunta = tipo_pregunta
    pregunta.peso = peso
    pregunta.orden = orden
    pregunta.obligatoria = obligatoria
    pregunta.activa = activa
    pregunta.save()
    return True, None


def crear_pregunta(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    error = None
    if request.method == "POST":
        pregunta = Pregunta()
        ok, error = _guardar_pregunta(pregunta, request.POST)
        if ok:
            request.session["valoracion_pregunta_ok"] = "Pregunta creada."
            return redirect("modulo_valoracion:gestionar_preguntas")
    return render(request, "valoracion_pregunta_form.html", {
        "pregunta": None,
        "competencias": Competencia.objects.filter(activa=True),
        "tipo_evaluacion_choices": TIPO_EVALUACION_CHOICES,
        "tipo_pregunta_choices": TIPO_PREGUNTA_CHOICES,
        "error": error,
        **_context_perms(user),
    })


def editar_pregunta(request, pregunta_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    pregunta = get_object_or_404(Pregunta, pk=pregunta_id)
    error = None
    if request.method == "POST":
        ok, error = _guardar_pregunta(pregunta, request.POST)
        if ok:
            request.session["valoracion_pregunta_ok"] = "Pregunta actualizada."
            return redirect("modulo_valoracion:gestionar_preguntas")
    return render(request, "valoracion_pregunta_form.html", {
        "pregunta": pregunta,
        "competencias": Competencia.objects.filter(activa=True),
        "tipo_evaluacion_choices": TIPO_EVALUACION_CHOICES,
        "tipo_pregunta_choices": TIPO_PREGUNTA_CHOICES,
        "error": error,
        **_context_perms(user),
    })


def eliminar_pregunta(request, pregunta_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    if request.method == "POST":
        pregunta = get_object_or_404(Pregunta, pk=pregunta_id)
        if pregunta.respuestas.exists():
            request.session["valoracion_pregunta_ok"] = (
                "No se puede eliminar: la pregunta ya tiene respuestas."
            )
        else:
            pregunta.delete()
            request.session["valoracion_pregunta_ok"] = "Pregunta eliminada."
    return redirect("modulo_valoracion:gestionar_preguntas")


# ----------------------------------------
# Ciclos
# ----------------------------------------

def _parse_dt_local(value):
    if not value:
        return None
    from django.utils import timezone as tz
    dt = parse_datetime(value)
    if not dt:
        return None
    if tz.is_naive(dt):
        dt = tz.make_aware(dt, tz.get_current_timezone())
    return dt


def gestionar_ciclos(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclos = CicloEvaluacion.objects.all()
    success = request.session.pop("valoracion_ciclo_ok", None)
    return render(request, "valoracion_ciclos.html", {
        "ciclos": ciclos,
        "success": success,
        **_context_perms(user),
    })


def _guardar_ciclo(ciclo, post, user_actual):
    nombre = post.get("nombre", "").strip()
    descripcion = post.get("descripcion", "").strip()
    tipo = post.get("tipo", "mixta")
    estado = post.get("estado", "programado")
    fecha_inicio = _parse_dt_local(post.get("fecha_inicio", "").strip())
    fecha_cierre = _parse_dt_local(post.get("fecha_cierre", "").strip())
    anonimato = post.get("anonimato") == "on"
    comentarios_obligatorios = post.get("comentarios_obligatorios") == "on"
    peso_jefe_raw = post.get("peso_jefe_lider", "60").strip()
    peso_equipo_raw = post.get("peso_equipo_lider", "40").strip()

    if not nombre:
        return False, "El nombre del ciclo es obligatorio."
    if not fecha_inicio or not fecha_cierre:
        return False, "Las fechas de inicio y cierre son obligatorias."
    if fecha_inicio > fecha_cierre:
        return False, "La fecha de inicio no puede ser posterior al cierre."
    if tipo not in {k for k, _ in TIPO_EVALUACION_CHOICES} | {"mixta"}:
        return False, "Tipo de ciclo no valido."
    if estado not in {k for k, _ in ESTADO_CICLO_CHOICES}:
        return False, "Estado no valido."

    try:
        peso_jefe = int(peso_jefe_raw)
        peso_equipo = int(peso_equipo_raw)
    except ValueError:
        return False, "Los pesos deben ser numeros enteros."
    if peso_jefe + peso_equipo != 100:
        return False, "Los pesos de jefe + equipo deben sumar 100."

    ciclo.nombre = nombre
    ciclo.descripcion = descripcion
    ciclo.tipo = tipo
    ciclo.estado = estado
    ciclo.fecha_inicio = fecha_inicio
    ciclo.fecha_cierre = fecha_cierre
    ciclo.anonimato = anonimato
    ciclo.comentarios_obligatorios = comentarios_obligatorios
    ciclo.peso_jefe_lider = peso_jefe
    ciclo.peso_equipo_lider = peso_equipo

    # Preguntas excluidas: las activas que NO vienen marcadas como incluidas.
    incluidas = {int(x) for x in post.getlist("preguntas_incluidas") if x.isdigit()}
    todas_activas = set(
        Pregunta.objects.filter(activa=True).values_list("id", flat=True)
    )
    ciclo.preguntas_excluidas = sorted(todas_activas - incluidas)

    if ciclo.pk is None:
        ciclo.creado_por = user_actual
    ciclo.save()
    return True, None


def _preguntas_por_tipo():
    """Agrupa las preguntas activas por tipo de evaluacion para el formulario de ciclo."""
    grupos = []
    for cod, label in TIPO_EVALUACION_CHOICES:
        preguntas = list(
            Pregunta.objects.filter(tipo_evaluacion=cod, activa=True)
            .select_related("competencia")
            .order_by("competencia__orden", "orden", "id")
        )
        grupos.append({"cod": cod, "label": label, "preguntas": preguntas})
    return grupos


def _generar_por_jerarquia(ciclo, areas):
    """Crea asignaciones basadas en jefe_directo para las areas dadas.
    Devuelve (creadas, omitidas)."""
    areas_set = set(areas)
    miembros = Usuario.objects.filter(
        is_active=True, area__in=areas_set, jefe_directo__isnull=False
    ).select_related("jefe_directo")

    creadas = 0
    omitidas = 0

    def _crear(ev, ed, rol, tipo):
        nonlocal creadas, omitidas
        if ev.pk == ed.pk or not ed.is_active or not ev.is_active:
            omitidas += 1
            return
        _, created = AsignacionEvaluacion.objects.get_or_create(
            ciclo=ciclo,
            evaluador=ev,
            evaluado=ed,
            defaults={"rol_evaluador": rol, "tipo_evaluacion": tipo},
        )
        if created:
            creadas += 1
        else:
            omitidas += 1

    tipo_ciclo = ciclo.tipo
    for miembro in miembros:
        jefe = miembro.jefe_directo
        if not jefe or jefe.area not in areas_set:
            omitidas += 1
            continue
        if tipo_ciclo == "lider":
            _crear(miembro, jefe, "equipo", "lider")
        elif tipo_ciclo == "operativo":
            _crear(jefe, miembro, "jefe", "operativo")
        else:  # mixta
            _crear(jefe, miembro, "jefe", "operativo")
            _crear(miembro, jefe, "equipo", "lider")

    return creadas, omitidas


def _aplicar_toggles_asignaciones(ciclo, post):
    """Activa/desactiva las asignaciones segun los checkboxes del formulario."""
    rendered = {int(x) for x in post.getlist("asignaciones_ids") if x.isdigit()}
    if not rendered:
        return
    activas = {int(x) for x in post.getlist("asignaciones_activas") if x.isdigit()}
    asignaciones = AsignacionEvaluacion.objects.filter(ciclo=ciclo, id__in=rendered)
    for a in asignaciones:
        nueva = a.id in activas
        if a.activa != nueva:
            a.activa = nueva
            a.save(update_fields=["activa"])


def _asignaciones_ciclo_form(ciclo):
    """Lista de asignaciones del ciclo para mostrar en el formulario."""
    if ciclo is None or ciclo.pk is None:
        return []
    return list(
        AsignacionEvaluacion.objects.filter(ciclo=ciclo)
        .select_related("evaluador", "evaluado")
        .order_by("evaluado__nombre", "evaluador__nombre")
    )


def crear_ciclo(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    error = None
    if request.method == "POST":
        ciclo = CicloEvaluacion()
        ok, error = _guardar_ciclo(ciclo, request.POST, user)
        if ok:
            areas = [a for a in request.POST.getlist("areas") if a in {k for k, _ in AREA_CHOICES}]
            if areas:
                creadas, _ = _generar_por_jerarquia(ciclo, areas)
                request.session["valoracion_ciclo_ok"] = f"Ciclo creado con {creadas} asignacion(es) generada(s)."
            else:
                request.session["valoracion_ciclo_ok"] = "Ciclo creado."
            _aplicar_toggles_asignaciones(ciclo, request.POST)
            return redirect("modulo_valoracion:gestionar_ciclos")
    return render(request, "valoracion_ciclo_form.html", {
        "ciclo": None,
        "tipo_choices": TIPO_EVALUACION_CHOICES + [("mixta", "Mixta")],
        "estado_choices": ESTADO_CICLO_CHOICES,
        "area_choices": AREA_CHOICES,
        "preguntas_por_tipo": _preguntas_por_tipo(),
        "excluidas": [],
        "asignaciones": [],
        "error": error,
        **_context_perms(user),
    })


def editar_ciclo(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloEvaluacion, pk=ciclo_id)
    error = None
    if request.method == "POST":
        ok, error = _guardar_ciclo(ciclo, request.POST, user)
        if ok:
            areas = [a for a in request.POST.getlist("areas") if a in {k for k, _ in AREA_CHOICES}]
            if areas:
                creadas, _ = _generar_por_jerarquia(ciclo, areas)
                request.session["valoracion_ciclo_ok"] = f"Ciclo actualizado con {creadas} asignacion(es) generada(s)."
            else:
                request.session["valoracion_ciclo_ok"] = "Ciclo actualizado."
            _aplicar_toggles_asignaciones(ciclo, request.POST)
            return redirect("modulo_valoracion:gestionar_ciclos")
    return render(request, "valoracion_ciclo_form.html", {
        "ciclo": ciclo,
        "tipo_choices": TIPO_EVALUACION_CHOICES + [("mixta", "Mixta")],
        "estado_choices": ESTADO_CICLO_CHOICES,
        "area_choices": AREA_CHOICES,
        "preguntas_por_tipo": _preguntas_por_tipo(),
        "excluidas": ciclo.preguntas_excluidas or [],
        "asignaciones": _asignaciones_ciclo_form(ciclo),
        "error": error,
        **_context_perms(user),
    })


# ----------------------------------------
# Asignaciones (quien evalua a quien) - vista simple por ciclo
# ----------------------------------------

def asignaciones_ciclo(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloEvaluacion, pk=ciclo_id)
    asignaciones = (
        AsignacionEvaluacion.objects.filter(ciclo=ciclo)
        .select_related("evaluador", "evaluado")
    )
    usuarios = Usuario.objects.filter(is_active=True).order_by("nombre", "apellido")
    success = request.session.pop("valoracion_asignacion_ok", None)
    return render(request, "valoracion_asignaciones.html", {
        "ciclo": ciclo,
        "asignaciones": asignaciones,
        "usuarios": usuarios,
        "rol_evaluador_choices": ROL_EVALUADOR_CHOICES,
        "tipo_evaluacion_choices": TIPO_EVALUACION_CHOICES,
        "area_choices": AREA_CHOICES,
        "success": success,
        **_context_perms(user),
    })


def crear_asignacion(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloEvaluacion, pk=ciclo_id)
    if request.method != "POST":
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    evaluador_id = request.POST.get("evaluador")
    evaluado_id = request.POST.get("evaluado")
    rol = request.POST.get("rol_evaluador")
    tipo = request.POST.get("tipo_evaluacion")

    if evaluador_id == evaluado_id:
        request.session["valoracion_asignacion_ok"] = "No se permite autoevaluacion."
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    try:
        evaluador = Usuario.objects.get(pk=int(evaluador_id))
        evaluado = Usuario.objects.get(pk=int(evaluado_id))
    except (Usuario.DoesNotExist, ValueError, TypeError):
        request.session["valoracion_asignacion_ok"] = "Usuario no valido."
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    if rol not in {k for k, _ in ROL_EVALUADOR_CHOICES}:
        request.session["valoracion_asignacion_ok"] = "Rol no valido."
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)
    if tipo not in {k for k, _ in TIPO_EVALUACION_CHOICES}:
        request.session["valoracion_asignacion_ok"] = "Tipo de evaluacion no valido."
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    AsignacionEvaluacion.objects.get_or_create(
        ciclo=ciclo,
        evaluador=evaluador,
        evaluado=evaluado,
        defaults={"rol_evaluador": rol, "tipo_evaluacion": tipo},
    )
    request.session["valoracion_asignacion_ok"] = "Asignacion registrada."
    return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)


def eliminar_asignacion(request, asignacion_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    asignacion = get_object_or_404(AsignacionEvaluacion, pk=asignacion_id)
    ciclo_id = asignacion.ciclo_id
    if request.method == "POST":
        if asignacion.respuestas.exists():
            request.session["valoracion_asignacion_ok"] = (
                "No se puede eliminar: la asignacion tiene respuestas."
            )
        else:
            asignacion.delete()
            request.session["valoracion_asignacion_ok"] = "Asignacion eliminada."
    return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo_id)


def generar_asignaciones_jerarquia(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloEvaluacion, pk=ciclo_id)
    if request.method != "POST":
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    areas = [a for a in request.POST.getlist("areas") if a in {k for k, _ in AREA_CHOICES}]
    if not areas:
        request.session["valoracion_asignacion_ok"] = "Selecciona al menos un area."
        return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)

    creadas, omitidas = _generar_por_jerarquia(ciclo, areas)
    msg = f"Generacion completada: {creadas} asignacion(es) creada(s)"
    if omitidas:
        msg += f", {omitidas} omitida(s) (ya existian o sin jefe activo)."
    else:
        msg += "."
    request.session["valoracion_asignacion_ok"] = msg
    return redirect("modulo_valoracion:asignaciones_ciclo", ciclo_id=ciclo.id)


# ----------------------------------------
# Mis evaluaciones (las que me toca responder)
# ----------------------------------------

def mis_evaluaciones(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    asignaciones = (
        AsignacionEvaluacion.objects.filter(evaluador=user, activa=True)
        .select_related("ciclo", "evaluado")
        .order_by("estado", "ciclo__fecha_cierre")
    )
    return render(request, "valoracion_mis_evaluaciones.html", {
        "asignaciones": asignaciones,
        **_context_perms(user),
    })

# ----------------------------------------
# Motor de calculo de resultados
# ----------------------------------------

def _puntaje_asignacion(asignacion):
    """Devuelve (puntaje_pct, detalle_por_pregunta) para una asignacion.
    puntaje_pct: 0-100 con base en preguntas likert y sus pesos.
    detalle_por_pregunta: dict {pregunta_id: valor}.
    """
    respuestas = (
        RespuestaEvaluacion.objects.filter(asignacion=asignacion)
        .select_related("pregunta")
    )
    suma_ponderada = 0.0
    suma_pesos_max = 0.0
    detalle = {}
    for r in respuestas:
        if r.pregunta.tipo_pregunta != "likert" or r.valor is None:
            continue
        peso = float(r.pregunta.peso or 1)
        suma_ponderada += float(r.valor) * peso
        suma_pesos_max += 5.0 * peso
        detalle[r.pregunta_id] = r.valor
    if suma_pesos_max == 0:
        return 0.0, detalle
    return (suma_ponderada / suma_pesos_max) * 100.0, detalle


def _promedio(valores):
    return sum(valores) / len(valores) if valores else None


def _detalle_items_evaluado(ciclo, evaluado, asignaciones=None):
    """Detalle item por item (pregunta) de un evaluado en un ciclo.

    Devuelve (items, competencias):
      - items: una fila por pregunta con el promedio global y desagregado por
        rol del evaluador (jefe / equipo / autoevaluacion) y la distribucion
        de calificaciones recibidas.
      - competencias: promedio agrupado por competencia.
    """
    if asignaciones is None:
        asignaciones = list(
            AsignacionEvaluacion.objects.filter(
                ciclo=ciclo, evaluado=evaluado, estado="completada", activa=True
            ).select_related("evaluador")
        )
    if not asignaciones:
        return [], []

    rol_por_asignacion = {a.id: a.rol_evaluador for a in asignaciones}
    respuestas = (
        RespuestaEvaluacion.objects.filter(asignacion__in=asignaciones)
        .select_related("pregunta", "pregunta__competencia")
    )

    acumulado = {}
    for r in respuestas:
        if r.pregunta.tipo_pregunta != "likert" or r.valor is None:
            continue
        d = acumulado.setdefault(r.pregunta_id, {
            "pregunta": r.pregunta,
            "todos": [],
            "jefe": [],
            "equipo": [],
            "auto": [],
            "dist": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        })
        valor = int(r.valor)
        d["todos"].append(valor)
        d["dist"][valor] = d["dist"].get(valor, 0) + 1
        rol = rol_por_asignacion.get(r.asignacion_id)
        if rol == "jefe":
            d["jefe"].append(valor)
        elif rol == "equipo":
            d["equipo"].append(valor)
        elif rol == "autoevaluacion":
            d["auto"].append(valor)

    escala_labels = dict(ESCALA_LIKERT_CHOICES)
    items = []
    for d in acumulado.values():
        pregunta = d["pregunta"]
        prom = _promedio(d["todos"]) or 0.0
        prom_jefe = _promedio(d["jefe"])
        prom_equipo = _promedio(d["equipo"])
        prom_auto = _promedio(d["auto"])
        externos = d["jefe"] + d["equipo"]
        prom_externos = _promedio(externos)
        brecha_auto = None
        if prom_auto is not None and prom_externos is not None:
            brecha_auto = round(prom_auto - prom_externos, 2)
        pct = prom / 5.0 * 100.0
        semaforo_item = calcular_semaforo(pct)
        items.append({
            "pregunta_id": pregunta.id,
            "competencia_codigo": pregunta.competencia.codigo,
            "competencia_nombre": pregunta.competencia.nombre,
            "competencia": "{}. {}".format(pregunta.competencia.codigo, pregunta.competencia.nombre),
            "competencia_orden": pregunta.competencia.orden,
            "orden": pregunta.orden,
            "enunciado": pregunta.enunciado,
            "peso": float(pregunta.peso or 1),
            "respuestas_count": len(d["todos"]),
            "promedio": round(prom, 2),
            "porcentaje": round(pct, 1),
            "semaforo": semaforo_item,
            "semaforo_emoji": SEMAFORO_EMOJI[semaforo_item],
            "nivel": escala_labels.get(int(round(prom)), ""),
            "promedio_jefe": round(prom_jefe, 2) if prom_jefe is not None else None,
            "promedio_equipo": round(prom_equipo, 2) if prom_equipo is not None else None,
            "promedio_auto": round(prom_auto, 2) if prom_auto is not None else None,
            "n_jefe": len(d["jefe"]),
            "n_equipo": len(d["equipo"]),
            "n_auto": len(d["auto"]),
            "brecha_auto": brecha_auto,
            "distribucion": [
                {"valor": v, "label": escala_labels.get(v, str(v)), "count": d["dist"].get(v, 0)}
                for v in (5, 4, 3, 2, 1)
            ],
        })
    items.sort(key=lambda x: (x["competencia_orden"], x["competencia_codigo"], x["orden"], x["pregunta_id"]))

    comp_acc = {}
    for it in items:
        c = comp_acc.setdefault(it["competencia"], {
            "codigo": it["competencia_codigo"],
            "nombre": it["competencia_nombre"],
            "orden": it["competencia_orden"],
            "suma": 0.0,
            "peso": 0.0,
            "items": 0,
            "respuestas": 0,
        })
        c["suma"] += it["promedio"] * it["peso"]
        c["peso"] += it["peso"]
        c["items"] += 1
        c["respuestas"] += it["respuestas_count"]

    competencias = []
    for etiqueta, c in comp_acc.items():
        prom = c["suma"] / c["peso"] if c["peso"] else 0.0
        pct = prom / 5.0 * 100.0
        sem = calcular_semaforo(pct)
        competencias.append({
            "codigo": c["codigo"],
            "nombre": c["nombre"],
            "etiqueta": etiqueta,
            "orden": c["orden"],
            "promedio": round(prom, 2),
            "porcentaje": round(pct, 1),
            "semaforo": sem,
            "semaforo_emoji": SEMAFORO_EMOJI[sem],
            "items": c["items"],
            "respuestas": c["respuestas"],
        })
    competencias.sort(key=lambda x: (x["orden"], x["codigo"]))
    return items, competencias


def _recalcular_resultado_evaluado(ciclo, evaluado):
    """Calcula y guarda el ResultadoEvaluacion (consolidado) de un evaluado.

    Todas las calificaciones recibidas se promedian por rol y luego se
    ponderan segun los pesos del ciclo, de forma que la persona queda con
    UN solo resultado por ciclo y no con una fila por evaluador.
    """
    asignaciones = list(
        AsignacionEvaluacion.objects.filter(
            ciclo=ciclo, evaluado=evaluado, estado="completada", activa=True
        ).select_related("evaluador")
    )
    if not asignaciones:
        ResultadoEvaluacion.objects.filter(ciclo=ciclo, evaluado=evaluado).delete()
        return None

    tipos = {a.tipo_evaluacion for a in asignaciones}
    tipo_eval = "lider" if "lider" in tipos else next(iter(tipos))

    scores_jefe = []
    scores_equipo = []
    scores_auto = []

    for a in asignaciones:
        pct, _detalle = _puntaje_asignacion(a)
        if a.rol_evaluador == "jefe":
            scores_jefe.append(pct)
        elif a.rol_evaluador == "equipo":
            scores_equipo.append(pct)
        elif a.rol_evaluador == "autoevaluacion":
            scores_auto.append(pct)

    avg_jefe = sum(scores_jefe) / len(scores_jefe) if scores_jefe else 0.0
    avg_equipo = sum(scores_equipo) / len(scores_equipo) if scores_equipo else 0.0
    avg_auto = sum(scores_auto) / len(scores_auto) if scores_auto else 0.0

    if tipo_eval == "lider" and scores_jefe and scores_equipo:
        peso_jefe = (ciclo.peso_jefe_lider or 60) / 100.0
        peso_equipo = (ciclo.peso_equipo_lider or 40) / 100.0
        porcentaje = avg_jefe * peso_jefe + avg_equipo * peso_equipo
    elif scores_jefe and scores_equipo:
        # Operativo con jefe y equipo: promedio simple de las dos miradas
        porcentaje = (avg_jefe + avg_equipo) / 2.0
    elif scores_jefe:
        porcentaje = avg_jefe
    elif scores_equipo:
        porcentaje = avg_equipo
    else:
        # Solo hay autoevaluacion: se usa como referencia
        porcentaje = avg_auto

    porcentaje = round(porcentaje, 2)
    puntaje_total = round(porcentaje / 100.0 * 5.0, 2)
    semaforo_cod = calcular_semaforo(porcentaje)

    items, competencias = _detalle_items_evaluado(ciclo, evaluado, asignaciones)

    fortalezas = [
        it["enunciado"][:120]
        for it in sorted(items, key=lambda x: x["promedio"], reverse=True)
        if it["promedio"] >= 4
    ][:5]
    brechas = [
        it["enunciado"][:120]
        for it in sorted(items, key=lambda x: x["promedio"])
        if it["promedio"] <= 2.5
    ][:5]

    resultado, _creado = ResultadoEvaluacion.objects.update_or_create(
        ciclo=ciclo,
        evaluado=evaluado,
        defaults={
            "tipo_evaluacion": tipo_eval,
            "puntaje_total": puntaje_total,
            "porcentaje": porcentaje,
            "semaforo": semaforo_cod,
            "puntaje_jefe": round(avg_jefe, 2),
            "puntaje_equipo": round(avg_equipo, 2),
            "puntaje_autoevaluacion": round(avg_auto, 2),
            "total_evaluadores": len(asignaciones),
            "evaluadores_jefe": len(scores_jefe),
            "evaluadores_equipo": len(scores_equipo),
            "evaluadores_auto": len(scores_auto),
            "detalle_competencias": competencias,
            "fortalezas": fortalezas,
            "brechas": brechas,
        },
    )
    return resultado


def consolidar_ciclo(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    if request.method != "POST":
        return redirect("modulo_valoracion:gestionar_ciclos")

    ciclo = get_object_or_404(CicloEvaluacion, pk=ciclo_id)
    evaluados_ids = list(
        AsignacionEvaluacion.objects.filter(ciclo=ciclo, estado="completada", activa=True)
        .values_list("evaluado_id", flat=True)
        .distinct()
    )
    procesados = 0
    for ev_id in evaluados_ids:
        try:
            evaluado = Usuario.objects.get(pk=ev_id)
        except Usuario.DoesNotExist:
            continue
        if _recalcular_resultado_evaluado(ciclo, evaluado) is not None:
            procesados += 1

    request.session["valoracion_ciclo_ok"] = (
        f"Resultados consolidados: {procesados} evaluado(s)."
    )
    return redirect("modulo_valoracion:gestionar_ciclos")


# ----------------------------------------
# Detalle de un resultado (drill-down)
# ----------------------------------------

def detalle_resultado(request, resultado_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    bloqueo = _bloqueo_resultados(request, user, "Mis Resultados")
    if bloqueo:
        return bloqueo

    resultado = get_object_or_404(
        ResultadoEvaluacion.objects.select_related("ciclo", "evaluado"),
        pk=resultado_id,
    )

    es_su_resultado = resultado.evaluado_id == user.pk
    es_su_jefe = (
        getattr(resultado.evaluado, "jefe_directo_id", None) == user.pk
    )
    if not (es_su_resultado or es_su_jefe or _puede_ver_todo(user)):
        return render(request, "acceso_no_permitido.html", status=403)

    asignaciones = list(
        AsignacionEvaluacion.objects.filter(
            ciclo=resultado.ciclo, evaluado=resultado.evaluado,
            estado="completada", activa=True,
        ).select_related("evaluador")
    )

    # ---- Segmentacion del detalle por rol del evaluador ----
    rol_filtro = request.GET.get("rol", "").strip()
    roles_validos = {k for k, _ in ROL_EVALUADOR_CHOICES}
    if rol_filtro in roles_validos:
        asignaciones_filtradas = [a for a in asignaciones if a.rol_evaluador == rol_filtro]
    else:
        rol_filtro = ""
        asignaciones_filtradas = asignaciones

    buscar = request.GET.get("q", "").strip()

    items, competencias = _detalle_items_evaluado(
        resultado.ciclo, resultado.evaluado, asignaciones_filtradas
    )
    if buscar:
        clave = buscar.lower()
        items = [
            it for it in items
            if clave in it["enunciado"].lower() or clave in it["competencia"].lower()
        ]

    # Ranking de items dentro del detalle
    items_ordenados = sorted(items, key=lambda x: x["promedio"], reverse=True)
    mejores_items = items_ordenados[:5]
    peores_items = list(reversed(items_ordenados[-5:])) if items_ordenados else []

    show_evaluador = not resultado.ciclo.anonimato or _puede_ver_todo(user)

    # ---- Desglose: puntaje de cada calificacion recibida ----
    calificaciones = []
    for a in asignaciones:
        pct, _detalle = _puntaje_asignacion(a)
        sem = calcular_semaforo(pct)
        calificaciones.append({
            "evaluador": str(a.evaluador) if show_evaluador else "Anonimo",
            "rol": a.get_rol_evaluador_display(),
            "rol_cod": a.rol_evaluador,
            "porcentaje": round(pct, 1),
            "puntaje": round(pct / 100.0 * 5.0, 2),
            "semaforo": sem,
            "semaforo_emoji": SEMAFORO_EMOJI[sem],
            "fecha": a.fecha_completada,
        })
    calificaciones.sort(key=lambda x: x["porcentaje"], reverse=True)

    # ---- Respuestas abiertas ----
    rol_por_asignacion = {a.id: a for a in asignaciones}
    abiertas = []
    for r in (
        RespuestaEvaluacion.objects.filter(asignacion__in=asignaciones)
        .exclude(respuesta_abierta="")
        .select_related("pregunta")
    ):
        a = rol_por_asignacion.get(r.asignacion_id)
        if a is None:
            continue
        abiertas.append({
            "enunciado": r.pregunta.enunciado,
            "texto": r.respuesta_abierta,
            "evaluador": str(a.evaluador) if show_evaluador else "Anonimo",
            "rol": a.get_rol_evaluador_display(),
        })

    observaciones = []
    for a in asignaciones:
        if a.observaciones_acuerdos:
            observaciones.append({
                "evaluador": str(a.evaluador) if show_evaluador else "Anonimo",
                "rol": a.get_rol_evaluador_display(),
                "texto": a.observaciones_acuerdos,
            })

    return render(request, "valoracion_detalle_resultado.html", {
        "resultado": resultado,
        "items": items,
        "competencias": competencias,
        "mejores_items": mejores_items,
        "peores_items": peores_items,
        "calificaciones": calificaciones,
        "abiertas": abiertas,
        "asignaciones_count": len(asignaciones),
        "asignaciones_filtradas_count": len(asignaciones_filtradas),
        "observaciones": observaciones,
        "rol_filtro": rol_filtro,
        "buscar": buscar,
        "rol_choices": ROL_EVALUADOR_CHOICES,
        "semaforo_emoji": SEMAFORO_EMOJI.get(resultado.semaforo, ""),
        **_context_perms(user),
    })


# ----------------------------------------
# Responder evaluacion (formulario dinamico)
# ----------------------------------------

def responder_evaluacion(request, asignacion_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    asignacion = get_object_or_404(
        AsignacionEvaluacion.objects.select_related("ciclo", "evaluado", "evaluador"),
        pk=asignacion_id,
    )

    if asignacion.evaluador_id != user.pk:
        return render(request, "acceso_no_permitido.html", status=403)

    ciclo = asignacion.ciclo
    ahora = timezone.now()
    ciclo_disponible = (
        asignacion.activa
        and ciclo.estado == "activo"
        and ciclo.fecha_inicio <= ahora <= ciclo.fecha_cierre
    )

    preguntas = list(
        Pregunta.objects.filter(
            tipo_evaluacion=asignacion.tipo_evaluacion, activa=True
        )
        .exclude(id__in=ciclo.preguntas_excluidas or [])
        .order_by("competencia__orden", "orden", "id")
    )

    respuestas_existentes = {
        r.pregunta_id: r
        for r in RespuestaEvaluacion.objects.filter(asignacion=asignacion)
    }

    error = None
    success = request.session.pop("valoracion_responder_ok", None)

    if request.method == "POST":
        if asignacion.estado == "completada":
            error = "Esta evaluacion ya fue enviada y no se puede modificar."
        elif not ciclo_disponible:
            error = "El ciclo no esta disponible para responder en este momento."
        else:
            accion = request.POST.get("accion", "borrador")
            observaciones = request.POST.get("observaciones_acuerdos", "").strip()
            faltantes_obligatorias = []

            with transaction.atomic():
                for pregunta in preguntas:
                    valor_raw = request.POST.get(f"valor_{pregunta.id}", "").strip()
                    texto_raw = request.POST.get(f"texto_{pregunta.id}", "").strip()

                    valor = None
                    if pregunta.tipo_pregunta == "likert" and valor_raw:
                        try:
                            valor_int = int(valor_raw)
                            if 1 <= valor_int <= 5:
                                valor = valor_int
                        except ValueError:
                            valor = None

                    if accion == "enviar" and pregunta.obligatoria:
                        if pregunta.tipo_pregunta == "likert" and valor is None:
                            faltantes_obligatorias.append(pregunta.id)
                        elif pregunta.tipo_pregunta == "abierta" and not texto_raw:
                            faltantes_obligatorias.append(pregunta.id)

                    RespuestaEvaluacion.objects.update_or_create(
                        asignacion=asignacion,
                        pregunta=pregunta,
                        defaults={"valor": valor, "respuesta_abierta": texto_raw},
                    )

                if accion == "enviar" and faltantes_obligatorias:
                    transaction.set_rollback(True)
                    error = (
                        f"Faltan {len(faltantes_obligatorias)} pregunta(s) obligatorias por responder."
                    )
                else:
                    asignacion.observaciones_acuerdos = observaciones
                    if asignacion.fecha_inicio_respuesta is None:
                        asignacion.fecha_inicio_respuesta = ahora
                    if accion == "enviar":
                        if ciclo.comentarios_obligatorios and not observaciones:
                            transaction.set_rollback(True)
                            error = "Las observaciones y acuerdos son obligatorios."
                        else:
                            asignacion.estado = "completada"
                            asignacion.fecha_completada = ahora
                            asignacion.save()
                            request.session["valoracion_responder_ok"] = (
                                "Evaluacion enviada. Gracias por completarla."
                            )
                            return redirect("modulo_valoracion:mis_evaluaciones")
                    else:
                        asignacion.estado = "en_progreso"
                        asignacion.save()
                        request.session["valoracion_responder_ok"] = (
                            "Borrador guardado. Puedes continuar mas tarde."
                        )
                        return redirect(
                            "modulo_valoracion:responder_evaluacion",
                            asignacion_id=asignacion.id,
                        )

        respuestas_existentes = {
            r.pregunta_id: r
            for r in RespuestaEvaluacion.objects.filter(asignacion=asignacion)
        }

    preguntas_data = []
    respondidas = 0
    for pregunta in preguntas:
        r = respuestas_existentes.get(pregunta.id)
        valor_actual = r.valor if r else None
        texto_actual = r.respuesta_abierta if r else ""
        respondida = valor_actual is not None or bool(texto_actual)
        if respondida:
            respondidas += 1

        opciones = []
        if pregunta.tipo_pregunta == "likert":
            for valor, label in ESCALA_LIKERT_CHOICES:
                opciones.append({
                    "valor": valor,
                    "label": label,
                    "seleccionado": valor_actual == valor,
                })

        preguntas_data.append({
            "id": pregunta.id,
            "enunciado": pregunta.enunciado,
            "tipo_pregunta": pregunta.tipo_pregunta,
            "obligatoria": pregunta.obligatoria,
            "valor_actual": valor_actual,
            "texto_actual": texto_actual,
            "opciones_likert": opciones,
        })

    total = len(preguntas)
    progreso_pct = int((respondidas / total) * 100) if total else 0
    bloquear_inputs = asignacion.estado == "completada" or not ciclo_disponible

    return render(request, "valoracion_responder.html", {
        "asignacion": asignacion,
        "ciclo": ciclo,
        "ciclo_disponible": ciclo_disponible,
        "preguntas_data": preguntas_data,
        "total": total,
        "respondidas": respondidas,
        "progreso_pct": progreso_pct,
        "bloquear_inputs": bloquear_inputs,
        "error": error,
        "success": success,
        **_context_perms(user),
    })


# ----------------------------------------
# Mis resultados (resultados propios)
# ----------------------------------------

def mis_resultados(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    bloqueo = _bloqueo_resultados(request, user, "Mis Resultados")
    if bloqueo:
        return bloqueo

    resultados = list(
        ResultadoEvaluacion.objects.filter(evaluado=user)
        .select_related("ciclo", "evaluado", "evaluado__jefe_directo")
        .order_by("-fecha_calculo")
    )
    consolidado_lista = _consolidar_personas(resultados)
    consolidado = consolidado_lista[0] if consolidado_lista else None
    return render(request, "valoracion_mis_resultados.html", {
        "resultados": resultados,
        "consolidado": consolidado,
        **_context_perms(user),
    })


# ----------------------------------------
# Resultados del equipo (lider)
# ----------------------------------------

def resultados_equipo(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not (_es_lider(user) or _puede_ver_todo(user)):
        return render(request, "acceso_no_permitido.html", status=403)

    if _puede_ver_todo(user):
        base = ResultadoEvaluacion.objects.all()
    else:
        subordinados_ids = list(
            Usuario.objects.filter(jefe_directo=user).values_list("id", flat=True)
        )
        base = ResultadoEvaluacion.objects.filter(evaluado_id__in=subordinados_ids)

    resultados, consolidado, filtros = _resultados_filtrados(request, base)
    resultados.sort(key=lambda r: (-r.ciclo.fecha_inicio.timestamp(), -float(r.porcentaje)))

    contexto = {
        "resultados": resultados,
        "consolidado": consolidado,
        "filtros": filtros,
        "qs_filtros": _query_string_filtros(filtros),
        "promedio_general": _prom([c["porcentaje"] for c in consolidado]),
    }
    contexto.update(_opciones_segmentacion())
    contexto.update(_context_perms(user))
    return render(request, "valoracion_resultados_equipo.html", contexto)


# ----------------------------------------
# Jerarquia (asignar jefes directos)
# ----------------------------------------

def gestionar_jerarquia(request):
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp

    query = request.GET.get("q", "").strip()
    usuarios = Usuario.objects.filter(is_active=True).select_related("jefe_directo")
    if query:
        usuarios = usuarios.filter(
            Q(nombre__icontains=query)
            | Q(apellido__icontains=query)
            | Q(email__icontains=query)
            | Q(cargo__icontains=query)
        )
    usuarios = usuarios.order_by("area", "nombre")

    todos_usuarios = Usuario.objects.filter(is_active=True).order_by("nombre", "apellido")
    success = request.session.pop("valoracion_jerarquia_ok", None)
    return render(request, "valoracion_jerarquia.html", {
        "usuarios": usuarios,
        "todos_usuarios": todos_usuarios,
        "query": query,
        "success": success,
        **_context_perms(user),
    })


def actualizar_jefe_directo(request, usuario_id):
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp
    if request.method != "POST":
        return redirect("modulo_valoracion:gestionar_jerarquia")

    objetivo = get_object_or_404(Usuario, pk=usuario_id)
    jefe_id = request.POST.get("jefe_directo", "").strip()
    cargo = request.POST.get("cargo", "").strip()

    if jefe_id:
        try:
            jefe = Usuario.objects.get(pk=int(jefe_id))
            if jefe.pk == objetivo.pk:
                request.session["valoracion_jerarquia_ok"] = (
                    "Un usuario no puede ser su propio jefe."
                )
                return redirect("modulo_valoracion:gestionar_jerarquia")
            objetivo.jefe_directo = jefe
        except (Usuario.DoesNotExist, ValueError):
            request.session["valoracion_jerarquia_ok"] = "Jefe no valido."
            return redirect("modulo_valoracion:gestionar_jerarquia")
    else:
        objetivo.jefe_directo = None

    objetivo.cargo = cargo or None
    objetivo.save()
    request.session["valoracion_jerarquia_ok"] = (
        f"Jerarquia actualizada para {objetivo}."
    )
    return redirect("modulo_valoracion:gestionar_jerarquia")


# ----------------------------------------
# Planes de Accion (listado)
# ----------------------------------------

def listar_planes_accion(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    bloqueo = _bloqueo_resultados(request, user, "Planes de Accion")
    if bloqueo:
        return bloqueo

    if _puede_ver_todo(user):
        planes = PlanAccion.objects.all()
    elif _es_lider(user):
        subordinados_ids = list(
            Usuario.objects.filter(jefe_directo=user).values_list("id", flat=True)
        )
        planes = PlanAccion.objects.filter(
            Q(responsable=user)
            | Q(resultado__evaluado_id__in=subordinados_ids)
            | Q(resultado__evaluado=user)
        )
    else:
        planes = PlanAccion.objects.filter(
            Q(responsable=user) | Q(resultado__evaluado=user)
        )

    planes = (
        planes.select_related("resultado", "resultado__evaluado", "responsable")
        .distinct()
        .order_by("estado", "fecha_compromiso")
    )

    return render(request, "valoracion_planes_accion.html", {
        "planes": planes,
        **_context_perms(user),
    })


# ----------------------------------------
# Dashboard de metricas e informes
# ----------------------------------------

def _parse_fecha_input(value, fin_dia=False):
    """Convierte un <input type=date> (YYYY-MM-DD) a datetime aware."""
    if not value:
        return None
    sufijo = "T23:59:59" if fin_dia else "T00:00:00"
    return _parse_dt_local(value + sufijo)


def _filtros_dashboard(request, base_qs=None):
    """Aplica la segmentacion sobre ResultadoEvaluacion.

    Segmentacion soportada: ciclo, fechas, area/direccion, equipo (jefe
    directo), rol organizacional, cargo, persona, tipo de evaluacion y
    semaforo. Devuelve (queryset, dict_filtros_seleccionados).
    """
    qs = base_qs if base_qs is not None else ResultadoEvaluacion.objects.all()
    qs = qs.select_related("ciclo", "evaluado", "evaluado__jefe_directo")

    ciclo_id = request.GET.get("ciclo", "").strip()
    area = request.GET.get("area", "").strip()
    equipo_id = request.GET.get("equipo", "").strip()
    rol = request.GET.get("rol", "").strip()
    cargo = request.GET.get("cargo", "").strip()
    persona_id = request.GET.get("persona", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    semaforo = request.GET.get("semaforo", "").strip()
    desde = request.GET.get("desde", "").strip()
    hasta = request.GET.get("hasta", "").strip()

    if ciclo_id.isdigit():
        qs = qs.filter(ciclo_id=int(ciclo_id))
    if area in {k for k, _ in AREA_CHOICES}:
        qs = qs.filter(evaluado__area=area)
    if equipo_id.isdigit():
        qs = qs.filter(evaluado__jefe_directo_id=int(equipo_id))
    if rol in {k for k, _ in TIPO_USUARIO_CHOICES}:
        qs = qs.filter(evaluado__tipo_usuario=rol)
    if cargo:
        qs = qs.filter(evaluado__cargo=cargo)
    if persona_id.isdigit():
        qs = qs.filter(evaluado_id=int(persona_id))
    if tipo in {k for k, _ in TIPO_EVALUACION_CHOICES}:
        qs = qs.filter(tipo_evaluacion=tipo)

    d_desde = _parse_fecha_input(desde)
    d_hasta = _parse_fecha_input(hasta, fin_dia=True)
    if d_desde:
        qs = qs.filter(ciclo__fecha_inicio__gte=d_desde)
    if d_hasta:
        qs = qs.filter(ciclo__fecha_inicio__lte=d_hasta)

    if semaforo not in {k for k, _ in SEMAFORO_CHOICES}:
        semaforo = ""

    filtros = {
        "ciclo": ciclo_id,
        "area": area,
        "equipo": equipo_id,
        "rol": rol,
        "cargo": cargo,
        "persona": persona_id,
        "tipo": tipo,
        "semaforo": semaforo,
        "desde": desde,
        "hasta": hasta,
    }
    return qs, filtros


def _opciones_segmentacion():
    """Catalogos para los selectores de segmentacion del dashboard."""
    cargos = list(
        Usuario.objects.exclude(cargo__isnull=True).exclude(cargo="")
        .values_list("cargo", flat=True).distinct().order_by("cargo")
    )
    jefes_ids = list(
        Usuario.objects.filter(reportes_directos__isnull=False)
        .values_list("id", flat=True).distinct()
    )
    equipos = Usuario.objects.filter(id__in=jefes_ids).order_by("nombre", "apellido")
    return {
        "area_choices": AREA_CHOICES,
        "tipo_choices": TIPO_EVALUACION_CHOICES,
        "rol_choices": TIPO_USUARIO_CHOICES,
        "semaforo_choices": SEMAFORO_CHOICES,
        "cargos": cargos,
        "equipos": equipos,
        "personas": Usuario.objects.filter(is_active=True).order_by("nombre", "apellido"),
        "ciclos": CicloEvaluacion.objects.all().order_by("-fecha_inicio"),
    }


def _query_string_filtros(filtros, excluir=()):
    partes = []
    for clave, valor in filtros.items():
        if clave in excluir or not valor:
            continue
        partes.append("%s=%s" % (clave, quote(str(valor))))
    return "&".join(partes)


def _prom(valores):
    return round(sum(valores) / len(valores), 1) if valores else 0.0


def _ponderado(pares):
    """Promedio ponderado a partir de una lista de (valor, peso)."""
    total_peso = sum(peso for _v, peso in pares)
    if not total_peso:
        valores = [v for v, _p in pares]
        return sum(valores) / len(valores) if valores else 0.0
    return sum(v * peso for v, peso in pares) / total_peso


def _consolidar_personas(resultados):
    """Consolida TODAS las calificaciones de una persona en un unico resultado.

    Cada ResultadoEvaluacion ya agrupa las calificaciones de un ciclo; aqui se
    ponderan los ciclos entre si por la cantidad de evaluadores que aportaron,
    de modo que una persona con 5 calificaciones ve un solo numero consolidado
    y no 5 filas independientes.
    """
    grupos = defaultdict(list)
    for r in resultados:
        grupos[r.evaluado_id].append(r)

    semaforo_display = dict(SEMAFORO_CHOICES)
    tipo_display = dict(TIPO_EVALUACION_CHOICES)
    rol_display = dict(TIPO_USUARIO_CHOICES)
    consolidado = []

    for rs in grupos.values():
        rs.sort(key=lambda r: r.ciclo.fecha_inicio)
        persona = rs[0].evaluado

        def peso(r):
            return max(int(r.total_evaluadores or 0), 1)

        porcentaje = _ponderado([(float(r.porcentaje), peso(r)) for r in rs])

        pares_jefe = [
            (float(r.puntaje_jefe), int(r.evaluadores_jefe or 0))
            for r in rs if (r.evaluadores_jefe or 0) > 0
        ]
        pares_equipo = [
            (float(r.puntaje_equipo), int(r.evaluadores_equipo or 0))
            for r in rs if (r.evaluadores_equipo or 0) > 0
        ]
        pares_auto = [
            (float(r.puntaje_autoevaluacion), int(r.evaluadores_auto or 0))
            for r in rs if (r.evaluadores_auto or 0) > 0
        ]

        prom_jefe = _ponderado(pares_jefe) if pares_jefe else None
        prom_equipo = _ponderado(pares_equipo) if pares_equipo else None
        prom_auto = _ponderado(pares_auto) if pares_auto else None

        tendencia = 0.0
        if len(rs) >= 2:
            tendencia = round(float(rs[-1].porcentaje) - float(rs[-2].porcentaje), 1)

        total_evaluadores = sum(int(r.total_evaluadores or 0) for r in rs)
        sem = calcular_semaforo(porcentaje)
        ultimo = rs[-1]

        # Consolidado por competencia a lo largo de los ciclos
        comp_acc = {}
        for r in rs:
            for c in (r.detalle_competencias or []):
                clave = c.get("etiqueta") or c.get("nombre") or ""
                acc = comp_acc.setdefault(clave, {
                    "codigo": c.get("codigo", ""),
                    "nombre": c.get("nombre", ""),
                    "etiqueta": clave,
                    "orden": c.get("orden", 0),
                    "pares": [],
                })
                acc["pares"].append((float(c.get("promedio") or 0), peso(r)))
        competencias = []
        for acc in comp_acc.values():
            prom_c = _ponderado(acc["pares"])
            pct_c = prom_c / 5.0 * 100.0
            sem_c = calcular_semaforo(pct_c)
            competencias.append({
                "codigo": acc["codigo"],
                "nombre": acc["nombre"],
                "etiqueta": acc["etiqueta"],
                "orden": acc["orden"],
                "promedio": round(prom_c, 2),
                "porcentaje": round(pct_c, 1),
                "semaforo": sem_c,
                "semaforo_emoji": SEMAFORO_EMOJI[sem_c],
            })
        competencias.sort(key=lambda x: (x["orden"], x["codigo"]))

        consolidado.append({
            "persona": persona,
            "persona_id": persona.pk,
            "area": persona.get_area_display() if persona.area else "Sin area",
            "area_cod": persona.area or "__sin__",
            "cargo": persona.cargo or "Sin cargo",
            "rol": rol_display.get(persona.tipo_usuario, "Sin rol"),
            "rol_cod": persona.tipo_usuario or "__sin__",
            "jefe": str(persona.jefe_directo) if persona.jefe_directo_id else "Sin jefe",
            "jefe_id": persona.jefe_directo_id,
            "tipo": tipo_display.get(ultimo.tipo_evaluacion, ultimo.tipo_evaluacion),
            "tipo_cod": ultimo.tipo_evaluacion,
            "ciclos": len(rs),
            "ciclos_nombres": ", ".join(r.ciclo.nombre for r in rs),
            "evaluaciones": total_evaluadores,
            "porcentaje": round(porcentaje, 1),
            "puntaje": round(porcentaje / 100.0 * 5.0, 2),
            "semaforo": sem,
            "semaforo_label": semaforo_display.get(sem, sem),
            "semaforo_emoji": SEMAFORO_EMOJI[sem],
            "promedio_jefe": round(prom_jefe, 1) if prom_jefe is not None else None,
            "promedio_equipo": round(prom_equipo, 1) if prom_equipo is not None else None,
            "promedio_auto": round(prom_auto, 1) if prom_auto is not None else None,
            "n_jefe": sum(int(r.evaluadores_jefe or 0) for r in rs),
            "n_equipo": sum(int(r.evaluadores_equipo or 0) for r in rs),
            "n_auto": sum(int(r.evaluadores_auto or 0) for r in rs),
            "tendencia": tendencia,
            "ultimo_resultado": ultimo,
            "ultimo_ciclo": ultimo.ciclo.nombre,
            "competencias": competencias,
            "resultados": rs,
        })

    consolidado.sort(key=lambda x: x["porcentaje"], reverse=True)
    return consolidado


def _agrupar_consolidado(consolidado, clave_cod, clave_label):
    """Promedio del consolidado individual agrupado por una dimension."""
    acc = defaultdict(list)
    etiquetas = {}
    for c in consolidado:
        acc[c[clave_cod]].append(c["porcentaje"])
        etiquetas[c[clave_cod]] = c[clave_label]
    filas = []
    for cod, vals in acc.items():
        prom = _prom(vals)
        sem = calcular_semaforo(prom)
        filas.append({
            "cod": cod,
            "label": etiquetas.get(cod, cod),
            "promedio": prom,
            "count": len(vals),
            "semaforo": sem,
            "emoji": SEMAFORO_EMOJI[sem],
        })
    filas.sort(key=lambda x: x["promedio"], reverse=True)
    return filas


def _competencias_organizacionales(resultados):
    """Promedio por competencia sobre el conjunto filtrado de resultados."""
    acc = {}
    for r in resultados:
        peso = max(int(r.total_evaluadores or 0), 1)
        for c in (r.detalle_competencias or []):
            clave = c.get("etiqueta") or c.get("nombre") or ""
            d = acc.setdefault(clave, {
                "etiqueta": clave,
                "codigo": c.get("codigo", ""),
                "nombre": c.get("nombre", ""),
                "orden": c.get("orden", 0),
                "pares": [],
                "personas": set(),
            })
            d["pares"].append((float(c.get("promedio") or 0), peso))
            d["personas"].add(r.evaluado_id)
    filas = []
    for d in acc.values():
        prom = _ponderado(d["pares"])
        pct = prom / 5.0 * 100.0
        sem = calcular_semaforo(pct)
        filas.append({
            "etiqueta": d["etiqueta"],
            "codigo": d["codigo"],
            "nombre": d["nombre"],
            "promedio": round(prom, 2),
            "porcentaje": round(pct, 1),
            "semaforo": sem,
            "emoji": SEMAFORO_EMOJI[sem],
            "personas": len(d["personas"]),
        })
    filas.sort(key=lambda x: x["porcentaje"], reverse=True)
    return filas


def _items_consolidados(resultados):
    """Detalle item por item para el conjunto filtrado (una fila por persona/pregunta).

    Se resuelve en pocas consultas para poder exportar sin degradar.
    """
    pares = {(r.ciclo_id, r.evaluado_id) for r in resultados}
    if not pares:
        return []
    ciclos_ids = {c for c, _e in pares}
    evaluados_ids = {e for _c, e in pares}

    asignaciones = (
        AsignacionEvaluacion.objects.filter(
            ciclo_id__in=ciclos_ids, evaluado_id__in=evaluados_ids,
            estado="completada", activa=True,
        ).select_related("ciclo", "evaluado")
    )
    asignaciones = [a for a in asignaciones if (a.ciclo_id, a.evaluado_id) in pares]
    if not asignaciones:
        return []

    info_asignacion = {
        a.id: (a.ciclo, a.evaluado, a.rol_evaluador) for a in asignaciones
    }
    respuestas = (
        RespuestaEvaluacion.objects.filter(asignacion_id__in=info_asignacion.keys())
        .select_related("pregunta", "pregunta__competencia")
    )

    acc = {}
    for r in respuestas:
        if r.pregunta.tipo_pregunta != "likert" or r.valor is None:
            continue
        ciclo, evaluado, rol = info_asignacion[r.asignacion_id]
        clave = (evaluado.pk, ciclo.pk, r.pregunta_id)
        d = acc.setdefault(clave, {
            "evaluado": evaluado,
            "ciclo": ciclo,
            "pregunta": r.pregunta,
            "todos": [], "jefe": [], "equipo": [], "auto": [],
        })
        valor = int(r.valor)
        d["todos"].append(valor)
        if rol == "jefe":
            d["jefe"].append(valor)
        elif rol == "equipo":
            d["equipo"].append(valor)
        elif rol == "autoevaluacion":
            d["auto"].append(valor)

    filas = []
    for d in acc.values():
        prom = _promedio(d["todos"]) or 0.0
        pct = prom / 5.0 * 100.0
        sem = calcular_semaforo(pct)
        persona = d["evaluado"]
        filas.append({
            "persona": persona,
            "area": persona.get_area_display() if persona.area else "Sin area",
            "cargo": persona.cargo or "Sin cargo",
            "jefe": str(persona.jefe_directo) if persona.jefe_directo_id else "Sin jefe",
            "rol": dict(TIPO_USUARIO_CHOICES).get(persona.tipo_usuario, "Sin rol"),
            "ciclo": d["ciclo"].nombre,
            "competencia": "%s. %s" % (
                d["pregunta"].competencia.codigo, d["pregunta"].competencia.nombre
            ),
            "enunciado": d["pregunta"].enunciado,
            "respuestas_count": len(d["todos"]),
            "promedio": round(prom, 2),
            "porcentaje": round(pct, 1),
            "semaforo": sem,
            "promedio_jefe": round(_promedio(d["jefe"]), 2) if d["jefe"] else None,
            "promedio_equipo": round(_promedio(d["equipo"]), 2) if d["equipo"] else None,
            "promedio_auto": round(_promedio(d["auto"]), 2) if d["auto"] else None,
        })
    filas.sort(key=lambda x: (str(x["persona"]), x["competencia"], x["enunciado"]))
    return filas


def _puntos_svg(serie, ancho=100.0, alto=40.0):
    """Genera la cadena de puntos para un <polyline> (escala 0-100)."""
    n = len(serie)
    if n == 0:
        return ""
    puntos = []
    for i, valor in enumerate(serie):
        x = (i / (n - 1)) * ancho if n > 1 else ancho / 2
        y = alto - (max(0.0, min(100.0, valor)) / 100.0) * alto
        puntos.append("%.1f,%.1f" % (x, y))
    return " ".join(puntos)


def _resultados_filtrados(request, base_qs=None):
    """Resultados + consolidado individual aplicando toda la segmentacion."""
    qs, filtros = _filtros_dashboard(request, base_qs)
    resultados = list(qs)
    consolidado = _consolidar_personas(resultados)
    if filtros["semaforo"]:
        consolidado = [c for c in consolidado if c["semaforo"] == filtros["semaforo"]]
        vigentes = {c["persona_id"] for c in consolidado}
        resultados = [r for r in resultados if r.evaluado_id in vigentes]
    return resultados, consolidado, filtros


def dashboard_organizacional(request):
    user, resp = _require_role(request, _puede_ver_dashboard)
    if resp:
        return resp

    resultados, consolidado, filtros = _resultados_filtrados(request)
    total = len(resultados)
    semaforo_display = dict(SEMAFORO_CHOICES)

    # ---- Promedio compania: promedio de los consolidados individuales ----
    promedio_compania = _prom([c["porcentaje"] for c in consolidado])
    semaforo_compania = calcular_semaforo(promedio_compania)
    personas_unicas = len(consolidado)
    calificaciones_totales = sum(c["evaluaciones"] for c in consolidado)

    # ---- Segmentacion ----
    por_area = _agrupar_consolidado(consolidado, "area_cod", "area")
    por_rol = _agrupar_consolidado(consolidado, "rol_cod", "rol")
    por_equipo = _agrupar_consolidado(consolidado, "jefe_id", "jefe")
    por_cargo = _agrupar_consolidado(consolidado, "cargo", "cargo")

    # ---- Lideres ----
    lideres = [c for c in consolidado if c["tipo_cod"] == "lider"]
    promedio_lideres = _prom([c["porcentaje"] for c in lideres])

    # ---- Distribucion semaforo (sobre el consolidado individual) ----
    conteo = {k: 0 for k in SEMAFORO_ORDEN}
    for c in consolidado:
        conteo[c["semaforo"]] = conteo.get(c["semaforo"], 0) + 1
    base = len(consolidado)
    distribucion = [{
        "cod": k,
        "label": semaforo_display.get(k, k),
        "emoji": SEMAFORO_EMOJI[k],
        "count": conteo[k],
        "pct": round(conteo[k] / base * 100) if base else 0,
    } for k in SEMAFORO_ORDEN]

    # ---- Top performers y brechas (consolidado, no calificaciones sueltas) ----
    top_performers = consolidado[:8]
    brechas_personas = list(reversed(consolidado[-8:])) if consolidado else []

    # ---- Competencias / items a nivel organizacional ----
    competencias_org = _competencias_organizacionales(resultados)

    # ---- Evolucion historica (por ciclo) ----
    ciclo_map = {}
    for r in resultados:
        c = r.ciclo
        ciclo_map.setdefault(c.id, {"nombre": c.nombre, "fecha": c.fecha_inicio, "vals": []})
        ciclo_map[c.id]["vals"].append(float(r.porcentaje))
    evolucion = sorted(
        ({
            "nombre": v["nombre"],
            "fecha": v["fecha"],
            "promedio": _prom(v["vals"]),
            "count": len(v["vals"]),
        } for v in ciclo_map.values()),
        key=lambda x: x["fecha"],
    )
    evol_points = _puntos_svg([e["promedio"] for e in evolucion])
    tendencia = 0.0
    if len(evolucion) >= 2:
        tendencia = round(evolucion[-1]["promedio"] - evolucion[-2]["promedio"], 1)

    # ---- Fortalezas y brechas recurrentes (texto) ----
    cont_f, cont_b = Counter(), Counter()
    for r in resultados:
        for f in (r.fortalezas or []):
            cont_f[f] += 1
        for b in (r.brechas or []):
            cont_b[b] += 1
    top_fortalezas = cont_f.most_common(6)
    top_brechas = cont_b.most_common(6)

    contexto = {
        "filtros": filtros,
        "qs_filtros": _query_string_filtros(filtros),
        "total": total,
        "personas_unicas": personas_unicas,
        "calificaciones_totales": calificaciones_totales,
        "promedio_compania": promedio_compania,
        "semaforo_compania": semaforo_compania,
        "semaforo_compania_label": semaforo_display.get(semaforo_compania, ""),
        "semaforo_compania_emoji": SEMAFORO_EMOJI[semaforo_compania],
        "promedio_lideres": promedio_lideres,
        "lideres_count": len(lideres),
        "consolidado": consolidado,
        "por_area": por_area,
        "por_rol": por_rol,
        "por_equipo": por_equipo,
        "por_cargo": por_cargo,
        "competencias_org": competencias_org,
        "distribucion": distribucion,
        "top_performers": top_performers,
        "brechas_personas": brechas_personas,
        "evolucion": evolucion,
        "evol_points": evol_points,
        "tendencia": tendencia,
        "top_fortalezas": top_fortalezas,
        "top_brechas": top_brechas,
    }
    contexto.update(_opciones_segmentacion())
    contexto.update(_context_perms(user))
    return render(request, "valoracion_dashboard.html", contexto)


def consolidado_individual(request):
    """Tabla completa del consolidado por persona con toda la segmentacion."""
    user, resp = _require_role(request, _puede_ver_dashboard)
    if resp:
        return resp

    resultados, consolidado, filtros = _resultados_filtrados(request)

    orden = request.GET.get("orden", "porcentaje").strip()
    claves_validas = {
        "porcentaje": lambda c: c["porcentaje"],
        "nombre": lambda c: str(c["persona"]).lower(),
        "area": lambda c: c["area"].lower(),
        "cargo": lambda c: c["cargo"].lower(),
        "equipo": lambda c: c["jefe"].lower(),
        "evaluaciones": lambda c: c["evaluaciones"],
    }
    if orden not in claves_validas:
        orden = "porcentaje"
    reverso = orden in {"porcentaje", "evaluaciones"}
    consolidado = sorted(consolidado, key=claves_validas[orden], reverse=reverso)

    ver_items = request.GET.get("items", "") == "1"
    items = _items_consolidados(resultados) if ver_items else []

    contexto = {
        "filtros": filtros,
        "qs_filtros": _query_string_filtros(filtros),
        "consolidado": consolidado,
        "items": items,
        "ver_items": ver_items,
        "orden": orden,
        "orden_opciones": [
            ("porcentaje", "Consolidado"),
            ("nombre", "Nombre"),
            ("area", "Area"),
            ("cargo", "Cargo"),
            ("equipo", "Equipo"),
            ("evaluaciones", "Calificaciones"),
        ],
        "total": len(resultados),
        "promedio_general": _prom([c["porcentaje"] for c in consolidado]),
    }
    contexto.update(_opciones_segmentacion())
    contexto.update(_context_perms(user))
    return render(request, "valoracion_consolidado.html", contexto)


def exportar_consolidado_csv(request):
    """Exporta el consolidado individual segmentado (CSV)."""
    user, resp = _require_role(request, _puede_ver_dashboard)
    if resp:
        return resp

    _resultados, consolidado, _filtros = _resultados_filtrados(request)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="supli_prime_consolidado.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "Persona", "Correo", "Area/Direccion", "Cargo", "Rol", "Equipo (jefe directo)",
        "Tipo evaluacion", "Ciclos", "Calificaciones recibidas",
        "Consolidado %", "Puntaje (0-5)", "Semaforo",
        "Prom. jefe %", "Prom. equipo %", "Autoevaluacion %", "Tendencia",
    ])
    for c in consolidado:
        writer.writerow([
            str(c["persona"]), c["persona"].email, c["area"], c["cargo"], c["rol"],
            c["jefe"], c["tipo"], c["ciclos"], c["evaluaciones"],
            c["porcentaje"], c["puntaje"], c["semaforo_label"],
            c["promedio_jefe"] if c["promedio_jefe"] is not None else "",
            c["promedio_equipo"] if c["promedio_equipo"] is not None else "",
            c["promedio_auto"] if c["promedio_auto"] is not None else "",
            c["tendencia"],
        ])
    return response


def exportar_items_csv(request):
    """Exporta el detalle item por item (pregunta) segmentado (CSV)."""
    user, resp = _require_role(request, _puede_ver_dashboard)
    if resp:
        return resp

    resultados, _consolidado, _filtros = _resultados_filtrados(request)
    filas = _items_consolidados(resultados)
    semaforo_display = dict(SEMAFORO_CHOICES)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="supli_prime_detalle_items.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "Persona", "Area/Direccion", "Cargo", "Rol", "Equipo (jefe directo)", "Ciclo",
        "Competencia", "Item evaluado", "Calificaciones", "Promedio (1-5)", "%",
        "Semaforo", "Jefe", "Equipo", "Autoevaluacion",
    ])
    for f in filas:
        writer.writerow([
            str(f["persona"]), f["area"], f["cargo"], f["rol"], f["jefe"], f["ciclo"],
            f["competencia"], f["enunciado"], f["respuestas_count"],
            f["promedio"], f["porcentaje"], semaforo_display.get(f["semaforo"], ""),
            f["promedio_jefe"] if f["promedio_jefe"] is not None else "",
            f["promedio_equipo"] if f["promedio_equipo"] is not None else "",
            f["promedio_auto"] if f["promedio_auto"] is not None else "",
        ])
    return response


def dashboard_individual(request, usuario_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    persona = get_object_or_404(Usuario, pk=usuario_id)
    es_self = persona.pk == user.pk
    es_su_jefe = getattr(persona, "jefe_directo_id", None) == user.pk
    if not (es_self or es_su_jefe or _puede_ver_dashboard(user)):
        return render(request, "acceso_no_permitido.html", status=403)

    resultados = list(
        ResultadoEvaluacion.objects.filter(evaluado=persona)
        .select_related("ciclo", "evaluado", "evaluado__jefe_directo")
        .order_by("ciclo__fecha_inicio")
    )
    actual = resultados[-1] if resultados else None

    # ---- Consolidado de TODAS las calificaciones recibidas ----
    consolidado_lista = _consolidar_personas(resultados)
    consolidado = consolidado_lista[0] if consolidado_lista else None

    # Evolucion individual
    evolucion = [{
        "id": r.id,
        "nombre": r.ciclo.nombre,
        "fecha": r.ciclo.fecha_inicio,
        "porcentaje": float(r.porcentaje),
        "semaforo": r.semaforo,
        "evaluadores": r.total_evaluadores,
    } for r in resultados]
    evol_points = _puntos_svg([e["porcentaje"] for e in evolucion])
    tendencia = 0.0
    if len(evolucion) >= 2:
        tendencia = round(evolucion[-1]["porcentaje"] - evolucion[-2]["porcentaje"], 1)

    # ---- Detalle de items del ciclo seleccionado (por defecto el ultimo) ----
    ciclo_sel = request.GET.get("ciclo", "").strip()
    resultado_detalle = actual
    if ciclo_sel.isdigit():
        for r in resultados:
            if r.ciclo_id == int(ciclo_sel):
                resultado_detalle = r
                break
    items = []
    competencias_detalle = []
    if resultado_detalle is not None:
        items, competencias_detalle = _detalle_items_evaluado(
            resultado_detalle.ciclo, persona
        )

    # Comentarios (observaciones de las asignaciones recibidas)
    comentarios = []
    puede_ver_eval = _puede_ver_todo(user)
    asignaciones = (
        AsignacionEvaluacion.objects.filter(evaluado=persona, estado="completada", activa=True)
        .exclude(observaciones_acuerdos="")
        .select_related("ciclo", "evaluador")
        .order_by("-fecha_completada")
    )
    for a in asignaciones:
        mostrar = not a.ciclo.anonimato or puede_ver_eval
        comentarios.append({
            "evaluador": str(a.evaluador) if mostrar else "Anonimo",
            "rol": a.get_rol_evaluador_display(),
            "ciclo": a.ciclo.nombre,
            "texto": a.observaciones_acuerdos,
        })

    # Planes de accion de la persona
    planes = (
        PlanAccion.objects.filter(resultado__evaluado=persona)
        .select_related("responsable", "resultado", "resultado__ciclo")
        .order_by("estado", "fecha_compromiso")
    )
    planes_total = planes.count()
    planes_cumplidos = sum(1 for p in planes if p.estado == "cumplido")
    cumplimiento = round(planes_cumplidos / planes_total * 100) if planes_total else 0

    responsables = Usuario.objects.filter(is_active=True).order_by("nombre", "apellido")

    semaforo_display = dict(SEMAFORO_CHOICES)
    plan_msg = request.session.pop("valoracion_plan_msg", None)
    return render(request, "valoracion_dashboard_individual.html", {
        "persona": persona,
        "plan_msg": plan_msg,
        "actual": actual,
        "consolidado": consolidado,
        "resultado_detalle": resultado_detalle,
        "items": items,
        "competencias_detalle": competencias_detalle,
        "ciclo_sel": ciclo_sel,
        "semaforo_actual_emoji": SEMAFORO_EMOJI[actual.semaforo] if actual else "",
        "evolucion": evolucion,
        "evol_points": evol_points,
        "tendencia": tendencia,
        "comentarios": comentarios,
        "planes": planes,
        "planes_total": planes_total,
        "planes_cumplidos": planes_cumplidos,
        "cumplimiento": cumplimiento,
        "responsables": responsables,
        "estado_plan_choices": ESTADO_PLAN_ACCION_CHOICES,
        "semaforo_display": semaforo_display,
        "puede_gestionar_planes": _puede_gestionar_planes(user) or es_su_jefe,
        **_context_perms(user),
    })


# ----------------------------------------
# Planes de accion: crear y seguimiento
# ----------------------------------------

def crear_plan_accion(request, resultado_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    resultado = get_object_or_404(
        ResultadoEvaluacion.objects.select_related("evaluado"), pk=resultado_id
    )
    es_su_jefe = getattr(resultado.evaluado, "jefe_directo_id", None) == user.pk
    if not (_puede_gestionar_planes(user) or es_su_jefe):
        return render(request, "acceso_no_permitido.html", status=403)

    bloqueo = _bloqueo_resultados(request, user, "Planes de Accion")
    if bloqueo:
        return bloqueo

    if request.method != "POST":
        return redirect("modulo_valoracion:dashboard_individual", usuario_id=resultado.evaluado_id)

    descripcion = request.POST.get("descripcion", "").strip()
    responsable_id = request.POST.get("responsable", "").strip()
    fecha_compromiso = request.POST.get("fecha_compromiso", "").strip()
    estado = request.POST.get("estado", "pendiente")
    observaciones = request.POST.get("observaciones", "").strip()

    estados_validos = {k for k, _ in ESTADO_PLAN_ACCION_CHOICES}
    if not descripcion or not responsable_id.isdigit() or not fecha_compromiso:
        request.session["valoracion_plan_msg"] = "Descripcion, responsable y fecha son obligatorios."
        return redirect("modulo_valoracion:dashboard_individual", usuario_id=resultado.evaluado_id)
    if estado not in estados_validos:
        estado = "pendiente"

    try:
        responsable = Usuario.objects.get(pk=int(responsable_id))
    except Usuario.DoesNotExist:
        request.session["valoracion_plan_msg"] = "Responsable no valido."
        return redirect("modulo_valoracion:dashboard_individual", usuario_id=resultado.evaluado_id)

    PlanAccion.objects.create(
        resultado=resultado,
        descripcion=descripcion,
        responsable=responsable,
        fecha_compromiso=fecha_compromiso,
        estado=estado,
        observaciones=observaciones,
        creado_por=user,
    )
    request.session["valoracion_plan_msg"] = "Plan de mejoramiento creado."
    return redirect("modulo_valoracion:dashboard_individual", usuario_id=resultado.evaluado_id)


def actualizar_plan_accion(request, plan_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    plan = get_object_or_404(
        PlanAccion.objects.select_related("resultado", "resultado__evaluado"), pk=plan_id
    )
    es_su_jefe = getattr(plan.resultado.evaluado, "jefe_directo_id", None) == user.pk
    if not (_puede_gestionar_planes(user) or es_su_jefe or plan.responsable_id == user.pk):
        return render(request, "acceso_no_permitido.html", status=403)

    bloqueo = _bloqueo_resultados(request, user, "Planes de Accion")
    if bloqueo:
        return bloqueo

    if request.method != "POST":
        return redirect("modulo_valoracion:dashboard_individual", usuario_id=plan.resultado.evaluado_id)

    estado = request.POST.get("estado", plan.estado)
    observaciones = request.POST.get("observaciones", "").strip()
    if estado in {k for k, _ in ESTADO_PLAN_ACCION_CHOICES}:
        plan.estado = estado
    plan.observaciones = observaciones
    plan.save()
    request.session["valoracion_plan_msg"] = "Plan de mejoramiento actualizado."
    return redirect("modulo_valoracion:dashboard_individual", usuario_id=plan.resultado.evaluado_id)
