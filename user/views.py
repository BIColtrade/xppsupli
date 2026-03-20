from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .jwt_utils import create_jwt, get_user_from_request


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, email=email, password=password)
        if user is None:
            return render(
                request,
                "login.html",
                {"error": "Credenciales incorrectas."},
            )
        token = create_jwt(user)
        response = redirect("home_autenticado")
        response.set_cookie(
            "jwt",
            token,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure(),
            max_age=None,
        )
        return response
    return render(request, "login.html")


@require_POST
def logout_view(request):
    response = redirect("home")
    response.delete_cookie("jwt")
    return response


def settings_user(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")

    context = {"user_obj": user}

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "update_info":
            user.username = request.POST.get("username", "").strip()
            user.nombre = request.POST.get("nombre", "").strip()
            user.apellido = request.POST.get("apellido", "").strip()
            edad_raw = request.POST.get("edad", "").strip()
            if edad_raw:
                if edad_raw.isdigit():
                    user.edad = int(edad_raw)
                else:
                    context["error_info"] = "La edad debe ser un numero."
            else:
                user.edad = None
            user.telefono = request.POST.get("telefono", "").strip() or None
            if "error_info" not in context:
                try:
                    user.save()
                    context["success_info"] = "Informacion actualizada."
                except IntegrityError:
                    context["error_info"] = "El usuario ya existe."

        elif action == "change_password":
            current = request.POST.get("current_password", "")
            new = request.POST.get("new_password", "")
            confirm = request.POST.get("confirm_password", "")

            if not user.check_password(current):
                context["error_password"] = "La contraseña actual no es correcta."
            elif not new:
                context["error_password"] = "La nueva contraseña es obligatoria."
            elif new != confirm:
                context["error_password"] = "Las contraseñas no coinciden."
            else:
                user.set_password(new)
                user.save()
                context["success_password"] = "Contraseña actualizada."

    return render(request, "settingsuser.html", context)
