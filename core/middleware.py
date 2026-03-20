from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request


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

        # Crear usuarios y listado: solo admin
        if path.startswith("/coltrxde/crear-usuarios") or path.startswith("/coltrxde/listado-usuarios"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not _is_admin():
                return render(request, "acceso_no_permitido.html", status=403)

        # Abastecimientos y settings_user: admin o abastecimiento
        if path.startswith("/abastecimientos/") or path.startswith("/coltrxde/settings-user/"):
            auth_resp = _require_auth()
            if auth_resp:
                return auth_resp
            if not (_is_admin() or _in_group("abastecimiento")):
                return render(request, "acceso_no_permitido.html", status=403)

        return self.get_response(request)
