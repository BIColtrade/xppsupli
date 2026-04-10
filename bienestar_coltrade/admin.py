from django.contrib import admin

from .models import AccionPPS, PuntosUsuario, RegistroAccion, Beneficio, ReclamoBeneficio


@admin.register(AccionPPS)
class AccionPPSAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "nivel",
        "puntos_min",
        "puntos_max",
        "puntos_default",
        "destinatarios",
        "aplica_empresa",
        "solo_lideres",
        "activa",
        "fecha_inicio",
        "fecha_fin",
    )
    list_filter = ("nivel", "destinatarios", "aplica_empresa", "solo_lideres", "activa")
    search_fields = ("nombre", "descripcion")


@admin.register(PuntosUsuario)
class PuntosUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "puntos_totales", "nivel", "fecha_actualizacion")
    list_filter = ("nivel",)
    search_fields = ("usuario__email", "usuario__username", "usuario__nombre", "usuario__apellido")


@admin.register(RegistroAccion)
class RegistroAccionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "accion", "estado", "puntos_asignados", "fecha_registro", "fecha_resolucion")
    list_filter = ("estado", "accion__nivel")
    search_fields = ("usuario__email", "usuario__username", "accion__nombre", "descripcion_evidencia")


@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "puntos_requeridos", "disponible", "stock", "imagen_url")
    list_filter = ("categoria", "disponible")
    search_fields = ("nombre", "descripcion")


@admin.register(ReclamoBeneficio)
class ReclamoBeneficioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "beneficio", "estado", "puntos_descontados", "fecha_reclamo", "aprobado_por")
    list_filter = ("estado",)
    search_fields = ("usuario__email", "usuario__username", "beneficio__nombre")
