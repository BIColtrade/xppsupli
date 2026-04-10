from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("recuperar-password", views.recuperar_password, name="recuperar_password"),
    path("logout", views.logout_view, name="logout"),
    path("settings-user/", views.settings_user, name="settings_user"),
    path("crear-usuarios/", views.crear_usuario, name="crear_usuarios"),
    path("home_user/", views.home_user, name="home_user"),
    path("listado-usuarios/", views.listado_usuarios, name="listado_usuarios"),
]
