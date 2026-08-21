from collections import OrderedDict

from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from user.jwt_utils import get_user_from_request
from user.models import AREA_CHOICES, Usuario

from .models import (
    CicloPulse,
    MiembroLeadershipTeam,
    ParticipacionReto,
    Pilar,
    PuntajeMensual,
    RetoSemanal,
    ESTADO_CICLO_CHOICES,
    ESTADO_PARTICIPACION_CHOICES,
    MESES_CHOICES,
    PILARES_BASE,
    PUNTAJE_MAXIMO_MENSUAL,
    PUNTAJE_MAXIMO_RETO,
    PUNTOS_CUMPLIMIENTO,
    SEMAFORO_CHOICES,
    SEMAFORO_EMOJI,
    SEMANAS_CHOICES,
    calcular_semaforo,
)


PULSE_GROUP = "leadershippulse"

SEMAFORO_ORDEN = ["champion", "alto", "consolidacion", "fortalecimiento", "intervencion"]
SEMAFORO_LABEL = dict(SEMAFORO_CHOICES)


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
    """Admin People: administra ciclos, retos, miembros y validaciones."""
    if _es_admin_global(user):
        return True
    return (
        getattr(user, "area", None) == "people"
        and getattr(user, "tipo_usuario", None) in {"admin", "lider"}
    )


def _es_ceo(user):
    """CEO: visibilidad total del Leadership Pulse."""
    if _es_admin_global(user):
        return True
    return getattr(user, "area", None) == "ceo"


def _es_bi_tech(user):
    """BI / Tech: configuracion tecnica (pilares) y metricas."""
    if _es_admin_global(user):
        return True
    return getattr(user, "area", None) in {"bi", "tecnologia"}


def _es_lider(user):
    if user is None:
        return False
    if _es_admin_global(user):
        return True
    if getattr(user, "tipo_usuario", None) == "lider":
        return True
    return Usuario.objects.filter(jefe_directo=user).exists()


def _es_miembro(user):
    """Miembro activo del Leadership Team."""
    if user is None:
        return False
    return MiembroLeadershipTeam.objects.filter(usuario=user, activo=True).exists()


def _puede_configurar(user):
    """Ciclos, retos y pilares."""
    return _es_admin_people(user) or _es_bi_tech(user)


def _puede_validar(user):
    """Validar evidencia e impacto de los retos."""
    return _es_admin_people(user)


def _puede_ver_todo(user):
    """Ranking completo y pulse de cualquier lider."""
    return _es_admin_people(user) or _es_ceo(user) or _es_bi_tech(user)


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
        "es_ceo": _es_ceo(user),
        "es_bi_tech": _es_bi_tech(user),
        "es_lider": _es_lider(user),
        "es_miembro": _es_miembro(user),
        "puede_configurar": _puede_configurar(user),
        "puede_validar": _puede_validar(user),
        "puede_ver_todo": _puede_ver_todo(user),
    }


# ----------------------------------------
# Helpers de dominio
# ----------------------------------------

def _ciclo_vigente():
    """Ciclo activo actual; si no hay, el ultimo ciclo registrado."""
    hoy = timezone.localdate()
    ciclo = (
        CicloPulse.objects.filter(
            estado="activo", fecha_inicio__lte=hoy, fecha_fin__gte=hoy
        ).first()
        or CicloPulse.objects.filter(estado="activo").first()
    )
    return ciclo or CicloPulse.objects.first()


def _asegurar_pilares_base():
    """Crea los 4 pilares oficiales si aun no existen."""
    for orden, (codigo, nombre, puntaje) in enumerate(PILARES_BASE, start=1):
        Pilar.objects.get_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "puntaje_max": puntaje, "orden": orden},
        )


def _miembros_activos():
    return (
        MiembroLeadershipTeam.objects.filter(activo=True)
        .select_related("usuario")
        .order_by("usuario__nombre", "usuario__apellido")
    )


def _asegurar_participaciones(reto):
    """Todos los miembros activos participan automaticamente en cada reto."""
    existentes = set(
        ParticipacionReto.objects.filter(reto=reto).values_list("lider_id", flat=True)
    )
    nuevas = [
        ParticipacionReto(reto=reto, lider=m.usuario)
        for m in _miembros_activos()
        if m.usuario_id not in existentes
    ]
    if nuevas:
        ParticipacionReto.objects.bulk_create(nuevas)
    return len(nuevas)


def _sincronizar_participaciones_ciclo(ciclo):
    total = 0
    for reto in ciclo.retos.filter(activo=True):
        total += _asegurar_participaciones(reto)
    return total


