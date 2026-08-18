from django.contrib import admin

from .models import (
    Competencia,
    Pregunta,
    CicloEvaluacion,
    AsignacionEvaluacion,
    RespuestaEvaluacion,
    ResultadoEvaluacion,
    PlanAccion,
)


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "orden", "activa", "fecha_creacion")
    list_filter = ("activa",)
    search_fields = ("codigo", "nombre", "descripcion")
    ordering = ("orden", "codigo")


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "competencia",
        "tipo_evaluacion",
        "tipo_pregunta",
        "peso",
        "orden",
        "obligatoria",
        "activa",
    )
    list_filter = ("tipo_evaluacion", "tipo_pregunta", "competencia", "activa", "obligatoria")
    search_fields = ("enunciado", "competencia__nombre", "competencia__codigo")
    ordering = ("competencia__orden", "orden")


@admin.register(CicloEvaluacion)
class CicloEvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tipo",
        "estado",
        "fecha_inicio",
        "fecha_cierre",
        "anonimato",
        "creado_por",
    )
    list_filter = ("estado", "tipo", "anonimato")
    search_fields = ("nombre", "descripcion")
    date_hierarchy = "fecha_inicio"


@admin.register(AsignacionEvaluacion)
class AsignacionEvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "ciclo",
        "evaluador",
        "evaluado",
        "rol_evaluador",
        "tipo_evaluacion",
        "estado",
        "fecha_completada",
    )
    list_filter = ("estado", "rol_evaluador", "tipo_evaluacion", "ciclo")
    search_fields = (
        "evaluador__email",
        "evaluador__nombre",
        "evaluado__email",
        "evaluado__nombre",
        "ciclo__nombre",
    )
    autocomplete_fields = ("evaluador", "evaluado")


@admin.register(RespuestaEvaluacion)
class RespuestaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ("asignacion", "pregunta", "valor", "fecha_respuesta")
    list_filter = ("pregunta__tipo_evaluacion", "pregunta__competencia")
    search_fields = (
        "asignacion__evaluador__email",
        "asignacion__evaluado__email",
        "pregunta__enunciado",
    )


@admin.register(ResultadoEvaluacion)
class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "evaluado",
        "ciclo",
        "tipo_evaluacion",
        "total_evaluadores",
        "puntaje_total",
        "porcentaje",
        "semaforo",
        "fecha_calculo",
    )
    list_filter = ("semaforo", "tipo_evaluacion", "ciclo")
    search_fields = ("evaluado__email", "evaluado__nombre", "ciclo__nombre")


@admin.register(PlanAccion)
class PlanAccionAdmin(admin.ModelAdmin):
    list_display = (
        "resultado",
        "responsable",
        "fecha_compromiso",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("estado",)
    search_fields = (
        "descripcion",
        "responsable__email",
        "responsable__nombre",
        "resultado__evaluado__email",
    )
    autocomplete_fields = ("responsable", "creado_por")
