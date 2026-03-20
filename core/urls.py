from django.urls import path

from . import views

urlpatterns = [
    path("home", views.home_autenticado, name="home_autenticado"),

]
