from django.contrib import admin

from .models import (
    CicloPulse,
    MiembroLeadershipTeam,
    ParticipacionReto,
    Pilar,
    PuntajeMensual,
    RetoSemanal,
)


@admin.register(Pilar)
class PilarAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "puntaje_max", "orden", "activo")
    list_filter = ("activo",)
    search_fields = ("codigo", "nombre", "descripcion")
    ordering = ("orden", "nombre")


@admin.register(MiembroLeadershipTeam)
class MiembroLeadershipTeamAdmin(admin.ModelAdmin):
    list_display = ("usuario", "activo", "fecha_ingreso")
    list_filter = ("activo", "usuario__area")
    search_fields = ("usuario__nombre", "usuario__apellido", "usuario__email")


@admin.register(CicloPulse)
class CicloPulseAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "anio", "mes", "estado", "fecha_inicio", "fecha_fin",
        "ranking_publicado", "creado_por",
    )
    list_filter = ("estado", "anio", "ranking_publicado")
    search_fields = ("nombre", "descripcion")
    ordering = ("-anio", "-mes")


@admin.register(RetoSemanal)
class RetoSemanalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "ciclo", "semana", "pilar", "fecha_inicio", "fecha_cierre", "activo")
    list_filter = ("ciclo", "pilar", "semana", "activo")
    search_fields = ("titulo", "descripcion")
    ordering = ("ciclo", "semana")


@admin.register(ParticipacionReto)
class ParticipacionRetoAdmin(admin.ModelAdmin):
    list_display = (
        "lider", "reto", "estado", "participo", "cumplio", "puntaje_total",
        "observaciones", "validado_por",
    )
    list_filter = ("estado", "participo", "cumplio", "reto__ciclo", "reto__pilar")
    search_fields = (
        "lider__nombre", "lider__apellido", "reto__titulo", "observaciones",
    )
    ordering = ("reto__semana", "lider__nombre")


@admin.register(PuntajeMensual)
class PuntajeMensualAdmin(admin.ModelAdmin):
    list_display = (
        "lider", "ciclo", "retos_evaluados", "retos_participados", "retos_cumplidos",
        "pct_participacion", "pct_cumplimiento", "semaforo", "posicion", "fecha_calculo",
    )
    list_filter = ("ciclo", "semaforo")
    search_fields = ("lider__nombre", "lider__apellido")
    ordering = ("ciclo", "posicion")
