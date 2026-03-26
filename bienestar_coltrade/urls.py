from django.urls import path

from . import views

app_name = "home_bienestar_coltrade"

urlpatterns = [
    path("home/", views.home_bienestar_coltrade, name="home_bienestar_coltrade"),
]
