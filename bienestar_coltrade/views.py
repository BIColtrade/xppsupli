from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q

from user.jwt_utils import get_user_from_request
from user.models import Usuario
from .models import AccionPPS, PuntosUsuario, RegistroAccion, Beneficio, ReclamoBeneficio


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


def _es_lider(user):
    return getattr(user, 'tipo_usuario', None) == 'lider' or user.is_staff


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
    acciones = AccionPPS.objects.filter(activa=True)
    if not lider:
        acciones = acciones.filter(solo_lideres=False)

    acciones_registradas_ids = set(
        RegistroAccion.objects.filter(usuario=user, accion__in=acciones)
        .values_list("accion_id", flat=True)
    )

    acciones_por_nivel = {
        'estrategico': acciones.filter(nivel='estrategico'),
        'tactico': acciones.filter(nivel='tactico'),
        'desarrollo': acciones.filter(nivel='desarrollo'),
        'activacion_bienestar': acciones.filter(nivel='activacion_bienestar'),
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
    acciones = AccionPPS.objects.filter(activa=True)
    if not lider:
        acciones = acciones.filter(solo_lideres=False)

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
            accion_seleccionada = acciones.filter(id=accion_param_id).first()
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
            if accion_id_int and acciones.filter(id=accion_id_int).exists():
                accion_seleccionada_id = accion_id_int

        if not accion_id or not evidencia:
            error = "Debes seleccionar una accion y describir la evidencia."
        else:
            try:
                accion = AccionPPS.objects.get(pk=accion_id, activa=True)
                if accion.solo_lideres and not lider:
                    error = "Esta accion solo esta disponible para lideres."
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

    es_admin_global = user.is_staff or user.is_superuser
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

    es_admin_global = user.is_staff or user.is_superuser
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

    es_admin_global = user.is_staff or user.is_superuser
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

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        nivel = request.POST.get("nivel", "")
        puntos_min = request.POST.get("puntos_min", "")
        puntos_max = request.POST.get("puntos_max", "")
        puntos_default = request.POST.get("puntos_default", "")
        solo_lideres = request.POST.get("solo_lideres") == "on"
        activa = request.POST.get("activa") == "on"

        if not all([nombre, descripcion, nivel, puntos_min, puntos_max, puntos_default]):
            error = "Todos los campos son obligatorios."
        else:
            try:
                AccionPPS.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    nivel=nivel,
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

    return render(request, "crear_accion_pps.html", {"error": error})


def editar_accion_pps(request, accion_id):
    user, redir = _require_login(request)
    if redir:
        return redir

    if not _es_lider(user):
        return redirect("home_bienestar_coltrade:home_bienestar_coltrade")

    accion = get_object_or_404(AccionPPS, pk=accion_id)
    error = None

    if request.method == "POST":
        accion.nombre = request.POST.get("nombre", "").strip()
        accion.descripcion = request.POST.get("descripcion", "").strip()
        accion.nivel = request.POST.get("nivel", "")
        accion.solo_lideres = request.POST.get("solo_lideres") == "on"
        accion.activa = request.POST.get("activa") == "on"
        try:
            accion.puntos_min = int(request.POST.get("puntos_min", 0))
            accion.puntos_max = int(request.POST.get("puntos_max", 0))
            accion.puntos_default = int(request.POST.get("puntos_default", 0))
            accion.save()
            request.session["pps_accion_ok"] = "Accion actualizada exitosamente."
            return redirect("home_bienestar_coltrade:gestionar_acciones_pps")
        except ValueError:
            error = "Los valores de puntos deben ser numeros enteros."

    return render(request, "editar_accion_pps.html", {"accion": accion, "error": error})


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
