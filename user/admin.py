from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "nombre", "apellido", "is_active", "is_staff")
    search_fields = ("email", "username", "nombre", "apellido")
    list_filter = ("is_active", "is_staff")
