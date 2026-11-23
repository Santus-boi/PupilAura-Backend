from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from payments.models import ContentType
from payments.services import has_access

from .models import (
    TechCategory,
    TechCourse,
    TechEnrollment,
    TechLesson,
    TechLessonProgress,
    TechModule,
    TechQuiz,
    TechQuizAttempt,
)


def student_only(request):
    """Make sure the logged-in user is a student."""
    if not request.user.is_authenticated:
        return None

    if getattr(request.user, "role", None) != "student":
        return None

    return request.user


def _require_course_access(request, course):
    """Check that the current user has paid access to a Tech course."""
    return has_access(
        request.user,
        ContentType.TECH_COURSE,
        course.id,
    )


@login_required
def tech_home(request):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    categories = (
        TechCategory.objects
        .filter(published=True)
        .annotate(course_count=Count("courses", distinct=True))
    )

    enrollments = (
        TechEnrollment.objects
        .filter(student=student)
        .select_related("course", "course__category")
    )

    context = {
        "categories": categories,
        "enrollments": enrollments,
    }

    return render(request, "tech/home.html", context)


@login_required
def category_detail(request, category_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    category = get_object_or_404(
        TechCategory,
        id=category_id,
        published=True,
    )

    courses = (
        TechCourse.objects
        .filter(category=category, published=True)
        .order_by("-created_at")
    )

    enrolled_course_ids = set(
        TechEnrollment.objects
        .filter(student=student, course__in=courses)
        .values_list("course_id", flat=True)
    )

    context = {
        "category": category,
        "courses": courses,
        "enrolled_course_ids": enrolled_course_ids,
    }

    return render(request, "tech/courses.html", context)


@login_required
def course_detail(request, course_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    course = get_object_or_404(
        TechCourse.objects.select_related("category"),
        id=course_id,
        published=True,
    )

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    modules = (
        TechModule.objects
        .filter(course=course, published=True)
        .prefetch_related("lessons")
        .order_by("order", "id")
    )

    enrollment = (
        TechEnrollment.objects
        .filter(student=student, course=course)
        .first()
    )

    completed_lesson_ids = set()

    if enrollment:
        completed_lesson_ids = set(
            TechLessonProgress.objects
            .filter(enrollment=enrollment, completed=True)
            .values_list("lesson_id", flat=True)
        )

    total_lessons = TechLesson.objects.filter(
        module__course=course,
        module__published=True,
        published=True,
    ).count()

    completed_lessons = len(completed_lesson_ids)

    progress_percentage = 0

    if total_lessons:
        progress_percentage = round((completed_lessons / total_lessons) * 100)

    context = {
        "course": course,
        "modules": modules,
        "enrollment": enrollment,
        "completed_lesson_ids": completed_lesson_ids,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": progress_percentage,
        "access": access,
    }

    return render(request, "tech/course_detail.html", context)


@login_required
def module_detail(request, course_id, module_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    course = get_object_or_404(
        TechCourse,
        id=course_id,
        published=True,
    )

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    module = get_object_or_404(
        TechModule,
        id=module_id,
        course=course,
        published=True,
    )

    enrollment = (
        TechEnrollment.objects
        .filter(student=student, course=course)
        .first()
    )

    lessons = (
        TechLesson.objects
        .filter(module=module, published=True)
        .order_by("order", "id")
    )

    completed_lesson_ids = set()

    if enrollment:
        completed_lesson_ids = set(
            TechLessonProgress.objects
            .filter(enrollment=enrollment, completed=True)
            .values_list("lesson_id", flat=True)
        )

    context = {
        "course": course,
        "module": module,
        "lessons": lessons,
        "enrollment": enrollment,
        "completed_lesson_ids": completed_lesson_ids,
        "access": access,
    }

    return render(request, "tech/module_detail.html", context)


@login_required
def lesson_detail(request, lesson_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
            "module__course__category",
        ),
        id=lesson_id,
        published=True,
        module__published=True,
        module__course__published=True,
    )

    course = lesson.module.course
    module = lesson.module

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    enrollment = (
        TechEnrollment.objects
        .filter(student=student, course=course)
        .first()
    )

    progress = None

    if enrollment:
        progress = (
            TechLessonProgress.objects
            .filter(enrollment=enrollment, lesson=lesson)
            .first()
        )

    videos = lesson.videos.filter(published=True).order_by("order", "id")
    images = lesson.images.filter(published=True).order_by("order", "id")
    resources = lesson.resources.filter(published=True).order_by("order", "id")

    quiz = (
        TechQuiz.objects
        .filter(lesson=lesson, published=True)
        .prefetch_related("questions", "questions__choices")
        .first()
    )

    context = {
        "lesson": lesson,
        "course": course,
        "module": module,
        "enrollment": enrollment,
        "progress": progress,
        "videos": videos,
        "images": images,
        "resources": resources,
        "quiz": quiz,
        "access": access,
    }

    return render(request, "tech/lesson_detail.html", context)


@login_required
def complete_lesson(request, lesson_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    if request.method != "POST":
        return redirect(
            "tech:tech_lesson_detail",
            lesson_id=lesson_id,
        )

    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
        ),
        id=lesson_id,
        published=True,
        module__published=True,
        module__course__published=True,
    )

    course = lesson.module.course

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    enrollment, created = TechEnrollment.objects.get_or_create(
        student=student,
        course=course,
    )

    progress, _ = TechLessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
    )

    progress.completed = True
    progress.save()

    total_lessons = TechLesson.objects.filter(
        module__course=course,
        module__published=True,
        published=True,
    ).count()

    completed_lessons = TechLessonProgress.objects.filter(
        enrollment=enrollment,
        completed=True,
        lesson__module__course=course,
        lesson__module__published=True,
        lesson__published=True,
    ).count()

    if total_lessons > 0 and completed_lessons >= total_lessons:
        enrollment.completed = True
        enrollment.save(update_fields=["completed"])

    messages.success(request, "Lesson completed successfully.")

    return redirect(
        "tech:tech_lesson_detail",
        lesson_id=lesson.id,
    )


