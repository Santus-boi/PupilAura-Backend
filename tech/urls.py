from django.urls import path

from . import views


app_name = "tech"


urlpatterns = [
    path(
        "",
        views.tech_home,
        name="tech_home",
    ),

    path(
        "category/<int:category_id>/",
        views.category_detail,
        name="tech_category_detail",
    ),

    path(
        "course/<int:course_id>/",
        views.course_detail,
        name="tech_course_detail",
    ),

    path(
        "course/<int:course_id>/module/<int:module_id>/",
        views.module_detail,
        name="tech_module_detail",
    ),

    path(
        "lesson/<int:lesson_id>/",
        views.lesson_detail,
        name="tech_lesson_detail",
    ),

    path(
        "lesson/<int:lesson_id>/complete/",
        views.complete_lesson,
        name="tech_complete_lesson",
    ),

    # --------------------------------------------------------
    # TECH QUIZ
    # --------------------------------------------------------

    path(
        "lesson/<int:lesson_id>/quiz/",
        views.quiz_detail,
        name="tech_quiz",
    ),

    path(
        "quiz/<int:quiz_id>/submit/",
        views.submit_quiz,
        name="tech_submit_quiz",
    ),

    path(
        "quiz/result/<int:attempt_id>/",
        views.quiz_result,
        name="tech_quiz_result",
    ),
]