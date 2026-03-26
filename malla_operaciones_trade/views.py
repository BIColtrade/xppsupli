from datetime import timedelta

from django.db import IntegrityError
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from user.jwt_utils import get_user_from_request

from .models import Asesor, Coordinador, PuntoVentaMalla, RegistroLaboral


def _require_login(request):
    user = get_user_from_request(request)
    if user is None:
        return None, redirect("login")
    return user, None


def home_malla_operaciones(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    return render(request, "home_malla_operaciones.html")


def asesores(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    context = {"asesores": Asesor.objects.order_by("nombre")}
    flash_success = request.session.pop("asesores_success", None)
    if flash_success:
        context["success"] = flash_success
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "create":
            nombre = request.POST.get("nombre", "").strip()
            correo = request.POST.get("correo", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            if not nombre:
                context["error"] = "El nombre es obligatorio."
            else:
                Asesor.objects.create(
                    nombre=nombre,
                    correo=correo or None,
                    telefono=telefono or None,
                )
                request.session["asesores_success"] = "Asesor creado."
                return redirect("malla_operaciones_trade:asesores")
        else:
            asesor_id = request.POST.get("asesor_id", "").strip()
            if not asesor_id:
                context["error"] = "Asesor no valido."
            else:
                try:
                    target = Asesor.objects.get(pk=asesor_id)
                except Asesor.DoesNotExist:
                    context["error"] = "Asesor no encontrado."
                else:
                    if action == "delete":
                        try:
                            target.delete()
                            request.session["asesores_success"] = "Asesor eliminado."
                            return redirect("malla_operaciones_trade:asesores")
                        except Exception:
                            context["error"] = "No se pudo eliminar el asesor."
                    elif action == "save":
                        nombre = request.POST.get("nombre", "").strip()
                        correo = request.POST.get("correo", "").strip()
                        telefono = request.POST.get("telefono", "").strip()
                        if not nombre:
                            context["error"] = "El nombre es obligatorio."
                        else:
                            target.nombre = nombre
                            target.correo = correo or None
                            target.telefono = telefono or None
                            target.save()
                            request.session["asesores_success"] = "Asesor actualizado."
                            return redirect("malla_operaciones_trade:asesores")

        context["asesores"] = Asesor.objects.order_by("nombre")

    return render(request, "asesores.html", context)


def coordinadores(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    context = {"coordinadores": Coordinador.objects.order_by("nombre")}
    flash_success = request.session.pop("coordinadores_success", None)
    if flash_success:
        context["success"] = flash_success
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "create":
            nombre = request.POST.get("nombre", "").strip()
            if not nombre:
                context["error"] = "El nombre es obligatorio."
            else:
                Coordinador.objects.create(nombre=nombre)
                request.session["coordinadores_success"] = "Coordinador creado."
                return redirect("malla_operaciones_trade:coordinadores")
        else:
            coordinador_id = request.POST.get("coordinador_id", "").strip()
            if not coordinador_id:
                context["error"] = "Coordinador no valido."
            else:
                try:
                    target = Coordinador.objects.get(pk=coordinador_id)
                except Coordinador.DoesNotExist:
                    context["error"] = "Coordinador no encontrado."
                else:
                    if action == "delete":
                        try:
                            target.delete()
                            request.session["coordinadores_success"] = "Coordinador eliminado."
                            return redirect("malla_operaciones_trade:coordinadores")
                        except Exception:
                            context["error"] = "No se pudo eliminar el coordinador."
                    elif action == "save":
                        nombre = request.POST.get("nombre", "").strip()
                        if not nombre:
                            context["error"] = "El nombre es obligatorio."
                        else:
                            target.nombre = nombre
                            target.save()
                            request.session["coordinadores_success"] = "Coordinador actualizado."
                            return redirect("malla_operaciones_trade:coordinadores")

        context["coordinadores"] = Coordinador.objects.order_by("nombre")

    return render(request, "coordinadores.html", context)


def punto_venta(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    context = {
        "puntos": PuntoVentaMalla.objects.order_by("nombre"),
        "coordinadores": Coordinador.objects.order_by("nombre"),
        "asesores": Asesor.objects.order_by("nombre"),
        "zonas": PuntoVentaMalla.ZONAS,
    }
    flash_success = request.session.pop("punto_venta_success", None)
    if flash_success:
        context["success"] = flash_success
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        zonas_validas = {z[0] for z in PuntoVentaMalla.ZONAS}
        if action == "create":
            id_punto = request.POST.get("id_punto", "").strip()
            nombre = request.POST.get("nombre", "").strip()
            zona = request.POST.get("zona", "").strip()
            coord_id = request.POST.get("coordinador_default", "").strip()
            asesor_id = request.POST.get("asesor_default", "").strip()

            if not id_punto or not nombre or not zona:
                context["error"] = "ID, nombre y zona son obligatorios."
            elif zona not in zonas_validas:
                context["error"] = "Zona no valida."
            elif PuntoVentaMalla.objects.filter(pk=id_punto).exists():
                context["error"] = "El ID del punto ya existe."
            else:
                PuntoVentaMalla.objects.create(
                    id_punto=id_punto,
                    nombre=nombre,
                    zona=zona,
                    coordinador_default_id=coord_id or None,
                    asesor_default_id=asesor_id or None,
                )
                request.session["punto_venta_success"] = "Punto de venta creado."
                return redirect("malla_operaciones_trade:punto_venta")
        else:
            id_punto = request.POST.get("id_punto", "").strip()
            if not id_punto:
                context["error"] = "Punto de venta no valido."
            else:
                try:
                    target = PuntoVentaMalla.objects.get(pk=id_punto)
                except PuntoVentaMalla.DoesNotExist:
                    context["error"] = "Punto de venta no encontrado."
                else:
                    if action == "delete":
                        try:
                            target.delete()
                            request.session["punto_venta_success"] = "Punto de venta eliminado."
                            return redirect("malla_operaciones_trade:punto_venta")
                        except Exception:
                            context["error"] = "No se pudo eliminar el punto."
                    elif action == "save":
                        nombre = request.POST.get("nombre", "").strip()
                        zona = request.POST.get("zona", "").strip()
                        coord_id = request.POST.get("coordinador_default", "").strip()
                        asesor_id = request.POST.get("asesor_default", "").strip()
                        if not nombre or not zona:
                            context["error"] = "Nombre y zona son obligatorios."
                        elif zona not in zonas_validas:
                            context["error"] = "Zona no valida."
                        else:
                            target.nombre = nombre
                            target.zona = zona
                            target.coordinador_default_id = coord_id or None
                            target.asesor_default_id = asesor_id or None
                            target.save()
                            request.session["punto_venta_success"] = "Punto de venta actualizado."
                            return redirect("malla_operaciones_trade:punto_venta")

        context["puntos"] = PuntoVentaMalla.objects.order_by("nombre")
        context["zonas"] = PuntoVentaMalla.ZONAS

    return render(request, "punto_venta.html", context)


def registro_horario(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    context = {
        "registros": RegistroLaboral.objects.select_related(
            "punto_venta", "coordinador", "asesor"
        ).order_by("-fecha", "id_registro"),
        "puntos": PuntoVentaMalla.objects.order_by("nombre"),
        "coordinadores": Coordinador.objects.order_by("nombre"),
        "asesores": Asesor.objects.order_by("nombre"),
        "estados": RegistroLaboral.ESTADOS,
    }
    flash_success = request.session.pop("registro_horario_success", None)
    if flash_success:
        context["success"] = flash_success
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "create":
            fecha_raw = request.POST.get("fecha", "").strip()
            punto_id = request.POST.get("punto_venta", "").strip()
            coord_id = request.POST.get("coordinador", "").strip()
            asesor_id = request.POST.get("asesor", "").strip()
            estado = request.POST.get("estado", "").strip()
            hora_ingreso_raw = request.POST.get("hora_ingreso", "").strip()
            hora_salida_raw = request.POST.get("hora_salida", "").strip()

            fecha = parse_date(fecha_raw)
            hora_ingreso = parse_time(hora_ingreso_raw) if hora_ingreso_raw else None
            hora_salida = parse_time(hora_salida_raw) if hora_salida_raw else None

            if not fecha or not punto_id or not estado:
                context["error"] = "Fecha, punto de venta y estado son obligatorios."
            else:
                RegistroLaboral.objects.create(
                    fecha=fecha,
                    punto_venta_id=punto_id,
                    coordinador_id=coord_id or None,
                    asesor_id=asesor_id or None,
                    estado=estado,
                    hora_ingreso=hora_ingreso,
                    hora_salida=hora_salida,
                )
                request.session["registro_horario_success"] = "Registro laboral creado."
                return redirect("malla_operaciones_trade:registro_horario")
        else:
            registro_id = request.POST.get("registro_id", "").strip()
            if not registro_id:
                context["error"] = "Registro no valido."
            else:
                try:
                    target = RegistroLaboral.objects.get(pk=registro_id)
                except RegistroLaboral.DoesNotExist:
                    context["error"] = "Registro no encontrado."
                else:
                    if action == "delete":
                        target.delete()
                        request.session["registro_horario_success"] = "Registro eliminado."
                        return redirect("malla_operaciones_trade:registro_horario")
                    elif action == "save":
                        fecha_raw = request.POST.get("fecha", "").strip()
                        punto_id = request.POST.get("punto_venta", "").strip()
                        coord_id = request.POST.get("coordinador", "").strip()
                        asesor_id = request.POST.get("asesor", "").strip()
                        estado = request.POST.get("estado", "").strip()
                        hora_ingreso_raw = request.POST.get("hora_ingreso", "").strip()
                        hora_salida_raw = request.POST.get("hora_salida", "").strip()

                        fecha = parse_date(fecha_raw)
                        hora_ingreso = (
                            parse_time(hora_ingreso_raw) if hora_ingreso_raw else None
                        )
                        hora_salida = (
                            parse_time(hora_salida_raw) if hora_salida_raw else None
                        )

                        if not fecha or not punto_id or not estado:
                            context["error"] = (
                                "Fecha, punto de venta y estado son obligatorios."
                            )
                        else:
                            target.fecha = fecha
                            target.punto_venta_id = punto_id
                            target.coordinador_id = coord_id or None
                            target.asesor_id = asesor_id or None
                            target.estado = estado
                            target.hora_ingreso = hora_ingreso
                            target.hora_salida = hora_salida
                            try:
                                target.save()
                                request.session["registro_horario_success"] = "Registro actualizado."
                                return redirect("malla_operaciones_trade:registro_horario")
                            except IntegrityError:
                                context["error"] = "No se pudo actualizar el registro."

        context["registros"] = RegistroLaboral.objects.select_related(
            "punto_venta", "coordinador", "asesor"
        ).order_by("-fecha", "id_registro")

    return render(request, "registro_horario.html", context)


def dashboard_horas(request):
    _, redirect_resp = _require_login(request)
    if redirect_resp:
        return redirect_resp
    today = timezone.localdate()
    start_raw = request.GET.get("start", "").strip()
    end_raw = request.GET.get("end", "").strip()
    zona = request.GET.get("zona", "").strip()
    punto_nombres = [n.strip() for n in request.GET.getlist("punto") if n.strip()]
    asesor_nombres = [n.strip() for n in request.GET.getlist("asesor") if n.strip()]
    coordinador_nombres = [
        n.strip() for n in request.GET.getlist("coordinador") if n.strip()
    ]

    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None
    if not start_date or not end_date:
        end_date = today
        start_date = today - timedelta(days=6)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    registros_qs = RegistroLaboral.objects.select_related(
        "punto_venta", "coordinador", "asesor"
    ).filter(fecha__range=[start_date, end_date])

    if zona:
        registros_qs = registros_qs.filter(punto_venta__zona=zona)
    if punto_nombres:
        registros_qs = registros_qs.filter(punto_venta__nombre__in=punto_nombres)
    if asesor_nombres:
        registros_qs = registros_qs.filter(asesor__nombre__in=asesor_nombres)
    if coordinador_nombres:
        registros_qs = registros_qs.filter(
            coordinador__nombre__in=coordinador_nombres
        )

    total_horas = (
        registros_qs.aggregate(total=Sum("horas_trabajadas")).get("total") or 0
    )
    total_registros = registros_qs.count()
    total_puntos = registros_qs.values("punto_venta_id").distinct().count()
    total_asesores = (
        registros_qs.exclude(asesor_id__isnull=True).values("asesor_id").distinct().count()
    )
    asesores_activos = (
        registros_qs.filter(estado="ACTIVO", asesor_id__isnull=False)
        .values("asesor_id")
        .distinct()
        .count()
    )

    estados_counts = {
        row["estado"]: row["total"]
        for row in registros_qs.values("estado").annotate(total=Count("id_registro"))
    }

    puntos_resumen = (
        registros_qs.values(
            "punto_venta_id", "punto_venta__nombre", "punto_venta__zona"
        )
        .annotate(
            total_horas=Sum("horas_trabajadas"),
            registros=Count("id_registro"),
            activos=Count(
                Case(When(estado="ACTIVO", then=1), output_field=IntegerField())
            ),
            vacantes=Count(
                Case(When(estado="VACANTE", then=1), output_field=IntegerField())
            ),
            incapacidades=Count(
                Case(When(estado="INCAPACIDAD", then=1), output_field=IntegerField())
            ),
            descansos=Count(
                Case(When(estado="DESCANSO", then=1), output_field=IntegerField())
            ),
        )
        .order_by("punto_venta__zona", "punto_venta__nombre")
    )

    registros = registros_qs.order_by("-fecha", "-id_registro")[:400]

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "zona": zona,
        "punto_nombres": punto_nombres,
        "asesor_nombres": asesor_nombres,
        "coordinador_nombres": coordinador_nombres,
        "zonas": PuntoVentaMalla.ZONAS,
        "puntos_opciones": PuntoVentaMalla.objects.order_by("nombre")
        .values_list("nombre", flat=True)
        .distinct(),
        "asesores_opciones": Asesor.objects.order_by("nombre")
        .values_list("nombre", flat=True)
        .distinct(),
        "coordinadores_opciones": Coordinador.objects.order_by("nombre")
        .values_list("nombre", flat=True)
        .distinct(),
        "total_horas": total_horas,
        "total_registros": total_registros,
        "total_puntos": total_puntos,
        "total_asesores": total_asesores,
        "asesores_activos": asesores_activos,
        "vacantes": estados_counts.get("VACANTE", 0),
        "incapacidades": estados_counts.get("INCAPACIDAD", 0),
        "descansos": estados_counts.get("DESCANSO", 0),
        "puntos_resumen": puntos_resumen,
        "registros": registros,
    }
    return render(request, "dashboard_horas.html", context)
