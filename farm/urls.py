from django.urls import path

from farm import views

urlpatterns = [
    path("", views.entrance, name="entrance"),
    path("field/", views.field, name="field"),
    path("role/", views.choose_role, name="role_choose"),
    path("role/clear/", views.clear_role, name="role_clear"),
    path("lang/", views.set_lang, name="lang"),
    path("api/boundaries/", views.boundaries, name="field_boundaries"),
    path("api/search/", views.search_places, name="field_search"),
    path("api/places/", views.place_children, name="field_places"),
    path("api/locate/", views.locate_place, name="field_locate"),
    path("api/advice/", views.advice_view, name="field_advice"),
    path("api/routine/", views.routine_view, name="field_routine"),
    path("api/hear/", views.hear_view, name="field_hear"),
    path("api/plans/", views.plans, name="field_plans"),
    path("api/plans/save/", views.save_plan, name="field_save"),
    path("api/plans/<int:plan_id>/check/", views.check_plan, name="field_check"),
]
