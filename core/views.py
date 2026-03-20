from django.shortcuts import redirect, render

from user.jwt_utils import get_user_from_request

def home(request):
    return render(request, "home.html")

    
def home_autenticado(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    return render(request, "home_autenticado.html")
