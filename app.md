Email: pxlxciosjulixn@gmail.com
Username: julixnpxlxcios
Password: Pass-2023
Password (again):


Integración de permisos


genial ahora revisa algo

tengo estos grupos

abastecimientos

    admin

    bienestarcoltrade

    mallaoperaciones

    portafoliomayoristas

admin tiene acceso a todas las urls de la aplicación

ahora

todos los demas tiene acceso a

C:\Users\Julian Herreño\OneDrive - Colombian Trade Company SAS\DATA\02. AREAS\DATA\Julian Estif Herreno Palacios\xppcoltrade\user

solo a estas

  path("login", views.login_view, name="login"),

    path("logout", views.logout_view, name="logout"),

    path("settings-user/", views.settings_user, name="settings_user"),

path("home_user/", views.home_user, name="home_user"),

y ahora

abastecimientos:  C:\Users\Julian Herreño\OneDrive - Colombian Trade Company SAS\DATA\02. AREAS\DATA\Julian Estif Herreno Palacios\xppcoltrade\abastecimientos\urls.py

    bienestarcoltrade: C:\Users\Julian Herreño\OneDrive - Colombian Trade Company SAS\DATA\02. AREAS\DATA\Julian Estif Herreno Palacios\xppcoltrade\bienestar_coltrade\urls.py

    mallaoperaciones:  C:\Users\Julian Herreño\OneDrive - Colombian Trade Company SAS\DATA\02. AREAS\DATA\Julian Estif Herreno Palacios\xppcoltrade\malla_operaciones_trade\urls.py

    portafoliomayoristas: C:\Users\Julian Herreño\OneDrive - Colombian Trade Company SAS\DATA\02. AREAS\DATA\Julian Estif Herreno Palacios\xppcoltrade\portafolio_mayoristas\urls.py
