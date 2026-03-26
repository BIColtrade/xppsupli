from django.contrib import admin
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", core_views.home, name="home"),
    path("coltrxde/", include("core.urls")),
    path("coltrxde/", include("user.urls")),
    path("abastecimientos/", include("abastecimientos.urls")),
    path("portafolio/mayoristas/", include("portafolio_mayoristas.urls")),
    path("malla/operaciones/coltrxde/", include("malla_operaciones_trade.urls")),
    path("bienestar/coltrxde/", include("bienestar_coltrade.urls")),
]
