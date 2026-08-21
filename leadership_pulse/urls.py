from django.urls import path

from . import views

app_name = "leadership_pulse"

urlpatterns = [
    # Home
    path("home/", views.home_leadership_pulse, name="home_leadership_pulse"),

    # Participacion del lider
    path("mis-retos/", views.mis_retos, name="mis_retos"),
    path("mis-retos/<int:participacion_id>/reportar/", views.reportar_reto, name="reportar_reto"),
    path("mi-pulse/", views.mi_pulse, name="mi_pulse"),

    # Ranking
    path("ranking/", views.ranking, name="ranking"),
    path("pulse/<int:usuario_id>/", views.pulse_lider, name="pulse_lider"),

    # Registro de retos (People / Admin)
    path("validacion/", views.bandeja_validacion, name="bandeja_validacion"),
    path("validacion/<int:participacion_id>/", views.validar_participacion, name="validar_participacion"),
    path("retos/<int:reto_id>/registro/", views.registro_reto, name="registro_reto"),

    # Ciclos mensuales
    path("ciclos/", views.gestionar_ciclos, name="gestionar_ciclos"),
    path("ciclos/crear/", views.crear_ciclo, name="crear_ciclo"),
    path("ciclos/<int:ciclo_id>/editar/", views.editar_ciclo, name="editar_ciclo"),
    path("ciclos/<int:ciclo_id>/consolidar/", views.consolidar_ciclo, name="consolidar_ciclo"),
    path("ciclos/<int:ciclo_id>/publicar-ranking/", views.publicar_ranking, name="publicar_ranking"),

    # Retos semanales
    path("ciclos/<int:ciclo_id>/retos/", views.gestionar_retos, name="gestionar_retos"),
    path("ciclos/<int:ciclo_id>/retos/crear/", views.crear_reto, name="crear_reto"),
    path("retos/<int:reto_id>/editar/", views.editar_reto, name="editar_reto"),
    path("retos/<int:reto_id>/eliminar/", views.eliminar_reto, name="eliminar_reto"),

    # Pilares
    path("pilares/", views.gestionar_pilares, name="gestionar_pilares"),
    path("pilares/crear/", views.crear_pilar, name="crear_pilar"),
    path("pilares/sembrar/", views.sembrar_pilares, name="sembrar_pilares"),
    path("pilares/<int:pilar_id>/editar/", views.editar_pilar, name="editar_pilar"),

    # Leadership Team
    path("miembros/", views.gestionar_miembros, name="gestionar_miembros"),
    path("miembros/sincronizar/", views.sincronizar_miembros, name="sincronizar_miembros"),
    path("miembros/agregar/", views.agregar_miembro, name="agregar_miembro"),
    path("miembros/<int:miembro_id>/alternar/", views.alternar_miembro, name="alternar_miembro"),
]