@login_required
def quiz_detail(request, lesson_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
        ),
        id=lesson_id,
        published=True,
        module__published=True,
        module__course__published=True,
    )

    course = lesson.module.course

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    quiz = get_object_or_404(
        TechQuiz.objects.prefetch_related("questions__choices"),
        lesson=lesson,
        published=True,
    )

    questions = quiz.questions.prefetch_related("choices").all()

    context = {
        "quiz": quiz,
        "lesson": lesson,
        "course": course,
        "questions": questions,
        "access": access,
    }

    return render(request, "tech/quiz.html", context)


@login_required
def submit_quiz(request, quiz_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    quiz = get_object_or_404(
        TechQuiz.objects.select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
        ),
        id=quiz_id,
        published=True,
        lesson__published=True,
        lesson__module__published=True,
        lesson__module__course__published=True,
    )

    course = quiz.lesson.module.course

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    if request.method != "POST":
        return redirect(
            "tech:tech_quiz",
            lesson_id=quiz.lesson.id,
        )

    questions = list(
        quiz.questions.prefetch_related("choices").order_by("order", "id")
    )

    score = 0
    total_points = 0

    for question in questions:
        total_points += question.points

        selected_choice_id = request.POST.get(f"question_{question.id}")

        if not selected_choice_id:
            continue

        correct_choice = question.choices.filter(
            id=selected_choice_id,
            is_correct=True,
        ).first()

        if correct_choice:
            score += question.points

    percentage = Decimal("0.00")

    if total_points > 0:
        percentage = (Decimal(score) / Decimal(total_points)) * Decimal("100")

    percentage = percentage.quantize(Decimal("0.01"))

    passed = percentage >= quiz.pass_mark

    attempt = TechQuizAttempt.objects.create(
        student=student,
        quiz=quiz,
        score=score,
        total_points=total_points,
        percentage=percentage,
        passed=passed,
    )

    if passed:
        enrollment, created = TechEnrollment.objects.get_or_create(
            student=student,
            course=course,
        )

        progress, _ = TechLessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=quiz.lesson,
        )

        progress.completed = True
        progress.save()

        total_lessons = TechLesson.objects.filter(
            module__course=course,
            module__published=True,
            published=True,
        ).count()

        completed_lessons = TechLessonProgress.objects.filter(
            enrollment=enrollment,
            completed=True,
            lesson__module__course=course,
            lesson__module__published=True,
            lesson__published=True,
        ).count()

        if total_lessons > 0 and completed_lessons >= total_lessons:
            enrollment.completed = True
            enrollment.save(update_fields=["completed"])

    return redirect(
        "tech:tech_quiz_result",
        attempt_id=attempt.id,
    )


@login_required
def quiz_result(request, attempt_id):
    student = student_only(request)

    if student is None:
        return redirect("student_dashboard")

    attempt = get_object_or_404(
        TechQuizAttempt.objects.select_related(
            "quiz",
            "quiz__lesson",
            "quiz__lesson__module",
            "quiz__lesson__module__course",
        ),
        id=attempt_id,
        student=student,
    )

    course = attempt.quiz.lesson.module.course

    access = _require_course_access(request, course)

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type=ContentType.TECH_COURSE,
            content_id=course.id,
        )

    context = {
        "attempt": attempt,
        "quiz": attempt.quiz,
        "lesson": attempt.quiz.lesson,
        "course": course,
        "access": access,
    }

    return render(request, "tech/quiz_result.html", context)