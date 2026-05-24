from django.urls import path

from . import views

app_name = "modulo_valoracion"

urlpatterns = [
    # Home
    path("home/", views.home_modulo_valoracion, name="home_modulo_valoracion"),

    # Configuracion: Competencias
    path("competencias/", views.gestionar_competencias, name="gestionar_competencias"),
    path("competencias/crear/", views.crear_competencia, name="crear_competencia"),
    path("competencias/editar/<int:competencia_id>/", views.editar_competencia, name="editar_competencia"),
    path("competencias/eliminar/<int:competencia_id>/", views.eliminar_competencia, name="eliminar_competencia"),

    # Configuracion: Preguntas
    path("preguntas/", views.gestionar_preguntas, name="gestionar_preguntas"),
    path("preguntas/crear/", views.crear_pregunta, name="crear_pregunta"),
    path("preguntas/editar/<int:pregunta_id>/", views.editar_pregunta, name="editar_pregunta"),
    path("preguntas/eliminar/<int:pregunta_id>/", views.eliminar_pregunta, name="eliminar_pregunta"),

    # Ciclos
    path("ciclos/", views.gestionar_ciclos, name="gestionar_ciclos"),
    path("ciclos/crear/", views.crear_ciclo, name="crear_ciclo"),
    path("ciclos/editar/<int:ciclo_id>/", views.editar_ciclo, name="editar_ciclo"),
    path("ciclos/<int:ciclo_id>/consolidar/", views.consolidar_ciclo, name="consolidar_ciclo"),

    # Detalle de resultado
    path("resultados/<int:resultado_id>/", views.detalle_resultado, name="detalle_resultado"),

    # Asignaciones por ciclo
    path("ciclos/<int:ciclo_id>/asignaciones/", views.asignaciones_ciclo, name="asignaciones_ciclo"),
    path("ciclos/<int:ciclo_id>/asignaciones/crear/", views.crear_asignacion, name="crear_asignacion"),
    path("asignaciones/<int:asignacion_id>/eliminar/", views.eliminar_asignacion, name="eliminar_asignacion"),

    # Evaluador
    path("mis-evaluaciones/", views.mis_evaluaciones, name="mis_evaluaciones"),
    path("mis-evaluaciones/<int:asignacion_id>/responder/", views.responder_evaluacion, name="responder_evaluacion"),

    # Resultados
    path("mis-resultados/", views.mis_resultados, name="mis_resultados"),
    path("resultados-equipo/", views.resultados_equipo, name="resultados_equipo"),

    # Jerarquia (jefe directo + cargo)
    path("jerarquia/", views.gestionar_jerarquia, name="gestionar_jerarquia"),
    path("jerarquia/<int:usuario_id>/actualizar/", views.actualizar_jefe_directo, name="actualizar_jefe_directo"),

    # Planes de accion
    path("planes-accion/", views.listar_planes_accion, name="listar_planes_accion"),
]
