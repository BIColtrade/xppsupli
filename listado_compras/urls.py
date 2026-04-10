from django.urls import path

from . import views

app_name = "listado_compras"

urlpatterns = [
    path("home/", views.home_listado_compras, name="home_listado_compras"),
    path(
        "cruce_producto_internacional/",
        views.cruce_producto_internacional,
        name="cruce_producto_internacional",
    ),
    path(
        "cruce_producto_internacional/detalle/",
        views.cruce_producto_internacional_detalle,
        name="cruce_producto_internacional_detalle",
    ),
    path(
        "cruce_producto_internacional/exportar/",
        views.cruce_producto_internacional_export,
        name="cruce_producto_internacional_export",
    ),
    path(
        "cruce_producto_internacional/detalle-general/",
        views.cruce_producto_internacional_detalle_general,
        name="cruce_producto_internacional_detalle_general",
    ),
    path(
        "cruce_producto_internacional/detalle-general/exportar/",
        views.cruce_producto_internacional_detalle_general_export,
        name="cruce_producto_internacional_detalle_general_export",
    ),
    path(
        "cruce_producto_nacional/",
        views.cruce_producto_nacional,
        name="cruce_producto_nacional",
    ),
    path(
        "cruce_producto_nacional/detalle/",
        views.cruce_producto_nacional_detalle,
        name="cruce_producto_nacional_detalle",
    ),
    path(
        "cruce_producto_nacional/exportar/",
        views.cruce_producto_nacional_export,
        name="cruce_producto_nacional_export",
    ),
    path(
        "cruce_producto_nacional/detalle-general/",
        views.cruce_producto_nacional_detalle_general,
        name="cruce_producto_nacional_detalle_general",
    ),
    path(
        "cruce_producto_nacional/detalle-general/exportar/",
        views.cruce_producto_nacional_detalle_general_export,
        name="cruce_producto_nacional_detalle_general_export",
    ),
    path("listado_productos_supli/", views.listado_productos_supli, name="listado_productos_supli"),
    path("crud_productos_supli/", views.crud_productos_supli, name="crud_productos_supli"),
    path(
        "crud_productos_supli/importar/",
        views.productos_supli_import,
        name="productos_supli_import",
    ),
    path(
        "crud_productos_supli/exportar/",
        views.productos_supli_export,
        name="productos_supli_export",
    ),
    path(
        "crud_listado_internacional/",
        views.crud_listado_internacional,
        name="crud_listado_internacional",
    ),
    path(
        "crud_listado_internacional/importar/",
        views.productos_internacionales_import,
        name="productos_internacionales_import",
    ),
    path(
        "crud_listado_internacional/exportar/",
        views.productos_internacionales_export,
        name="productos_internacionales_export",
    ),
    path(
        "crud_listado_nacional/",
        views.crud_listado_nacional,
        name="crud_listado_nacional",
    ),
    path(
        "crud_listado_nacional/importar/",
        views.productos_nacionales_import,
        name="productos_nacionales_import",
    ),
    path(
        "crud_listado_nacional/exportar/",
        views.productos_nacionales_export,
        name="productos_nacionales_export",
    ),
]
