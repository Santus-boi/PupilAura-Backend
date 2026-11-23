from django.urls import path

from . import views


urlpatterns = [
    path(
        "enroll/<int:course_id>/",
        views.enroll,
        name="enroll",
    ),
]