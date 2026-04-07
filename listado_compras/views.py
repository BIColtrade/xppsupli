from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request

LISTADO_COMPRAS_GROUP = "listadocompras"


def _require_listado_compras_group(request):
    user = get_user_from_request(request)
    if user is None:
        return None, redirect("login")
    if not user.groups.filter(name=LISTADO_COMPRAS_GROUP).exists():
        return user, render(request, "acceso_no_permitido.html", status=403)
    return user, None


def home_listado_compras(request):
    user, response = _require_listado_compras_group(request)
    if response is not None:
        return response
    return render(request, "home_listado_compras.html")


def listado_productos_supli(request):
    user, response = _require_listado_compras_group(request)
    if response is not None:
        return response
    return render(request, "listado_productos_supli.html")

