from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from urllib.parse import parse_qs, urlparse
import re

from user.jwt_utils import get_user_from_request
from user.models import AREA_CHOICES, Usuario
from .models import (
    AccionPPS,
    PuntosUsuario,
    RegistroAccion,
    Beneficio,
    ReclamoBeneficio,
    ProgresoCapacitacion,
)


# ----------------------------------------
# Helpers
# ----------------------------------------

def _require_login(request):
    user = get_user_from_request(request)
    if user is None:
        return None, redirect("login")
    return user, None


def _get_or_create_puntos(user):
    puntos, _ = PuntosUsuario.objects.get_or_create(usuario=user)
    return puntos


def _es_admin_global(user):
    if user is None:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    return getattr(user, "tipo_usuario", None) == "admin"


def _es_lider(user):
    if _es_admin_global(user):
        return True
    return (
        getattr(user, "tipo_usuario", None) == "lider"
        and getattr(user, "area", None) == "people"
    )


def _accion_es_para_usuario(accion, user):
    if _es_admin_global(user):
        return True

    if getattr(accion, "aplica_empresa", False):
        return True

    area_user = getattr(user, "area", None)
    areas_accion = getattr(accion, "areas", None) or []
    if areas_accion:
        if not area_user or area_user not in areas_accion:
            return False

    tipo_user = getattr(user, "tipo_usuario", None) or "colaborador"
    es_lider = tipo_user == "lider"

    destinatarios = getattr(accion, "destinatarios", None) or "todos"
    if destinatarios == "todos" and getattr(accion, "solo_lideres", False) and not es_lider:
        return False
    if destinatarios == "lideres" and not es_lider:
        return False
    if destinatarios == "colaboradores" and es_lider:
        return False

    return True


