from django.urls import path

from sheet import views

urlpatterns = [
    path("advisor/", views.advisor, name="advisor"),
    path("advisor/<slug:key>/", views.crop, name="crop"),
    path("sheet/", views.overview, name="overview"),
    path("district/<slug:slug>/", views.district, name="district"),
    path("district/<slug:slug>/panel/", views.district_panel, name="district_panel"),
    path("method/", views.method, name="method"),
]
