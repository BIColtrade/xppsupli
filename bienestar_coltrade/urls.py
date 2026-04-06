from django.urls import path

from . import views

app_name = "home_bienestar_coltrade"

urlpatterns = [
    # Home
    path("home/", views.home_bienestar_coltrade, name="home_bienestar_coltrade"),

    # Colaborador / todos
    path("mi-perfil/", views.mi_perfil_pps, name="mi_perfil_pps"),
    path("catalogo-acciones/", views.catalogo_acciones_pps, name="catalogo_acciones_pps"),
    path("registrar-accion/", views.registrar_accion_pps, name="registrar_accion_pps"),
    path("capacitacion/<int:accion_id>/", views.ver_capacitacion_pps, name="ver_capacitacion_pps"),
    path("capacitacion/<int:accion_id>/progreso/", views.actualizar_progreso_capacitacion, name="actualizar_progreso_capacitacion"),
    path("mis-acciones/", views.mis_acciones_pps, name="mis_acciones_pps"),
    path("mis-beneficios/", views.mis_beneficios_pps, name="mis_beneficios_pps"),
    path("ranking/", views.ranking_pps, name="ranking_pps"),
    path("beneficios/", views.catalogo_beneficios_pps, name="catalogo_beneficios_pps"),
    path("beneficios/reclamar/<int:beneficio_id>/", views.reclamar_beneficio_pps, name="reclamar_beneficio_pps"),
    path("beneficios/crear/", views.crear_beneficio_pps, name="crear_beneficio_pps"),
    path("beneficios/gestionar/", views.gestionar_beneficios_pps, name="gestionar_beneficios_pps"),
    path("beneficios/editar/<int:beneficio_id>/", views.editar_beneficio_pps, name="editar_beneficio_pps"),
    path("beneficios/eliminar/<int:beneficio_id>/", views.eliminar_beneficio_pps, name="eliminar_beneficio_pps"),

    # Lider / Admin
    path("panel-lider/", views.panel_lider_pps, name="panel_lider_pps"),
    path("panel-lider/resolver/<int:registro_id>/", views.resolver_accion_pps, name="resolver_accion_pps"),
    path("panel-lider/resolver-reclamo/<int:reclamo_id>/", views.resolver_reclamo_beneficio_pps, name="resolver_reclamo_beneficio_pps"),
    path("gestionar-acciones/", views.gestionar_acciones_pps, name="gestionar_acciones_pps"),
    path("gestionar-acciones/crear/", views.crear_accion_pps, name="crear_accion_pps"),
    path("gestionar-acciones/editar/<int:accion_id>/", views.editar_accion_pps, name="editar_accion_pps"),
    path("gestionar-acciones/eliminar/<int:accion_id>/", views.eliminar_accion_pps, name="eliminar_accion_pps"),
]
