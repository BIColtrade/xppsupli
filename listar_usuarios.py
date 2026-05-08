import os
import sys

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

django.setup()

from user.models import Usuario  # noqa: E402


def yes_no(value):
    return "si" if value else "no"


def main():
    users = (
        Usuario.objects.prefetch_related("groups")
        .order_by("id")
        .values(
            "id",
            "email",
            "username",
            "nombre",
            "apellido",
            "tipo_usuario",
            "area",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
        )
    )

    users = list(users)
    if not users:
        print("No hay usuarios registrados.")
        return

    header = (
        "ID | Email | Username | Nombre | Rol | Area | Activo | Staff | Superuser | "
        "Password hash"
    )
    print(header)
    print("-" * len(header))

    for user in users:
        apellido = user.get("apellido") or ""
        nombre = f"{user.get('nombre') or ''} {apellido}".strip() or "-"
        rol = user.get("tipo_usuario") or "-"
        area = user.get("area") or "-"
        password_hash = user.get("password") or "-"

        print(
            f"{user['id']} | "
            f"{user['email']} | "
            f"{user['username']} | "
            f"{nombre} | "
            f"{rol} | "
            f"{area} | "
            f"{yes_no(user['is_active'])} | "
            f"{yes_no(user['is_staff'])} | "
            f"{yes_no(user['is_superuser'])} | "
            f"{password_hash}"
        )

    print()
    print("Nota: Django no guarda contraseñas en texto plano; solo puede mostrarse el hash.")


if __name__ == "__main__":
    main()
