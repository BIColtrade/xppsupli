from django.shortcuts import redirect, render

from user.jwt_utils import (
    UMBRAL_RENOVACION, create_jwt, get_user_from_request, segundos_restantes,
)


class GroupAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""

        # Skip static/admin/login/logout
        if (
            path.startswith("/static/")
            or path.startswith("/media/")
            or path.startswith("/admin/")
            or path.startswith("/coltrxde/login")
            or path.startswith("/coltrxde/logout")
        ):
            return self.get_response(request)

        user = get_user_from_request(request)

        # If user is required but missing, redirect to login
        def _require_auth():
            if user is None:
                return redirect("login")
            return None

        # Admin check
        def _is_admin():
            if user is None:
                return False
            if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
                return True
            groups = set(user.groups.values_list("name", flat=True))
            groups = {g.lower() for g in groups}
            return "admin" in groups

        # Group check
        def _in_group(name):
            if user is None:
                return False
            groups = set(user.groups.values_list("name", flat=True))
            groups = {g.lower() for g in groups}
            return name.lower() in groups

        def _in_any_group(names):
            if user is None:
                return False
            groups = set(user.groups.values_list("name", flat=True))
            groups = {g.lower() for g in groups}
            names = {n.lower() for n in names}
            return not groups.isdisjoint(names)

        # Crear usuarios y listado: solo admin
        if path.startswith("/coltrxde/crear-usuarios") or path.startswith("/coltrxde/listado-usuarios"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not _is_admin():
                return render(request, "acceso_no_permitido.html", status=403)

        # Abastecimientos: admin o abastecimientos
        if path.startswith("/abastecimientos/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not (_is_admin() or _in_group("abastecimientos")):
                return render(request, "acceso_no_permitido.html", status=403)

        # Bienestar Coltrade: admin o bienestarcoltrade
        if path.startswith("/bienestar/coltrxde/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not (_is_admin() or _in_group("bienestarcoltrade")):
                return render(request, "acceso_no_permitido.html", status=403)

        # Modulo Valoracion: admin, grupo modulovaloracion, o roles internos
        # (Admin People, BI/Tech, CEO, lider o colaborador con asignacion).
        # Aqui solo bloqueamos a quienes claramente no tienen acceso global; los
        # views aplican controles finos por seccion.
        if path.startswith("/modulo/valoracion/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            area = getattr(user, "area", None)
            tipo_usuario = getattr(user, "tipo_usuario", None)
            if not (
                _is_admin()
                or _in_group("modulovaloracion")
                or area in {"people", "bi", "tecnologia", "ceo"}
                or tipo_usuario in {"admin", "lider", "colaborador"}
            ):
                return render(request, "acceso_no_permitido.html", status=403)

        # Leadership Pulse: admin, grupo leadershippulse, o roles internos
        # (Admin People, BI/Tech, CEO o lider). Los views aplican el control
        # fino por seccion (configuracion, validacion, ranking).
        if path.startswith("/leadership/pulse/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            area = getattr(user, "area", None)
            tipo_usuario = getattr(user, "tipo_usuario", None)
            if not (
                _is_admin()
                or _in_group("leadershippulse")
                or area in {"people", "bi", "tecnologia", "ceo"}
                or tipo_usuario in {"admin", "lider"}
            ):
                return render(request, "acceso_no_permitido.html", status=403)

        # home_user y settings_user: admin o cualquier grupo funcional
        if path.startswith("/coltrxde/home_user/") or path.startswith("/coltrxde/settings-user/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not (
                _is_admin()
                or _in_any_group(
                    [
                        "abastecimientos",
                        "bienestarcoltrade",
                    ]
                )
            ):
                return render(request, "acceso_no_permitido.html", status=403)

        response = self.get_response(request)
        self._renovar_sesion(request, response, user)
        return response

    @staticmethod
    def _renovar_sesion(request, response, user):
        """Renueva el JWT si esta por vencer (sesion deslizante).

        Sin esto el token moria a las 8 horas exactas sin importar que la
        persona estuviera trabajando: al enviar un formulario largo la peticion
        rebotaba al login y se perdia todo lo escrito.
        """
        if user is None:
            return
        token = request.COOKIES.get("jwt")
        if not token:
            return
        restantes = segundos_restantes(token)
        if restantes is None or restantes > UMBRAL_RENOVACION.total_seconds():
            return
        response.set_cookie(
            "jwt",
            create_jwt(user),
            httponly=True,
            samesite="Lax",
            secure=request.is_secure(),
            max_age=None,
        )