def _consolidar_ciclo(ciclo):
    """Consolida el puntaje mensual de cada lider y arma el ranking."""
    pilares = list(Pilar.objects.filter(activo=True))
    retos = list(ciclo.retos.filter(activo=True).select_related("pilar"))
    participaciones = (
        ParticipacionReto.objects.filter(reto__ciclo=ciclo, reto__activo=True)
        .select_related("reto", "reto__pilar", "lider")
    )

    por_lider = {}
    for p in participaciones:
        por_lider.setdefault(p.lider, []).append(p)

    # Asegura que todo miembro activo aparezca aunque no tenga participaciones
    for m in _miembros_activos():
        por_lider.setdefault(m.usuario, [])

    total_retos = len(retos)
    resultados = []
    for lider, items in por_lider.items():
        detalle = OrderedDict()
        for pilar in pilares:
            detalle[pilar.codigo] = {
                "nombre": pilar.nombre,
                "puntaje": 0,
                "max": pilar.puntaje_max,
            }

        puntaje_total = 0
        retos_registrados = 0
        retos_participados = 0
        retos_cumplidos = 0
        for p in items:
            if not p.esta_registrado:
                continue
            retos_registrados += 1
            if p.participo:
                retos_participados += 1
            if p.cumplio:
                retos_cumplidos += 1
                puntaje_total += p.puntaje_total
                codigo = p.reto.pilar.codigo
                if codigo in detalle:
                    detalle[codigo]["puntaje"] += p.puntaje_total

        puntaje_total = min(puntaje_total, ciclo.puntaje_max)
        pct_participacion = _porcentaje(retos_participados, total_retos)
        pct_cumplimiento = _porcentaje(retos_cumplidos, total_retos)
        registro, _ = PuntajeMensual.objects.update_or_create(
            ciclo=ciclo,
            lider=lider,
            defaults={
                "puntaje_total": puntaje_total,
                "detalle_pilares": detalle,
                "retos_evaluados": total_retos,
                "retos_registrados": retos_registrados,
                "retos_participados": retos_participados,
                "retos_cumplidos": retos_cumplidos,
                "pct_participacion": pct_participacion,
                "pct_cumplimiento": pct_cumplimiento,
                # El semaforo se lee sobre el % de cumplimiento para que sea
                # comparable aunque el ciclo aun no tenga sus 4 retos cargados.
                "semaforo": calcular_semaforo(pct_cumplimiento),
            },
        )
        resultados.append(registro)

    resultados.sort(
        key=lambda r: (-r.pct_cumplimiento, -r.pct_participacion, str(r.lider))
    )
    for posicion, registro in enumerate(resultados, start=1):
        if registro.posicion != posicion:
            registro.posicion = posicion
            registro.save(update_fields=["posicion"])
    return len(resultados)


def _porcentaje(parte, total):
    """Porcentaje 0-100 con un decimal; 0 si no hay retos asignados."""
    if not total:
        return 0.0
    return round(parte * 100.0 / total, 1)


def _decorar_puntajes(queryset):
    """Agrega etiqueta y emoji de semaforo a cada puntaje para la plantilla."""
    filas = []
    for p in queryset:
        filas.append({
            "obj": p,
            "lider": p.lider,
            "puntaje": p.puntaje_total,
            "posicion": p.posicion,
            "asignados": p.retos_evaluados,
            "registrados": p.retos_registrados,
            "participados": p.retos_participados,
            "cumplidos": p.retos_cumplidos,
            "pct_participacion": p.pct_participacion,
            "pct_cumplimiento": p.pct_cumplimiento,
            "semaforo": p.semaforo,
            "semaforo_label": SEMAFORO_LABEL.get(p.semaforo, p.semaforo),
            "emoji": SEMAFORO_EMOJI.get(p.semaforo, ""),
            "detalle": list(p.detalle_pilares.values()) if p.detalle_pilares else [],
        })
    return filas


def _parse_date(value):
    return parse_date(value) if value else None


# ----------------------------------------
# Home
# ----------------------------------------

