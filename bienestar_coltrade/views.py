from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request


def home_bienestar_coltrade(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    return render(request, "home_bienestar_coltrade.html")
