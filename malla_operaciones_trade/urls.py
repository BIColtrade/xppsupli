from django.urls import path

from . import views

app_name = "malla_operaciones_trade"

urlpatterns = [
    path("home/", views.home_malla_operaciones, name="home_malla_operaciones"),
    path("asesores/", views.asesores, name="asesores"),
    path("coordinadores/", views.coordinadores, name="coordinadores"),
    path("punto-venta/", views.punto_venta, name="punto_venta"),
    path("registro-horario/", views.registro_horario, name="registro_horario"),
    path("dashboard-horas/", views.dashboard_horas, name="dashboard_horas"),
]
