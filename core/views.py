from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request

def home(request):
    return render(request, "home.html")

    
def home_autenticado(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    group_names = set(user.groups.values_list("name", flat=True))
    is_admin = "admin" in group_names
    context = {
        "can_abastecimientos": is_admin or "abastecimientos" in group_names,
        "can_bienestar": is_admin or "bienestarcoltrade" in group_names,
        "can_listadocompras": is_admin or "listadocompras" in group_names,
        "can_malla": is_admin or "mallaoperaciones" in group_names,
        "can_portafolio": is_admin or "portafoliomayoristas" in group_names,
        "can_user": True,  # Todo usuario autenticado ve la tarjeta Usuarios
    }
    return render(request, "home_autenticado.html", context)
