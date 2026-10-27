from django.urls import include, path

urlpatterns = [
    path("", include("farm.urls")),
    path("", include("sheet.urls")),
]
