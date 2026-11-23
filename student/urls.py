from django.urls import path
from . import views


urlpatterns = [
    path(
        "dashboard/",
        views.dashboard,
        name="student_dashboard",
    ),

    path(
        "courses/",
        views.my_courses,
        name="my_courses",
    ),

    path(
        "progress/",
        views.my_progress,
        name="my_progress",
    ),

    path(
        "assessments/",
        views.assessments,
        name="student_assessments",
    ),

    path(
        "certificates/",
        views.certificates,
        name="student_certificates",
    ),

    path(
        "profile/",
        views.profile,
        name="student_profile",
    ),

    path(
        "settings/",
        views.settings,
        name="student_settings",
    ),

    # Curriculum
    path(
        "classes/",
        views.classes,
        name="student_classes",
    ),

    path(
        "classes/<int:class_id>/subjects/",
        views.subjects,
        name="student_subjects",
    ),

    path(
        "subjects/<int:subject_id>/start/",
        views.start_subject,
        name="student_start_subject",
    ),

    path(
        "subjects/<int:subject_id>/terms/",
        views.terms,
        name="student_terms",
    ),

    path(
        "terms/<int:term_id>/weeks/",
        views.weeks,
        name="student_weeks",
    ),

    path(
        "weeks/<int:week_id>/lessons/",
        views.lessons,
        name="student_lessons",
    ),

    # Lesson detail
    path(
        "lessons/<int:lesson_id>/",
        views.lesson_detail,
        name="student_lesson_detail",
    ),

    # Complete lesson
    path(
        "lessons/<int:lesson_id>/complete/",
        views.complete_lesson,
        name="complete_lesson",
    ),

    path(
        "assessments/<int:attempt_id>/result/",
        views.assessment_result,
        name="student_assessment_result",
    ),
]