from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .jwt_utils import create_jwt, get_user_from_request
from django.contrib.auth.models import Group

from .models import AREA_CHOICES, TIPO_USUARIO_CHOICES, Usuario


def _is_admin_user(user):
    if user is None:
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    groups = set(user.groups.values_list("name", flat=True))
    groups = {g.lower() for g in groups}
    return "admin" in groups


def crear_usuario(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    if not _is_admin_user(user):
        return redirect("home_autenticado")

    context = {
        "grupos": Group.objects.order_by("name"),
        "tipo_usuario_choices": TIPO_USUARIO_CHOICES,
        "area_choices": AREA_CHOICES,
    }
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        edad_raw = request.POST.get("edad", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        tipo_usuario = request.POST.get("tipo_usuario", "").strip() or None
        area = request.POST.get("area", "").strip() or None
        password = request.POST.get("password", "")
        grupos_ids = request.POST.getlist("grupos")
        valid_tipo_usuario = {key for key, _ in TIPO_USUARIO_CHOICES}
        valid_area = {key for key, _ in AREA_CHOICES}

        if not email or not username or not nombre or not password:
            context["error"] = "Email, usuario, nombre y contraseña son obligatorios."
        else:
            edad_val = None
            if edad_raw:
                if edad_raw.isdigit():
                    edad_val = int(edad_raw)
                else:
                    context["error"] = "La edad debe ser un numero."

            if tipo_usuario and tipo_usuario not in valid_tipo_usuario:
                context["error"] = "El tipo de usuario no es valido."
            if area and area not in valid_area:
                context["error"] = "El area no es valida."

            if "error" not in context:
                try:
                    new_user = Usuario.objects.create_user(
                        email=email, username=username, password=password
                    )
                    new_user.nombre = nombre
                    new_user.apellido = apellido
                    new_user.edad = edad_val
                    new_user.telefono = telefono or None
                    new_user.tipo_usuario = tipo_usuario
                    new_user.area = area
                    new_user.save()
                    if grupos_ids:
                        grupos_validos = Group.objects.filter(id__in=grupos_ids)
                        new_user.groups.set(grupos_validos)
                    context["success"] = "Usuario creado correctamente."
                except IntegrityError:
                    context["error"] = "El email o usuario ya existe."

    return render(request, "crear_usuarios.html", context)


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


def home_user(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    return render(request, "home_user.html")


def listado_usuarios(request):
    user = get_user_from_request(request)
    if user is None:
        return redirect("login")
    if not _is_admin_user(user):
        return redirect("home_autenticado")

    context = {
        "usuarios": Usuario.objects.order_by("email"),
        "grupos": Group.objects.order_by("name"),
        "tipo_usuario_choices": TIPO_USUARIO_CHOICES,
        "area_choices": AREA_CHOICES,
    }

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        if action == "create_group":
            group_name = request.POST.get("group_name", "").strip()
            if not group_name:
                context["error"] = "El nombre del grupo es obligatorio."
            else:
                group_obj, created = Group.objects.get_or_create(name=group_name)
                if created:
                    context["success"] = "Grupo creado correctamente."
                else:
                    context["error"] = "El grupo ya existe."
        elif action == "create":
            email = request.POST.get("email", "").strip()
            username = request.POST.get("username", "").strip()
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            edad_raw = request.POST.get("edad", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            tipo_usuario = request.POST.get("tipo_usuario", "").strip() or None
            area = request.POST.get("area", "").strip() or None
            password = request.POST.get("password", "")
            grupos_ids = request.POST.getlist("grupos")
            valid_tipo_usuario = {key for key, _ in TIPO_USUARIO_CHOICES}
            valid_area = {key for key, _ in AREA_CHOICES}

            if not email or not username or not nombre or not password:
                context["error"] = "Email, usuario, nombre y contraseña son obligatorios."
            else:
                edad_val = None
                if edad_raw:
                    if edad_raw.isdigit():
                        edad_val = int(edad_raw)
                    else:
                        context["error"] = "La edad debe ser un numero."
                if tipo_usuario and tipo_usuario not in valid_tipo_usuario:
                    context["error"] = "El tipo de usuario no es valido."
                if area and area not in valid_area:
                    context["error"] = "El area no es valida."

            if "error" not in context:
                try:
                    new_user = Usuario.objects.create_user(
                        email=email, username=username, password=password
                    )
                    new_user.nombre = nombre
                    new_user.apellido = apellido
                    new_user.edad = edad_val
                    new_user.telefono = telefono or None
                    new_user.tipo_usuario = tipo_usuario
                    new_user.area = area
                    new_user.save()
                    if grupos_ids:
                        grupos_validos = Group.objects.filter(id__in=grupos_ids)
                        new_user.groups.set(grupos_validos)
                    context["success"] = "Usuario creado correctamente."
                except IntegrityError:
                    context["error"] = "El email o usuario ya existe."
        else:
            user_id = request.POST.get("user_id", "").strip()
            if not user_id:
                context["error"] = "Usuario no valido."
            else:
                try:
                    target = Usuario.objects.get(pk=user_id)
                except Usuario.DoesNotExist:
                    context["error"] = "Usuario no encontrado."
                else:
                    if action == "delete":
                        if target.id == user.id:
                            context["error"] = "No puedes eliminar tu propio usuario."
                        else:
                            target.delete()
                            context["success"] = "Usuario eliminado."
                        return render(request, "listado_usuarios.html", context)

                    email = request.POST.get("email", "").strip()
                    username = request.POST.get("username", "").strip()
                    nombre = request.POST.get("nombre", "").strip()
                    apellido = request.POST.get("apellido", "").strip()
                    edad_raw = request.POST.get("edad", "").strip()
                    telefono = request.POST.get("telefono", "").strip()
                    tipo_usuario = request.POST.get("tipo_usuario", "").strip() or None
                    area = request.POST.get("area", "").strip() or None
                    grupos_ids = request.POST.getlist("grupos")
                    valid_tipo_usuario = {key for key, _ in TIPO_USUARIO_CHOICES}
                    valid_area = {key for key, _ in AREA_CHOICES}

                    if not email or not username or not nombre:
                        context["error"] = "Email, usuario y nombre son obligatorios."
                    else:
                        edad_val = None
                        if edad_raw:
                            if edad_raw.isdigit():
                                edad_val = int(edad_raw)
                            else:
                                context["error"] = "La edad debe ser un numero."
                        if tipo_usuario and tipo_usuario not in valid_tipo_usuario:
                            context["error"] = "El tipo de usuario no es valido."
                        if area and area not in valid_area:
                            context["error"] = "El area no es valida."

                    if "error" not in context:
                        try:
                            target.email = email
                            target.username = username
                            target.nombre = nombre
                            target.apellido = apellido
                            target.edad = edad_val
                            target.telefono = telefono or None
                            target.tipo_usuario = tipo_usuario
                            target.area = area
                            target.save()

                            if grupos_ids:
                                grupos_validos = Group.objects.filter(id__in=grupos_ids)
                                target.groups.set(grupos_validos)
                            else:
                                target.groups.clear()

                            context["success"] = "Usuario actualizado."
                        except IntegrityError:
                            context["error"] = "El email o usuario ya existe."

        context["usuarios"] = Usuario.objects.order_by("email")
        context["grupos"] = Group.objects.order_by("name")

    return render(request, "listado_usuarios.html", context)
