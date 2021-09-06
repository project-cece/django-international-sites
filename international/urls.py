from international import views
from django.urls import path

urlpatterns = [
    path(
        r"localize/",
        views.get_country_from_request,
        name="get_country_from_request",
    ),
]