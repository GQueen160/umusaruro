from django.urls import path

from sheet import views

urlpatterns = [
    path("", views.overview, name="overview"),
    path("district/<slug:slug>/", views.district, name="district"),
    path("method/", views.method, name="method"),
]