def _extraer_youtube_id(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    host = (parsed.netloc or "").lower()
    path = parsed.path or ""

    if "youtu.be" in host:
        video_id = path.strip("/").split("/")[0]
        return video_id or None

    if "youtube.com" in host or "youtube-nocookie.com" in host:
        if path == "/watch":
            query = parse_qs(parsed.query)
            return query.get("v", [None])[0]
        if path.startswith("/embed/"):
            parts = path.split("/")
            return parts[2] if len(parts) > 2 else None
        if path.startswith("/shorts/"):
            parts = path.split("/")
            return parts[2] if len(parts) > 2 else None

    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


# ----------------------------------------
# Home
# ----------------------------------------

def home_bienestar_coltrade(request):
    user, redir = _require_login(request)
    if redir:
        return redir
    puntos = _get_or_create_puntos(user)
    return render(request, "home_bienestar_coltrade.html", {
        "puntos": puntos,
        "es_lider": _es_lider(user),
    })


# ----------------------------------------
# Mi Perfil
# ----------------------------------------

def mi_perfil_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    puntos = _get_or_create_puntos(user)
    registros = RegistroAccion.objects.filter(usuario=user).select_related("accion")[:20]
    reclamos = ReclamoBeneficio.objects.filter(usuario=user).select_related("beneficio")[:10]

    p = puntos.puntos_totales
    if p < 500:
        siguiente_nivel = 'Plata'
        puntos_siguiente = 500
        progreso = int((p / 500) * 100)
    elif p < 1500:
        siguiente_nivel = 'Oro'
        puntos_siguiente = 1500
        progreso = int(((p - 500) / 1000) * 100)
    elif p < 4000:
        siguiente_nivel = 'Diamante'
        puntos_siguiente = 4000
        progreso = int(((p - 1500) / 2500) * 100)
    else:
        siguiente_nivel = None
        puntos_siguiente = None
        progreso = 100
    puntos_faltantes = puntos_siguiente - p if puntos_siguiente else 0

    return render(request, "mi_perfil_pps.html", {
        "puntos": puntos,
        "registros": registros,
        "reclamos": reclamos,
        "siguiente_nivel": siguiente_nivel,
        "puntos_siguiente": puntos_siguiente,
        "progreso": progreso,
        "puntos_faltantes": puntos_faltantes,
    })


# ----------------------------------------
# Catalogo de Acciones
# ----------------------------------------

def catalogo_acciones_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    lider = _es_lider(user)
    acciones_qs = AccionPPS.objects.filter(activa=True)
    acciones = [a for a in acciones_qs if _accion_es_para_usuario(a, user)]

    acciones_ids = [a.id for a in acciones]
    acciones_registradas_ids = set(
        RegistroAccion.objects.filter(usuario=user, accion_id__in=acciones_ids)
        .values_list("accion_id", flat=True)
    )

    acciones_por_nivel = {
        'estrategico': [a for a in acciones if a.nivel == 'estrategico'],
        'tactico': [a for a in acciones if a.nivel == 'tactico'],
        'desarrollo': [a for a in acciones if a.nivel == 'desarrollo'],
        'activacion_bienestar': [a for a in acciones if a.nivel == 'activacion_bienestar'],
        'capacitacion': [a for a in acciones if a.nivel == 'capacitacion'],
    }

    return render(request, "catalogo_acciones_pps.html", {
        "acciones_por_nivel": acciones_por_nivel,
        "es_lider": lider,
        "acciones_registradas_ids": acciones_registradas_ids,
    })


# ----------------------------------------
# Registrar Accion
# ----------------------------------------

def registrar_accion_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    lider = _es_lider(user)
    acciones_qs = AccionPPS.objects.filter(activa=True).exclude(nivel="capacitacion")
    acciones = [a for a in acciones_qs if _accion_es_para_usuario(a, user)]
    acciones_ids = {a.id for a in acciones}

    error = None
    success = request.session.pop("pps_registro_ok", None)
    accion_seleccionada_id = None

    accion_param = request.GET.get("accion", "").strip()
    if accion_param:
        try:
            accion_param_id = int(accion_param)
        except ValueError:
            accion_param_id = None

        if accion_param_id:
            accion_seleccionada = next(
                (a for a in acciones if a.id == accion_param_id),
                None,
            )
            if accion_seleccionada:
                accion_seleccionada_id = accion_seleccionada.id

    if request.method == "POST":
        accion_id = request.POST.get("accion")
        evidencia = request.POST.get("evidencia", "").strip()
        if accion_id:
            try:
                accion_id_int = int(accion_id)
            except ValueError:
                accion_id_int = None
            if accion_id_int and accion_id_int in acciones_ids:
                accion_seleccionada_id = accion_id_int

        if not accion_id or not evidencia:
            error = "Debes seleccionar una accion y describir la evidencia."
        else:
            try:
                accion = AccionPPS.objects.get(pk=accion_id, activa=True)
                if accion.nivel == "capacitacion":
                    return redirect("home_bienestar_coltrade:ver_capacitacion_pps", accion_id=accion.id)
                if not _accion_es_para_usuario(accion, user):
                    error = "Esta accion no esta disponible para tu perfil."
                elif RegistroAccion.objects.filter(usuario=user, accion=accion).exists():
                    error = "Ya registraste esta accion."
                else:
                    RegistroAccion.objects.create(
                        usuario=user,
                        accion=accion,
                        descripcion_evidencia=evidencia,
                        puntos_asignados=accion.puntos_default,
                    )
                    request.session["pps_registro_ok"] = True
                    return redirect("home_bienestar_coltrade:registrar_accion_pps")
            except AccionPPS.DoesNotExist:
                error = "Accion no valida."

    return render(request, "registrar_accion_pps.html", {
        "acciones": acciones,
        "error": error,
        "success": success,
        "accion_seleccionada_id": accion_seleccionada_id,
        "es_lider": lider,
    })


# ----------------------------------------
# Capacitacion
# ----------------------------------------

def ver_capacitacion_pps(request, accion_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    accion = get_object_or_404(
        AccionPPS, pk=accion_id, activa=True, nivel="capacitacion"
    )
    video_id = _extraer_youtube_id(accion.youtube_url or "")
    if not video_id:
        return render(request, "ver_capacitacion_pps.html", {
            "accion": accion,
            "error": "Esta capacitacion no tiene un video valido.",
        })

    progreso, _ = ProgresoCapacitacion.objects.get_or_create(
        usuario=user, accion=accion
    )

    return render(request, "ver_capacitacion_pps.html", {
        "accion": accion,
        "video_id": video_id,
        "progreso_pct": progreso.progreso_pct,
        "puntos_otorgados": progreso.puntos_otorgados,
        "puntos_max": accion.puntos_default,
    })


@require_POST
def actualizar_progreso_capacitacion(request, accion_id):
    user, redir = _require_login(request)
    if redir:
        return JsonResponse({"error": "login_required"}, status=401)

    accion = get_object_or_404(
        AccionPPS, pk=accion_id, activa=True, nivel="capacitacion"
    )

    progreso_raw = request.POST.get("progreso", "").strip()
    try:
        progreso_val = float(progreso_raw)
    except ValueError:
        return JsonResponse({"error": "progreso_invalido"}, status=400)

    progreso_val = max(0, min(100, int(progreso_val)))
    puntos_max = accion.puntos_default or 0

    with transaction.atomic():
        progreso, _ = ProgresoCapacitacion.objects.select_for_update().get_or_create(
            usuario=user, accion=accion
        )
        if progreso_val < progreso.progreso_pct:
            progreso_val = progreso.progreso_pct

        nuevos_puntos_total = int((progreso_val / 100) * puntos_max)
        if nuevos_puntos_total < progreso.puntos_otorgados:
            nuevos_puntos_total = progreso.puntos_otorgados

        delta = nuevos_puntos_total - progreso.puntos_otorgados
        if delta > 0:
            puntos = _get_or_create_puntos(user)
            puntos.puntos_totales += delta
            puntos.actualizar_nivel()
            puntos.save()

        progreso.progreso_pct = progreso_val
        progreso.puntos_otorgados = nuevos_puntos_total
        progreso.completado = progreso_val >= 100
        progreso.save()

    return JsonResponse({
        "progreso_pct": progreso.progreso_pct,
        "puntos_otorgados": progreso.puntos_otorgados,
        "puntos_max": puntos_max,
    })


# ----------------------------------------
# Mis Acciones
# ----------------------------------------

def mis_acciones_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    filtro = request.GET.get("estado", "")
    registros = RegistroAccion.objects.filter(usuario=user).select_related("accion", "aprobado_por")
    if filtro in ("pendiente", "aprobado", "rechazado"):
        registros = registros.filter(estado=filtro)

    totales = RegistroAccion.objects.filter(usuario=user).aggregate(
        pendientes=Count("id", filter=Q(estado="pendiente")),
        aprobados=Count("id", filter=Q(estado="aprobado")),
        rechazados=Count("id", filter=Q(estado="rechazado")),
    )

    return render(request, "mis_acciones_pps.html", {
        "registros": registros,
        "filtro": filtro,
        "totales": totales,
    })


# ----------------------------------------
# Mis Beneficios
# ----------------------------------------

def mis_beneficios_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    filtro = request.GET.get("estado", "")
    reclamos = ReclamoBeneficio.objects.filter(usuario=user).select_related("beneficio")
    if filtro in ("pendiente", "entregado", "cancelado"):
        reclamos = reclamos.filter(estado=filtro)

    totales = ReclamoBeneficio.objects.filter(usuario=user).aggregate(
        pendientes=Count("id", filter=Q(estado="pendiente")),
        entregados=Count("id", filter=Q(estado="entregado")),
        cancelados=Count("id", filter=Q(estado="cancelado")),
    )

    return render(request, "mis_beneficios_pps.html", {
        "reclamos": reclamos,
        "filtro": filtro,
        "totales": totales,
    })


# ----------------------------------------
# Ranking
# ----------------------------------------

def ranking_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    ranking = PuntosUsuario.objects.select_related("usuario").order_by("-puntos_totales")[:20]
    puntos_user = _get_or_create_puntos(user)

    return render(request, "ranking_pps.html", {
        "ranking": ranking,
        "puntos_user": puntos_user,
    })


# ----------------------------------------
# Catalogo de Beneficios
# ----------------------------------------

def catalogo_beneficios_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    puntos = _get_or_create_puntos(user)
    beneficios = Beneficio.objects.filter(disponible=True)
    success = request.session.pop("pps_reclamo_ok", None)
    error = request.session.pop("pps_reclamo_error", None)

    return render(request, "catalogo_beneficios_pps.html", {
        "beneficios": beneficios,
        "puntos": puntos,
        "success": success,
        "error": error,
    })


def reclamar_beneficio_pps(request, beneficio_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if request.method != "POST":
        return redirect("home_bienestar_coltrade:catalogo_beneficios_pps")

    beneficio = get_object_or_404(Beneficio, pk=beneficio_id, disponible=True)
    puntos = _get_or_create_puntos(user)

    if puntos.puntos_totales < beneficio.puntos_requeridos:
        request.session["pps_reclamo_error"] = "No tienes suficientes puntos para este beneficio."
    elif beneficio.stock is not None and beneficio.stock <= 0:
        request.session["pps_reclamo_error"] = "Este beneficio ya no tiene stock disponible."
    else:
        ReclamoBeneficio.objects.create(
            usuario=user,
            beneficio=beneficio,
            puntos_descontados=beneficio.puntos_requeridos,
        )
        puntos.puntos_totales = max(puntos.puntos_totales - beneficio.puntos_requeridos, 0)
        puntos.actualizar_nivel()
        puntos.save()
        if beneficio.stock is not None:
            beneficio.stock -= 1
            beneficio.save()
        request.session["pps_reclamo_ok"] = f"Beneficio '{beneficio.nombre}' reclamado con exito."

    return redirect("home_bienestar_coltrade:catalogo_beneficios_pps")


def crear_beneficio_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    categorias = Beneficio.CATEGORIA_CHOICES
    error = None
    success = request.session.pop("pps_beneficio_ok", None)

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        categoria = request.POST.get("categoria", "")
        puntos_requeridos = request.POST.get("puntos_requeridos", "")
        disponible = request.POST.get("disponible") == "on"
        stock_raw = request.POST.get("stock", "").strip()

        if not all([nombre, descripcion, categoria, puntos_requeridos]):
            error = "Todos los campos obligatorios deben estar completos."
        else:
            try:
                puntos_val = int(puntos_requeridos)
                stock_val = int(stock_raw) if stock_raw else None
                Beneficio.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    categoria=categoria,
                    puntos_requeridos=puntos_val,
                    disponible=disponible,
                    stock=stock_val,
                )
                request.session["pps_beneficio_ok"] = "Beneficio creado exitosamente."
                return redirect("home_bienestar_coltrade:crear_beneficio_pps")
            except ValueError:
                error = "Los valores numericos deben ser enteros."

    return render(request, "crear_beneficio_pps.html", {
        "error": error,
        "success": success,
        "categorias": categorias,
    })


# ----------------------------------------
# Panel Lider
# ----------------------------------------

def panel_lider_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    es_admin_global = _es_admin_global(user)
    area = getattr(user, "area", None)

    filtro = request.GET.get("estado", "pendiente")
    registros_base = RegistroAccion.objects.select_related("usuario", "accion")
    if not es_admin_global:
        if area:
            registros_base = registros_base.filter(usuario__area=area)
        else:
            registros_base = registros_base.none()

    registros = registros_base
    if filtro in ("pendiente", "aprobado", "rechazado"):
        registros = registros.filter(estado=filtro)

    totales = registros_base.aggregate(
        pendientes=Count("id", filter=Q(estado="pendiente")),
        aprobados=Count("id", filter=Q(estado="aprobado")),
        rechazados=Count("id", filter=Q(estado="rechazado")),
    )

    reclamos_base = ReclamoBeneficio.objects.select_related(
        "usuario", "beneficio"
    )
    if not es_admin_global:
        if area:
            reclamos_base = reclamos_base.filter(usuario__area=area)
        else:
            reclamos_base = reclamos_base.none()

    reclamos_pendientes = reclamos_base.filter(estado="pendiente")

    totales_reclamos = reclamos_base.aggregate(
        pendientes=Count("id", filter=Q(estado="pendiente")),
        entregados=Count("id", filter=Q(estado="entregado")),
        cancelados=Count("id", filter=Q(estado="cancelado")),
    )

    success = request.session.pop("pps_panel_ok", None)

    return render(request, "panel_lider_pps.html", {
        "registros": registros,
        "filtro": filtro,
        "totales": totales,
        "reclamos_pendientes": reclamos_pendientes,
        "totales_reclamos": totales_reclamos,
        "success": success,
    })


def resolver_accion_pps(request, registro_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    if request.method != "POST":
        return redirect("home_bienestar_coltrade:panel_lider_pps")

    es_admin_global = _es_admin_global(user)
    area = getattr(user, "area", None)

    registros_qs = RegistroAccion.objects.filter(estado="pendiente")
    if not es_admin_global:
        if area:
            registros_qs = registros_qs.filter(usuario__area=area)
        else:
            registros_qs = registros_qs.none()

    registro = get_object_or_404(registros_qs, pk=registro_id)
    accion_resolucion = request.POST.get("accion_resolucion")
    observacion = request.POST.get("observacion", "").strip()
    puntos_custom = request.POST.get("puntos_asignados", "").strip()

    if accion_resolucion == "aprobar":
        try:
            pts = int(puntos_custom) if puntos_custom else registro.accion.puntos_default
        except ValueError:
            pts = registro.accion.puntos_default

        registro.estado = "aprobado"
        registro.puntos_asignados = pts
        registro.aprobado_por = user
        registro.observacion_lider = observacion
        registro.fecha_resolucion = timezone.now()
        registro.save()

        puntos = _get_or_create_puntos(registro.usuario)
        puntos.puntos_totales += pts
        puntos.actualizar_nivel()
        puntos.save()
        request.session["pps_panel_ok"] = f"Accion aprobada: +{pts} pts a {registro.usuario}."

    elif accion_resolucion == "rechazar":
        registro.estado = "rechazado"
        registro.aprobado_por = user
        registro.observacion_lider = observacion
        registro.fecha_resolucion = timezone.now()
        registro.save()
        request.session["pps_panel_ok"] = f"Accion de {registro.usuario} rechazada."

    return redirect("home_bienestar_coltrade:panel_lider_pps")


def resolver_reclamo_beneficio_pps(request, reclamo_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    if request.method != "POST":
        return redirect("home_bienestar_coltrade:panel_lider_pps")

    es_admin_global = _es_admin_global(user)
    area = getattr(user, "area", None)

    reclamos_qs = ReclamoBeneficio.objects.filter(estado="pendiente")
    if not es_admin_global:
        if area:
            reclamos_qs = reclamos_qs.filter(usuario__area=area)
        else:
            reclamos_qs = reclamos_qs.none()

    reclamo = get_object_or_404(reclamos_qs, pk=reclamo_id)
    accion_resolucion = request.POST.get("accion_resolucion")

    if accion_resolucion == "entregar":
        reclamo.estado = "entregado"
        reclamo.save()
        request.session["pps_panel_ok"] = f"Beneficio entregado a {reclamo.usuario}."
    elif accion_resolucion == "cancelar":
        reclamo.estado = "cancelado"
        reclamo.save()

        puntos = _get_or_create_puntos(reclamo.usuario)
        puntos.puntos_totales += reclamo.puntos_descontados
        puntos.actualizar_nivel()
        puntos.save()

        beneficio = reclamo.beneficio
        if beneficio.stock is not None:
            beneficio.stock += 1
            beneficio.save()

        request.session["pps_panel_ok"] = f"Reclamo cancelado y puntos devueltos a {reclamo.usuario}."

    return redirect("home_bienestar_coltrade:panel_lider_pps")


# ----------------------------------------
# Gestion del Catalogo de Acciones
# ----------------------------------------

def gestionar_acciones_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    acciones = AccionPPS.objects.all()
    success = request.session.pop("pps_accion_ok", None)

    return render(request, "gestionar_acciones_pps.html", {
        "acciones": acciones,
        "success": success,
    })


def crear_accion_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    error = None

    area_choices = AREA_CHOICES
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        nivel = request.POST.get("nivel", "")
        youtube_url = request.POST.get("youtube_url", "").strip() or None
        areas = request.POST.getlist("areas")
        destinatarios = request.POST.get("destinatarios", "todos")
        puntos_min = request.POST.get("puntos_min", "")
        puntos_max = request.POST.get("puntos_max", "")
        puntos_default = request.POST.get("puntos_default", "")
        activa = request.POST.get("activa") == "on"

        video_id = _extraer_youtube_id(youtube_url) if youtube_url else None
        valid_areas = {key for key, _ in area_choices}
        aplica_empresa = "empresa" in areas or destinatarios == "empresa"
        if aplica_empresa:
            areas = []
            destinatarios = "todos"

        if not all([nombre, descripcion, nivel, puntos_min, puntos_max, puntos_default]):
            error = "Todos los campos son obligatorios."
        elif not aplica_empresa and not areas:
            error = "Debes seleccionar al menos un area o marcar Accion a Nivel Empresa."
        elif any(a not in valid_areas for a in areas):
            error = "Seleccionaste un area no valida."
        elif destinatarios not in {"todos", "lideres", "colaboradores"}:
            error = "Seleccionaste un destinatario no valido."
        elif nivel == "capacitacion" and not video_id:
            error = "Debes ingresar un enlace de YouTube valido para la capacitacion."
        else:
            try:
                if nivel == "capacitacion":
                    destinatarios = destinatarios or "todos"
                else:
                    youtube_url = None
                if video_id:
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                solo_lideres = destinatarios == "lideres"
                AccionPPS.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    nivel=nivel,
                    youtube_url=youtube_url,
                    areas=areas,
                    destinatarios=destinatarios,
                    aplica_empresa=aplica_empresa,
                    puntos_min=int(puntos_min),
                    puntos_max=int(puntos_max),
                    puntos_default=int(puntos_default),
                    solo_lideres=solo_lideres,
                    activa=activa,
                )
                request.session["pps_accion_ok"] = "Accion creada exitosamente."
                return redirect("home_bienestar_coltrade:gestionar_acciones_pps")
            except ValueError:
                error = "Los valores de puntos deben ser numeros enteros."

    return render(request, "crear_accion_pps.html", {"error": error, "area_choices": area_choices})


def editar_accion_pps(request, accion_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    accion = get_object_or_404(AccionPPS, pk=accion_id)
    error = None

    area_choices = AREA_CHOICES
    if request.method == "POST":
        accion.nombre = request.POST.get("nombre", "").strip()
        accion.descripcion = request.POST.get("descripcion", "").strip()
        accion.nivel = request.POST.get("nivel", "")
        youtube_url = request.POST.get("youtube_url", "").strip() or None
        areas = request.POST.getlist("areas")
        destinatarios = request.POST.get("destinatarios", "todos")
        accion.activa = request.POST.get("activa") == "on"
        video_id = _extraer_youtube_id(youtube_url) if youtube_url else None
        valid_areas = {key for key, _ in area_choices}
        aplica_empresa = "empresa" in areas or destinatarios == "empresa"
        if aplica_empresa:
            areas = []
            destinatarios = "todos"

        if not aplica_empresa and not areas:
            error = "Debes seleccionar al menos un area o marcar Accion a Nivel Empresa."
        elif any(a not in valid_areas for a in areas):
            error = "Seleccionaste un area no valida."
        elif destinatarios not in {"todos", "lideres", "colaboradores"}:
            error = "Seleccionaste un destinatario no valido."
        elif accion.nivel == "capacitacion" and not video_id:
            error = "Debes ingresar un enlace de YouTube valido para la capacitacion."
        else:
            try:
                if accion.nivel == "capacitacion":
                    destinatarios = destinatarios or "todos"
                else:
                    youtube_url = None
                if video_id:
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                accion.youtube_url = youtube_url
                accion.areas = areas
                accion.destinatarios = destinatarios
                accion.aplica_empresa = aplica_empresa
                accion.solo_lideres = destinatarios == "lideres"
                accion.puntos_min = int(request.POST.get("puntos_min", 0))
                accion.puntos_max = int(request.POST.get("puntos_max", 0))
                accion.puntos_default = int(request.POST.get("puntos_default", 0))
                accion.save()
                request.session["pps_accion_ok"] = "Accion actualizada exitosamente."
                return redirect("home_bienestar_coltrade:gestionar_acciones_pps")
            except ValueError:
                error = "Los valores de puntos deben ser numeros enteros."

    return render(request, "editar_accion_pps.html", {"accion": accion, "error": error, "area_choices": area_choices})


def eliminar_accion_pps(request, accion_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    if request.method == "POST":
        accion = get_object_or_404(AccionPPS, pk=accion_id)
        accion.delete()
        request.session["pps_accion_ok"] = "Accion eliminada."

    return redirect("home_bienestar_coltrade:gestionar_acciones_pps")


# ----------------------------------------
# Gestion de Beneficios
# ----------------------------------------

def gestionar_beneficios_pps(request):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    beneficios = Beneficio.objects.order_by("puntos_requeridos")
    success = request.session.pop("pps_beneficio_ok", None)

    return render(request, "gestionar_beneficios_pps.html", {
        "beneficios": beneficios,
        "success": success,
    })


def editar_beneficio_pps(request, beneficio_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    beneficio = get_object_or_404(Beneficio, pk=beneficio_id)
    categorias = Beneficio.CATEGORIA_CHOICES
    error = None

    if request.method == "POST":
        beneficio.nombre = request.POST.get("nombre", "").strip()
        beneficio.descripcion = request.POST.get("descripcion", "").strip()
        beneficio.categoria = request.POST.get("categoria", "")
        beneficio.disponible = request.POST.get("disponible") == "on"

        puntos_raw = request.POST.get("puntos_requeridos", "").strip()
        stock_raw = request.POST.get("stock", "").strip()

        if not all([beneficio.nombre, beneficio.descripcion, beneficio.categoria, puntos_raw]):
            error = "Todos los campos obligatorios deben estar completos."
        else:
            try:
                beneficio.puntos_requeridos = int(puntos_raw)
                beneficio.stock = int(stock_raw) if stock_raw else None
                beneficio.save()
                request.session["pps_beneficio_ok"] = "Beneficio actualizado correctamente."
                return redirect("home_bienestar_coltrade:gestionar_beneficios_pps")
            except ValueError:
                error = "Los valores numericos deben ser enteros."

    return render(request, "editar_beneficio_pps.html", {
        "beneficio": beneficio,
        "categorias": categorias,
        "error": error,
    })


def eliminar_beneficio_pps(request, beneficio_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    if request.method == "POST":
        beneficio = get_object_or_404(Beneficio, pk=beneficio_id)
        beneficio.delete()
        request.session["pps_beneficio_ok"] = "Beneficio eliminado."

    return redirect("home_bienestar_coltrade:gestionar_beneficios_pps")
