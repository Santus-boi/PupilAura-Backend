from django.urls import path

from . import views


urlpatterns = [
    path(
        "lessons/<int:lesson_id>/",
        views.lesson_detail,
        name="learning_lesson_detail",
    ),
]