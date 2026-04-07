from django.urls import path

from . import views

app_name = "listado_compras"

urlpatterns = [
    path("home/", views.home_listado_compras, name="home_listado_compras"),
    path("listado_productos_supli/", views.listado_productos_supli, name="listado_productos_supli"),
]
