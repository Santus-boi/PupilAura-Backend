from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Lesson


@login_required
def lesson_detail(request, lesson_id):
    """
    Display a lesson using the current curriculum structure:

        School Class
            ↓
        Subject
            ↓
        Term
            ↓
        Week
            ↓
        Lesson
    """

    student_profile = getattr(
        request.user,
        "student_profile",
        None,
    )

    if student_profile is None:
        return redirect("/")

    lesson = get_object_or_404(
        Lesson.objects
        .select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",
        )
        .prefetch_related(
            "videos",
            "images",
            "resources",
            "quizzes",
        ),
        id=lesson_id,
        published=True,
        week__term__subject__enrollments__student=student_profile,
    )

    enrollment = get_object_or_404(
        student_profile.enrollments,
        subject=lesson.week.term.subject,
    )

    progress = (
        enrollment.lesson_progress
        .filter(
            lesson=lesson,
        )
        .first()
    )

    quiz = (
        lesson.quizzes
        .filter(
            published=True,
        )
        .first()
    )

    return render(
        request,
        "student/lesson_detail.html",
        {
            "student": student_profile,
            "lesson": lesson,
            "enrollment": enrollment,
            "progress": progress,
            "quiz": quiz,
            "subject": lesson.week.term.subject,
            "term": lesson.week.term,
            "week": lesson.week,
            "school_class": lesson.week.term.subject.school_class,
        },
    )


@login_required
def home(request):
    return redirect("student_dashboard")