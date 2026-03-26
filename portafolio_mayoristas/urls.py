from django.urls import path

from . import views

app_name = "portafolio_mayoristas"

urlpatterns = [
    path("home/", views.home_portafolio_mayoristas, name="home_portafolio_mayoristas"),
]
