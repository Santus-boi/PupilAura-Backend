from django.urls import path

from . import views


app_name = "exam_prep"


urlpatterns = [
    path(
        "",
        views.exam_home,
        name="home",
    ),

    path(
        "exam/<int:exam_id>/",
        views.exam_detail,
        name="exam_detail",
    ),

    path(
        "subject/<int:subject_id>/",
        views.subject_detail,
        name="subject_detail",
    ),

    path(
        "subject/<int:subject_id>/year/<int:year_id>/",
        views.year_detail,
        name="year_detail",
    ),

    path(
        "resource/<int:resource_id>/",
        views.resource_detail,
        name="resource_detail",
    ),

    path(
        "resource/<int:resource_id>/start/",
        views.start_test,
        name="start_test",
    ),

    path(
        "attempt/<int:attempt_id>/submit/",
        views.submit_test,
        name="submit_test",
    ),

    path(
        "attempt/<int:attempt_id>/result/",
        views.result,
        name="result",
    ),

     path(
        "history/",
        views.attempt_history,
        name="history",
    ),
]