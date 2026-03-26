from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request


def home_portafolio_mayoristas(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    return render(request, "home_portafolio_mayoristas.html")