def home_leadership_pulse(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    ciclo = _ciclo_vigente()
    mi_puntaje = None
    mis_pendientes = 0
    por_registrar = 0

    if ciclo:
        mi_puntaje = PuntajeMensual.objects.filter(ciclo=ciclo, lider=user).first()
        mis_pendientes = ParticipacionReto.objects.filter(
            reto__ciclo=ciclo, reto__activo=True, lider=user,
            estado__in=["pendiente", "devuelto"],
        ).count()
        if _puede_validar(user):
            por_registrar = ParticipacionReto.objects.filter(
                reto__ciclo=ciclo, reto__activo=True,
                estado__in=["pendiente", "en_revision"],
            ).count()

    top3 = []
    if ciclo and (ciclo.ranking_publicado or _puede_ver_todo(user)):
        top3 = _decorar_puntajes(
            PuntajeMensual.objects.filter(ciclo=ciclo)
            .select_related("lider")[:3]
        )

    ctx = {
        "ciclo": ciclo,
        "mi_puntaje": mi_puntaje,
        "mi_semaforo_label": SEMAFORO_LABEL.get(mi_puntaje.semaforo) if mi_puntaje else None,
        "mi_semaforo_emoji": SEMAFORO_EMOJI.get(mi_puntaje.semaforo, "") if mi_puntaje else "",
        "mis_pendientes": mis_pendientes,
        "por_registrar": por_registrar,
        "top3": top3,
        "puntaje_maximo": PUNTAJE_MAXIMO_MENSUAL,
        "puntaje_reto": PUNTAJE_MAXIMO_RETO,
    }
    ctx.update(_context_perms(user))
    return render(request, "home_pulse.html", ctx)


# ----------------------------------------
# Pilares
# ----------------------------------------

def gestionar_pilares(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    success = request.session.pop("pulse_pilar_ok", None)
    return render(request, "pulse_pilares.html", {
        "pilares": Pilar.objects.all(),
        "success": success,
        **_context_perms(user),
    })


def sembrar_pilares(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    if request.method == "POST":
        _asegurar_pilares_base()
        request.session["pulse_pilar_ok"] = "Pilares oficiales de SUPLI OS verificados."
    return redirect("leadership_pulse:gestionar_pilares")


def _guardar_pilar(pilar, post):
    codigo = post.get("codigo", "").strip().lower()
    nombre = post.get("nombre", "").strip()
    descripcion = post.get("descripcion", "").strip()
    puntaje_raw = post.get("puntaje_max", str(PUNTAJE_MAXIMO_RETO)).strip()
    orden_raw = post.get("orden", "0").strip()
    activo = post.get("activo") == "on"

    if not codigo or not nombre:
        return False, "Codigo y nombre son obligatorios."

    duplicado = Pilar.objects.filter(codigo=codigo).exclude(pk=pilar.pk).exists()
    if duplicado:
        return False, "Ya existe un pilar con ese codigo."

    try:
        puntaje_max = int(puntaje_raw) if puntaje_raw else PUNTAJE_MAXIMO_RETO
        orden = int(orden_raw) if orden_raw else 0
    except ValueError:
        return False, "Puntaje maximo y orden deben ser numeros enteros."

    if puntaje_max <= 0:
        return False, "El puntaje maximo debe ser mayor a cero."

    pilar.codigo = codigo
    pilar.nombre = nombre
    pilar.descripcion = descripcion
    pilar.puntaje_max = puntaje_max
    pilar.orden = orden
    pilar.activo = activo
    pilar.save()
    return True, None


def crear_pilar(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    error = None
    if request.method == "POST":
        ok, error = _guardar_pilar(Pilar(), request.POST)
        if ok:
            request.session["pulse_pilar_ok"] = "Pilar creado."
            return redirect("leadership_pulse:gestionar_pilares")
    return render(request, "pulse_pilar_form.html", {
        "pilar": None,
        "error": error,
        **_context_perms(user),
    })


def editar_pilar(request, pilar_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    pilar = get_object_or_404(Pilar, pk=pilar_id)
    error = None
    if request.method == "POST":
        ok, error = _guardar_pilar(pilar, request.POST)
        if ok:
            request.session["pulse_pilar_ok"] = "Pilar actualizado."
            return redirect("leadership_pulse:gestionar_pilares")
    return render(request, "pulse_pilar_form.html", {
        "pilar": pilar,
        "error": error,
        **_context_perms(user),
    })


# ----------------------------------------
# Ciclos mensuales
# ----------------------------------------

def gestionar_ciclos(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    success = request.session.pop("pulse_ciclo_ok", None)
    return render(request, "pulse_ciclos.html", {
        "ciclos": CicloPulse.objects.all(),
        "success": success,
        **_context_perms(user),
    })


def _guardar_ciclo(ciclo, post, user_actual):
    nombre = post.get("nombre", "").strip()
    descripcion = post.get("descripcion", "").strip()
    anio_raw = post.get("anio", "").strip()
    mes_raw = post.get("mes", "").strip()
    estado = post.get("estado", "programado")
    fecha_inicio = _parse_date(post.get("fecha_inicio"))
    fecha_fin = _parse_date(post.get("fecha_fin"))
    ranking_publicado = post.get("ranking_publicado") == "on"

    if not nombre:
        return False, "El nombre del ciclo es obligatorio."
    if estado not in {k for k, _ in ESTADO_CICLO_CHOICES}:
        return False, "Estado no valido."
    if not fecha_inicio or not fecha_fin:
        return False, "Fecha de inicio y fin son obligatorias."
    if fecha_fin < fecha_inicio:
        return False, "La fecha de fin no puede ser anterior a la de inicio."

    try:
        anio = int(anio_raw)
        mes = int(mes_raw)
    except ValueError:
        return False, "Ano y mes deben ser numericos."
    if mes < 1 or mes > 12:
        return False, "El mes debe estar entre 1 y 12."

    duplicado = CicloPulse.objects.filter(anio=anio, mes=mes).exclude(pk=ciclo.pk).exists()
    if duplicado:
        return False, "Ya existe un ciclo para ese mes."

    ciclo.nombre = nombre
    ciclo.descripcion = descripcion
    ciclo.anio = anio
    ciclo.mes = mes
    ciclo.estado = estado
    ciclo.fecha_inicio = fecha_inicio
    ciclo.fecha_fin = fecha_fin
    ciclo.ranking_publicado = ranking_publicado
    if ciclo.pk is None:
        ciclo.creado_por = user_actual
    ciclo.save()
    return True, None


def crear_ciclo(request):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    error = None
    if request.method == "POST":
        ciclo = CicloPulse()
        ok, error = _guardar_ciclo(ciclo, request.POST, user)
        if ok:
            _asegurar_pilares_base()
            request.session["pulse_ciclo_ok"] = "Ciclo creado."
            return redirect("leadership_pulse:gestionar_retos", ciclo_id=ciclo.id)
    hoy = timezone.localdate()
    return render(request, "pulse_ciclo_form.html", {
        "ciclo": None,
        "error": error,
        "estado_choices": ESTADO_CICLO_CHOICES,
        "meses_choices": MESES_CHOICES,
        "anio_actual": hoy.year,
        "mes_actual": hoy.month,
        **_context_perms(user),
    })


def editar_ciclo(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloPulse, pk=ciclo_id)
    error = None
    if request.method == "POST":
        ok, error = _guardar_ciclo(ciclo, request.POST, user)
        if ok:
            request.session["pulse_ciclo_ok"] = "Ciclo actualizado."
            return redirect("leadership_pulse:gestionar_ciclos")
    return render(request, "pulse_ciclo_form.html", {
        "ciclo": ciclo,
        "error": error,
        "estado_choices": ESTADO_CICLO_CHOICES,
        "meses_choices": MESES_CHOICES,
        "anio_actual": ciclo.anio,
        "mes_actual": ciclo.mes,
        **_context_perms(user),
    })


def consolidar_ciclo(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloPulse, pk=ciclo_id)
    if request.method == "POST":
        with transaction.atomic():
            _sincronizar_participaciones_ciclo(ciclo)
            total = _consolidar_ciclo(ciclo)
        request.session["pulse_ciclo_ok"] = (
            f"Ciclo consolidado: {total} lideres en el ranking."
        )
    return redirect("leadership_pulse:gestionar_ciclos")


def publicar_ranking(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloPulse, pk=ciclo_id)
    if request.method == "POST":
        ciclo.ranking_publicado = not ciclo.ranking_publicado
        ciclo.save(update_fields=["ranking_publicado"])
        estado = "publicado" if ciclo.ranking_publicado else "ocultado"
        request.session["pulse_ciclo_ok"] = f"Ranking {estado}."
    return redirect("leadership_pulse:gestionar_ciclos")


# ----------------------------------------
# Retos semanales
# ----------------------------------------

def gestionar_retos(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloPulse, pk=ciclo_id)
    retos = ciclo.retos.select_related("pilar").all()
    success = request.session.pop("pulse_reto_ok", None)
    return render(request, "pulse_retos.html", {
        "ciclo": ciclo,
        "retos": retos,
        "success": success,
        "puntaje_reto": PUNTAJE_MAXIMO_RETO,
        **_context_perms(user),
    })


def _guardar_reto(reto, post, ciclo):
    pilar_id = post.get("pilar", "")
    semana_raw = post.get("semana", "")
    titulo = post.get("titulo", "").strip()
    descripcion = post.get("descripcion", "").strip()
    fecha_inicio = _parse_date(post.get("fecha_inicio"))
    fecha_cierre = _parse_date(post.get("fecha_cierre"))
    activo = post.get("activo") == "on"

    if not titulo:
        return False, "El titulo del reto es obligatorio."
    if not fecha_inicio or not fecha_cierre:
        return False, "Fecha de inicio y cierre son obligatorias."
    if fecha_cierre < fecha_inicio:
        return False, "La fecha de cierre no puede ser anterior a la de inicio."

    try:
        semana = int(semana_raw)
    except ValueError:
        return False, "Semana no valida."
    if semana not in {k for k, _ in SEMANAS_CHOICES}:
        return False, "La semana debe estar entre 1 y 4."

    try:
        pilar = Pilar.objects.get(pk=int(pilar_id))
    except (Pilar.DoesNotExist, ValueError):
        return False, "Pilar no valido."

    duplicado = RetoSemanal.objects.filter(ciclo=ciclo, semana=semana).exclude(pk=reto.pk).exists()
    if duplicado:
        return False, "Ya existe un reto para esa semana en este ciclo."

    reto.ciclo = ciclo
    reto.pilar = pilar
    reto.semana = semana
    reto.titulo = titulo
    reto.descripcion = descripcion
    reto.criterio_cumplimiento = post.get("criterio_cumplimiento", "").strip()
    reto.fecha_inicio = fecha_inicio
    reto.fecha_cierre = fecha_cierre
    reto.puntaje_max = PUNTAJE_MAXIMO_RETO
    reto.activo = activo
    reto.save()
    return True, None


def crear_reto(request, ciclo_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    ciclo = get_object_or_404(CicloPulse, pk=ciclo_id)
    _asegurar_pilares_base()
    error = None
    if request.method == "POST":
        reto = RetoSemanal()
        ok, error = _guardar_reto(reto, request.POST, ciclo)
        if ok:
            _asegurar_participaciones(reto)
            request.session["pulse_reto_ok"] = "Reto creado y asignado al Leadership Team."
            return redirect("leadership_pulse:gestionar_retos", ciclo_id=ciclo.id)
    return render(request, "pulse_reto_form.html", {
        "ciclo": ciclo,
        "reto": None,
        "error": error,
        "pilares": Pilar.objects.filter(activo=True),
        "semanas_choices": SEMANAS_CHOICES,
        "puntaje_reto": PUNTAJE_MAXIMO_RETO,
        "pts_cumplimiento": PUNTOS_CUMPLIMIENTO,
        **_context_perms(user),
    })


def editar_reto(request, reto_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    reto = get_object_or_404(RetoSemanal, pk=reto_id)
    error = None
    if request.method == "POST":
        ok, error = _guardar_reto(reto, request.POST, reto.ciclo)
        if ok:
            _asegurar_participaciones(reto)
            request.session["pulse_reto_ok"] = "Reto actualizado."
            return redirect("leadership_pulse:gestionar_retos", ciclo_id=reto.ciclo_id)
    return render(request, "pulse_reto_form.html", {
        "ciclo": reto.ciclo,
        "reto": reto,
        "error": error,
        "pilares": Pilar.objects.filter(activo=True),
        "semanas_choices": SEMANAS_CHOICES,
        "puntaje_reto": PUNTAJE_MAXIMO_RETO,
        "pts_cumplimiento": PUNTOS_CUMPLIMIENTO,
        **_context_perms(user),
    })


def eliminar_reto(request, reto_id):
    user, resp = _require_role(request, _puede_configurar)
    if resp:
        return resp
    reto = get_object_or_404(RetoSemanal, pk=reto_id)
    ciclo_id = reto.ciclo_id
    if request.method == "POST":
        if reto.participaciones.filter(estado="validado").exists():
            request.session["pulse_reto_ok"] = (
                "No se puede eliminar: el reto ya tiene participaciones validadas."
            )
        else:
            reto.delete()
            request.session["pulse_reto_ok"] = "Reto eliminado."
    return redirect("leadership_pulse:gestionar_retos", ciclo_id=ciclo_id)


# ----------------------------------------
# Leadership Team (miembros)
# ----------------------------------------

def gestionar_miembros(request):
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp
    miembros = MiembroLeadershipTeam.objects.select_related("usuario").all()
    candidatos = (
        Usuario.objects.filter(is_active=True)
        .filter(Q(tipo_usuario__in=["lider", "admin"]) | Q(reportes_directos__isnull=False))
        .exclude(pulse_membresia__isnull=False)
        .distinct()
        .order_by("nombre", "apellido")
    )
    success = request.session.pop("pulse_miembro_ok", None)
    return render(request, "pulse_miembros.html", {
        "miembros": miembros,
        "candidatos": candidatos,
        "areas": dict(AREA_CHOICES),
        "success": success,
        **_context_perms(user),
    })


def sincronizar_miembros(request):
    """Inscribe automaticamente a todo el Leadership Team (lideres y admins)."""
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp
    if request.method == "POST":
        lideres = (
            Usuario.objects.filter(is_active=True)
            .filter(Q(tipo_usuario__in=["lider", "admin"]) | Q(reportes_directos__isnull=False))
            .distinct()
        )
        creados = 0
        for lider in lideres:
            _, nuevo = MiembroLeadershipTeam.objects.get_or_create(usuario=lider)
            if nuevo:
                creados += 1
        ciclo = _ciclo_vigente()
        if ciclo:
            _sincronizar_participaciones_ciclo(ciclo)
        request.session["pulse_miembro_ok"] = (
            f"Leadership Team sincronizado: {creados} lideres inscritos."
        )
    return redirect("leadership_pulse:gestionar_miembros")


def agregar_miembro(request):
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp
    if request.method == "POST":
        usuario_id = request.POST.get("usuario", "")
        try:
            usuario = Usuario.objects.get(pk=int(usuario_id))
        except (Usuario.DoesNotExist, ValueError):
            request.session["pulse_miembro_ok"] = "Usuario no valido."
            return redirect("leadership_pulse:gestionar_miembros")
        MiembroLeadershipTeam.objects.get_or_create(usuario=usuario)
        ciclo = _ciclo_vigente()
        if ciclo:
            _sincronizar_participaciones_ciclo(ciclo)
        request.session["pulse_miembro_ok"] = f"{usuario} inscrito en Leadership Pulse."
    return redirect("leadership_pulse:gestionar_miembros")


def alternar_miembro(request, miembro_id):
    user, resp = _require_role(request, _es_admin_people)
    if resp:
        return resp
    miembro = get_object_or_404(MiembroLeadershipTeam, pk=miembro_id)
    if request.method == "POST":
        miembro.activo = not miembro.activo
        miembro.save(update_fields=["activo"])
        estado = "activado" if miembro.activo else "desactivado"
        request.session["pulse_miembro_ok"] = f"{miembro.usuario} {estado}."
    return redirect("leadership_pulse:gestionar_miembros")


# ----------------------------------------
# Participacion del lider
# ----------------------------------------

def mis_retos(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    ciclo_id = request.GET.get("ciclo", "")
    ciclo = None
    if ciclo_id:
        ciclo = CicloPulse.objects.filter(pk=ciclo_id).first()
    ciclo = ciclo or _ciclo_vigente()

    participaciones = []
    if ciclo:
        _asegurar_participaciones_usuario(ciclo, user)
        participaciones = (
            ParticipacionReto.objects.filter(reto__ciclo=ciclo, lider=user, reto__activo=True)
            .select_related("reto", "reto__pilar")
            .order_by("reto__semana")
        )

    participaciones = list(participaciones)
    asignados = len(participaciones)
    participados = sum(1 for p in participaciones if p.esta_registrado and p.participo)
    cumplidos = sum(1 for p in participaciones if p.esta_registrado and p.cumplio)
    acumulado = sum(p.puntaje_total for p in participaciones if p.esta_registrado)
    pct_cumplimiento = _porcentaje(cumplidos, asignados)

    ctx = {
        "ciclo": ciclo,
        "ciclos": CicloPulse.objects.all()[:12],
        "participaciones": participaciones,
        "acumulado": acumulado,
        "asignados": asignados,
        "participados": participados,
        "cumplidos": cumplidos,
        "pct_participacion": _porcentaje(participados, asignados),
        "pct_cumplimiento": pct_cumplimiento,
        "puntaje_maximo": ciclo.puntaje_max if ciclo else PUNTAJE_MAXIMO_MENSUAL,
        "semaforo_label": SEMAFORO_LABEL.get(calcular_semaforo(pct_cumplimiento)),
        "semaforo_codigo": calcular_semaforo(pct_cumplimiento),
        "success": request.session.pop("pulse_reporte_ok", None),
    }
    ctx.update(_context_perms(user))
    return render(request, "pulse_mis_retos.html", ctx)


def _asegurar_participaciones_usuario(ciclo, user):
    """Si el usuario es miembro activo, garantiza su participacion en cada reto."""
    if not MiembroLeadershipTeam.objects.filter(usuario=user, activo=True).exists():
        return
    existentes = set(
        ParticipacionReto.objects.filter(reto__ciclo=ciclo, lider=user)
        .values_list("reto_id", flat=True)
    )
    nuevas = [
        ParticipacionReto(reto=reto, lider=user)
        for reto in ciclo.retos.filter(activo=True)
        if reto.id not in existentes
    ]
    if nuevas:
        ParticipacionReto.objects.bulk_create(nuevas)


def reportar_reto(request, participacion_id):
    """El lider declara si participo y si cumplio el reto, con soporte opcional."""
    user, redir = _require_login(request)
    if redir:
        return redir

    participacion = get_object_or_404(
        ParticipacionReto.objects.select_related("reto", "reto__pilar", "reto__ciclo"),
        pk=participacion_id,
    )
    if participacion.lider_id != user.id and not _puede_validar(user):
        return render(request, "acceso_no_permitido.html", status=403)

    error = None
    bloqueado = participacion.estado == "validado" and not _puede_validar(user)

    if request.method == "POST" and not bloqueado:
        declara = request.POST.get("declara_cumplimiento") == "on"
        participacion.participo = request.POST.get("participo") == "on"
        participacion.declara_cumplimiento = declara and participacion.participo
        participacion.evidencia_url = request.POST.get("evidencia_url", "").strip()
        participacion.evidencia_descripcion = request.POST.get(
            "evidencia_descripcion", ""
        ).strip()
        participacion.estado = "en_revision"
        participacion.fecha_reporte = timezone.now()
        participacion.save()
        request.session["pulse_reporte_ok"] = (
            "Reporte enviado. People confirmara el registro del reto."
        )
        return redirect("leadership_pulse:mis_retos")

    ctx = {
        "participacion": participacion,
        "reto": participacion.reto,
        "error": error,
        "bloqueado": bloqueado,
        "puntaje_reto": participacion.reto.puntaje_max,
    }
    ctx.update(_context_perms(user))
    return render(request, "pulse_reportar_reto.html", ctx)


# ----------------------------------------
# Registro de retos (People / Admin)
# ----------------------------------------

def _aplicar_registro(participacion, post, user, sufijo=""):
    """Aplica participo / cumplio / observaciones sobre una participacion."""
    participacion.participo = post.get("participo" + sufijo) == "on"
    participacion.cumplio = post.get("cumplio" + sufijo) == "on"
    participacion.observaciones = post.get("observaciones" + sufijo, "").strip()
    participacion.recalcular_puntaje()
    participacion.estado = "validado"
    participacion.validado_por = user
    participacion.fecha_validacion = timezone.now()
    participacion.save()
    return participacion


def bandeja_validacion(request):
    """Seguimiento individual: una fila por persona y reto del ciclo."""
    user, resp = _require_role(request, _puede_validar)
    if resp:
        return resp

    ciclo_id = request.GET.get("ciclo", "")
    estado = request.GET.get("estado", "")
    reto_id = request.GET.get("reto", "")
    ciclo = CicloPulse.objects.filter(pk=ciclo_id).first() if ciclo_id else _ciclo_vigente()

    participaciones = ParticipacionReto.objects.select_related(
        "reto", "reto__pilar", "lider"
    )
    if ciclo:
        participaciones = participaciones.filter(reto__ciclo=ciclo)
    if estado in {k for k, _ in ESTADO_PARTICIPACION_CHOICES}:
        participaciones = participaciones.filter(estado=estado)
    if reto_id:
        participaciones = participaciones.filter(reto_id=reto_id)
    participaciones = list(
        participaciones.order_by("reto__semana", "lider__nombre", "lider__apellido")
    )

    total = len(participaciones)
    registrados = sum(1 for p in participaciones if p.esta_registrado)

    return render(request, "pulse_validacion.html", {
        "ciclo": ciclo,
        "ciclos": CicloPulse.objects.all()[:12],
        "retos_ciclo": ciclo.retos.filter(activo=True).select_related("pilar") if ciclo else [],
        "reto_filtro": reto_id,
        "participaciones": participaciones,
        "estado_filtro": estado,
        "estado_choices": ESTADO_PARTICIPACION_CHOICES,
        "total_registros": total,
        "registrados": registrados,
        "pendientes": total - registrados,
        "pct_avance": _porcentaje(registrados, total),
        "puntaje_reto": PUNTAJE_MAXIMO_RETO,
        "success": request.session.pop("pulse_validacion_ok", None),
        **_context_perms(user),
    })


def registro_reto(request, reto_id):
    """Grilla masiva: registra a todo el Leadership Team en un mismo reto."""
    user, resp = _require_role(request, _puede_validar)
    if resp:
        return resp

    reto = get_object_or_404(
        RetoSemanal.objects.select_related("ciclo", "pilar"), pk=reto_id
    )
    _asegurar_participaciones(reto)

    if request.method == "POST":
        por_id = {
            p.id: p
            for p in ParticipacionReto.objects.filter(reto=reto).select_related("reto")
        }
        guardados = 0
        with transaction.atomic():
            for pid in request.POST.getlist("participacion_id"):
                participacion = por_id.get(int(pid))
                if participacion is None:
                    continue
                _aplicar_registro(participacion, request.POST, user, sufijo="_" + str(pid))
                guardados += 1
        request.session["pulse_validacion_ok"] = (
            "Registro guardado para %s lider(es) en la semana %s." % (guardados, reto.semana)
        )
        return redirect("leadership_pulse:registro_reto", reto_id=reto.id)

    participaciones = list(
        ParticipacionReto.objects.filter(reto=reto)
        .select_related("lider")
        .order_by("lider__nombre", "lider__apellido")
    )
    total = len(participaciones)
    participados = sum(1 for p in participaciones if p.esta_registrado and p.participo)
    cumplidos = sum(1 for p in participaciones if p.esta_registrado and p.cumplio)
    registrados = sum(1 for p in participaciones if p.esta_registrado)

    return render(request, "pulse_registro_reto.html", {
        "reto": reto,
        "ciclo": reto.ciclo,
        "participaciones": participaciones,
        "total": total,
        "registrados": registrados,
        "participados": participados,
        "cumplidos": cumplidos,
        "pct_participacion": _porcentaje(participados, total),
        "pct_cumplimiento": _porcentaje(cumplidos, total),
        "success": request.session.pop("pulse_validacion_ok", None),
        **_context_perms(user),
    })


def validar_participacion(request, participacion_id):
    """Registro individual: participo / cumplio / observaciones."""
    user, resp = _require_role(request, _puede_validar)
    if resp:
        return resp
    participacion = get_object_or_404(
        ParticipacionReto.objects.select_related("reto"), pk=participacion_id
    )
    if request.method == "POST":
        accion = request.POST.get("accion", "registrar")
        if accion == "devolver":
            participacion.participo = False
            participacion.cumplio = False
            participacion.observaciones = request.POST.get("observaciones", "").strip()
            participacion.recalcular_puntaje()
            participacion.estado = "devuelto"
            participacion.observaciones_validador = participacion.observaciones
            participacion.validado_por = user
            participacion.fecha_validacion = timezone.now()
            participacion.save()
            request.session["pulse_validacion_ok"] = "Reporte devuelto al lider."
        else:
            _aplicar_registro(participacion, request.POST, user)
            request.session["pulse_validacion_ok"] = (
                "%s: %s." % (participacion.lider, participacion.registro_label)
            )
    destino = request.POST.get("next") or "leadership_pulse:bandeja_validacion"
    return redirect(destino)


# ----------------------------------------
# Ranking y pulse individual
# ----------------------------------------

def ranking(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    ciclo_id = request.GET.get("ciclo", "")
    ciclo = CicloPulse.objects.filter(pk=ciclo_id).first() if ciclo_id else _ciclo_vigente()

    puede_ver = _puede_ver_todo(user)
    if ciclo and not (ciclo.ranking_publicado or puede_ver):
        return render(request, "pulse_ranking.html", {
            "ciclo": ciclo,
            "ciclos": CicloPulse.objects.all()[:12],
            "no_publicado": True,
            "top3": [],
            "filas": [],
            **_context_perms(user),
        })

    puntajes = []
    if ciclo:
        puntajes = list(
            PuntajeMensual.objects.filter(ciclo=ciclo).select_related("lider")
        )
    filas = _decorar_puntajes(puntajes)

    promedio = (
        round(sum(f["pct_cumplimiento"] for f in filas) / len(filas), 1) if filas else 0
    )
    promedio_participacion = (
        round(sum(f["pct_participacion"] for f in filas) / len(filas), 1) if filas else 0
    )
    distribucion = OrderedDict()
    for codigo in SEMAFORO_ORDEN:
        distribucion[codigo] = {
            "label": SEMAFORO_LABEL.get(codigo, codigo),
            "emoji": SEMAFORO_EMOJI.get(codigo, ""),
            "total": sum(1 for f in filas if f["semaforo"] == codigo),
        }

    ctx = {
        "ciclo": ciclo,
        "ciclos": CicloPulse.objects.all()[:12],
        "top3": filas[:3],
        "filas": filas,
        "promedio": promedio,
        "promedio_participacion": promedio_participacion,
        "distribucion": list(distribucion.values()),
        "total_lideres": len(filas),
        "no_publicado": False,
        "puntaje_maximo": ciclo.puntaje_max if ciclo else PUNTAJE_MAXIMO_MENSUAL,
    }
    ctx.update(_context_perms(user))
    return render(request, "pulse_ranking.html", ctx)


def mi_pulse(request):
    user, redir = _require_login(request)
    if redir:
        return redir
    return _render_pulse(request, user, user)


def pulse_lider(request, usuario_id):
    user, resp = _require_role(request, _puede_ver_todo)
    if resp:
        return resp
    lider = get_object_or_404(Usuario, pk=usuario_id)
    return _render_pulse(request, user, lider)


def _render_pulse(request, user_actual, lider):
    """Historico y detalle de desempeno de un lider."""
    puntajes = list(
        PuntajeMensual.objects.filter(lider=lider)
        .select_related("ciclo")
        .order_by("-ciclo__anio", "-ciclo__mes")[:12]
    )

    historico = _decorar_puntajes(puntajes)
    for fila, registro in zip(historico, puntajes):
        fila["ciclo"] = registro.ciclo

    actual = historico[0] if historico else None
    promedio = (
        round(sum(h["pct_cumplimiento"] for h in historico) / len(historico), 1)
        if historico else 0
    )

    tendencia = None
    if len(historico) >= 2:
        tendencia = round(
            historico[0]["pct_cumplimiento"] - historico[1]["pct_cumplimiento"], 1
        )

    # Historial completo de retos registrados (seguimiento individual)
    ultimas = (
        ParticipacionReto.objects.filter(lider=lider, estado__in=["validado", "devuelto"])
        .select_related("reto", "reto__pilar", "reto__ciclo")
        .order_by("-reto__ciclo__anio", "-reto__ciclo__mes", "-reto__semana")[:20]
    )

    # Acumulado historico de participacion y cumplimiento
    todas = ParticipacionReto.objects.filter(lider=lider, reto__activo=True)
    hist_asignados = todas.count()
    hist_participados = todas.filter(estado="validado", participo=True).count()
    hist_cumplidos = todas.filter(estado="validado", cumplio=True).count()

    ctx = {
        "lider": lider,
        "es_propio": lider.id == user_actual.id,
        "actual": actual,
        "historico": historico,
        "promedio": promedio,
        "tendencia": tendencia,
        "ultimas": ultimas,
        "puntaje_maximo": PUNTAJE_MAXIMO_MENSUAL,
        "hist_asignados": hist_asignados,
        "hist_participados": hist_participados,
        "hist_cumplidos": hist_cumplidos,
        "hist_pct_participacion": _porcentaje(hist_participados, hist_asignados),
        "hist_pct_cumplimiento": _porcentaje(hist_cumplidos, hist_asignados),
        "total_validado": ParticipacionReto.objects.filter(
            lider=lider, estado="validado"
        ).aggregate(t=Sum("puntaje_total"))["t"] or 0,
    }
    ctx.update(_context_perms(user_actual))
    return render(request, "pulse_individual.html", ctx)
