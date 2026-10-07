from django.urls import path

from . import views

app_name = "taxonomy"

urlpatterns = [
    path("regions/", views.regions, name="regions"),
    path("countries/", views.countries, name="countries"),
    path("themes/", views.themes, name="themes"),
]
