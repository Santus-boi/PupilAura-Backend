from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from payments.models import ContentType
from payments.services import has_access

from .models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamAttempt,
    ExamAnswer,
)


def student_only(request):
    if not request.user.is_authenticated:
        return None

    if request.user.role != "student":
        return None

    return request.user


# ==============================================================
# ACCESS HELPERS
# ==============================================================

def _has_exam_access(request, exam):
    return has_access(
        request.user,
        ContentType.EXAM,
        exam.id,
    )


def _has_resource_access(request, resource):
    return has_access(
        request.user,
        ContentType.EXAM_RESOURCE,
        resource.id,
    )


def _resource_is_free(resource):
    return resource.price is None or resource.price <= 0


def _exam_is_free(exam):
    return exam.price is None or exam.price <= 0


def _attach_resource_access(request, resources, exam_access):
    """
    Annotate each resource with:
      .has_access     → True if student can open it right now
      .is_free        → True if price is None/0
      .via_exam       → True if access comes from the exam purchase
      .via_resource   → True if access comes from a per-resource purchase
    """
    for resource in resources:
        resource.is_free = _resource_is_free(resource)

        if exam_access.has_access:
            resource.has_access = True
            resource.via_exam = True
            resource.via_resource = False
        elif resource.is_free:
            resource.has_access = True
            resource.via_exam = False
            resource.via_resource = False
        else:
            res_access = _has_resource_access(request, resource)
            resource.has_access = res_access.has_access
            resource.via_exam = False
            resource.via_resource = res_access.has_access


# ==============================================================
# EXAM PREP VIEWS
# ==============================================================

@login_required
def exam_home(request):
    student = student_only(request)

    if student is None:
        return redirect("/")

    exams = (
        Exam.objects.filter(published=True)
        .order_by("order", "name")
    )

    return render(
        request,
        "exam_prep/home.html",
        {
            "student": student,
            "exams": exams,
        },
    )


@login_required
def exam_detail(request, exam_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        published=True,
    )

    exam_access = _has_exam_access(request, exam)
    exam_free = _exam_is_free(exam)

    subjects = (
        ExamSubject.objects.filter(
            exam=exam,
            published=True,
        )
        .order_by("order", "name")
    )

    return render(
        request,
        "exam_prep/exam_detail.html",
        {
            "student": student,
            "exam": exam,
            "subjects": subjects,
            "exam_access": exam_access,
            "exam_free": exam_free,
            # Templates can show:
            # {% if exam_access.has_access %} Unlocked
            # {% elif exam_free %} Free
            # {% else %} ₦{{ exam.price }} · Unlock
        },
    )


@login_required
def subject_detail(request, subject_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    subject = get_object_or_404(
        ExamSubject.objects.select_related("exam"),
        id=subject_id,
        published=True,
    )

    exam_access = _has_exam_access(request, subject.exam)
    exam_free = _exam_is_free(subject.exam)

    years = (
        ExamYear.objects.filter(
            exam=subject.exam,
            published=True,
        )
        .order_by("-year")
    )

    return render(
        request,
        "exam_prep/subject_detail.html",
        {
            "student": student,
            "subject": subject,
            "years": years,
            "exam_access": exam_access,
            "exam_free": exam_free,
        },
    )


@login_required
def year_detail(request, subject_id, year_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    subject = get_object_or_404(
        ExamSubject.objects.select_related("exam"),
        id=subject_id,
        published=True,
    )

    year = get_object_or_404(
        ExamYear,
        id=year_id,
        exam=subject.exam,
        published=True,
    )

    exam_access = _has_exam_access(request, subject.exam)
    exam_free = _exam_is_free(subject.exam)

    resources = list(
        ExamResource.objects.filter(
            exam=subject.exam,
            subject=subject,
            year=year,
            published=True,
        )
        .order_by("order", "title")
    )

    _attach_resource_access(request, resources, exam_access)

    return render(
        request,
        "exam_prep/year_detail.html",
        {
            "student": student,
            "subject": subject,
            "year": year,
            "resources": resources,
            "exam_access": exam_access,
            "exam_free": exam_free,
        },
    )



@login_required
def resource_detail(request, resource_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
        published=True,
    )

    # ----------------------------------------------------------
    # CHECK ACCESS TO THE REQUESTED RESOURCE
    # ----------------------------------------------------------

    exam_access = _has_exam_access(request, resource.exam)
    resource_is_free = _resource_is_free(resource)

    if exam_access.has_access or resource_is_free:
        allowed = True
        resource_access = None
    else:
        resource_access = _has_resource_access(request, resource)
        allowed = resource_access.has_access

    if not allowed:
        return redirect(
            "payments:checkout",
            content_type=ContentType.EXAM_RESOURCE,
            content_id=resource.id,
        )

    # ----------------------------------------------------------
    # RELATED RESOURCES
    # ----------------------------------------------------------

    related_resources = (
        ExamResource.objects.filter(
            exam=resource.exam,
            subject=resource.subject,
            year=resource.year,
            published=True,
        )
        .order_by("order", "title")
    )

    current_view = request.GET.get("view", "overview")

    allowed_views = [
        "overview",
        "questions",
        "solutions",
        "lesson",
        "video",
        "material",
        "practical",
        "revision",
        "mock_exam",
    ]

    if current_view not in allowed_views:
        current_view = "overview"

    display_resource = resource

    # ----------------------------------------------------------
    # SELECT THE RESOURCE FOR THE REQUESTED TAB
    # ----------------------------------------------------------

    if current_view == "questions":
        selected_resource = related_resources.filter(
            resource_type="past_questions"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "solutions":
        selected_resource = related_resources.filter(
            resource_type="solutions"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "lesson":
        selected_resource = related_resources.filter(
            resource_type="lesson"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "video":
        selected_resource = (
            related_resources.exclude(video_url="")
            .filter(video_url__isnull=False)
            .first()
        )

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "material":
        selected_resource = (
            related_resources.exclude(file="")
            .filter(file__isnull=False)
            .first()
        )

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "practical":
        selected_resource = related_resources.filter(
            resource_type="practical"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "revision":
        selected_resource = related_resources.filter(
            resource_type="revision"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    elif current_view == "mock_exam":
        selected_resource = related_resources.filter(
            resource_type="mock_exam"
        ).first()

        if selected_resource:
            display_resource = selected_resource

    # ----------------------------------------------------------
    # CHECK ACCESS TO THE SELECTED RELATED RESOURCE
    # ----------------------------------------------------------

    if display_resource.id == resource.id:
        display_resource_access = resource_access

    elif exam_access.has_access or _resource_is_free(display_resource):
        display_resource_access = None

    else:
        display_resource_access = _has_resource_access(
            request,
            display_resource,
        )

        if not display_resource_access.has_access:
            return redirect(
                "payments:checkout",
                content_type=ContentType.EXAM_RESOURCE,
                content_id=display_resource.id,
            )

    # ----------------------------------------------------------
    # LOAD QUESTIONS FROM THE ACTUAL DISPLAYED RESOURCE
    # ----------------------------------------------------------

    questions = (
        display_resource.questions.filter(published=True)
        .prefetch_related("choices")
        .order_by("order", "question_number")
    )

    display_questions_exist = questions.exists()

    # Only published MCQ questions make a resource testable.
    testable = (
        display_resource.resource_type in [
            "past_questions",
            "mock_exam",
        ]
        and display_resource.questions.filter(
            published=True,
            question_type="mcq",
        ).exists()
    )

    # ----------------------------------------------------------
    # CHECK AVAILABLE CONTENT TABS
    # ----------------------------------------------------------

    has_questions = related_resources.filter(
        resource_type="past_questions"
    ).exists()

    has_solutions = related_resources.filter(
        resource_type="solutions"
    ).exists()

    has_lesson = related_resources.filter(
        resource_type="lesson"
    ).exists()

    has_practical = related_resources.filter(
        resource_type="practical"
    ).exists()

    has_revision = related_resources.filter(
        resource_type="revision"
    ).exists()

    has_mock_exam = related_resources.filter(
        resource_type="mock_exam"
    ).exists()

    has_video = (
        related_resources.exclude(video_url="")
        .filter(video_url__isnull=False)
        .exists()
    )

    has_material = (
        related_resources.exclude(file="")
        .filter(file__isnull=False)
        .exists()
    )

    # ----------------------------------------------------------
    # STUDENT AVATAR
    # ----------------------------------------------------------

    avatar_letter = (
        (student.first_name or "").strip()[:1]
        or (student.username or "").strip()[:1]
        or "S"
    ).upper()

    # ----------------------------------------------------------
    # RENDER PAGE
    # ----------------------------------------------------------

    return render(
        request,
        "exam_prep/resource_detail.html",
        {
            "student": student,
            "avatar_letter": avatar_letter,
            "resource": resource,
            "display_resource": display_resource,
            "questions": questions,
            "display_questions_exist": display_questions_exist,
            "testable": testable,
            "related_resources": related_resources,
            "current_view": current_view,
            "has_questions": has_questions,
            "has_solutions": has_solutions,
            "has_lesson": has_lesson,
            "has_practical": has_practical,
            "has_revision": has_revision,
            "has_mock_exam": has_mock_exam,
            "has_video": has_video,
            "has_material": has_material,
            "exam_access": exam_access,
            "resource_access": resource_access,
            "display_resource_access": display_resource_access,
        },
    )


@login_required
def start_test(request, resource_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    resource = get_object_or_404(
        ExamResource.objects.select_related("exam", "subject", "year"),
        id=resource_id,
        published=True,
    )

    exam_access = _has_exam_access(request, resource.exam)
    resource_is_free = _resource_is_free(resource)

    if exam_access.has_access or resource_is_free:
        allowed = True
    else:
        allowed = _has_resource_access(request, resource).has_access

    if not allowed:
        return redirect(
            "payments:checkout",
            content_type=ContentType.EXAM_RESOURCE,
            content_id=resource.id,
        )

    if resource.resource_type not in ["past_questions", "mock_exam"]:
        return redirect(
            "exam_prep:resource_detail",
            resource_id=resource.id,
        )

    questions = (
        resource.questions.filter(published=True, question_type="mcq")
        .prefetch_related("choices")
        .order_by("order", "question_number")
    )

    if not questions.exists():
        return redirect(
            "exam_prep:resource_detail",
            resource_id=resource.id,
        )

    attempt = ExamAttempt.objects.create(
        student=student,
        resource=resource,
        total_marks=sum(q.marks for q in questions),
    )

    return render(
        request,
        "exam_prep/test.html",
        {
            "student": student,
            "resource": resource,
            "attempt": attempt,
            "questions": questions,
        },
    )


@login_required
@transaction.atomic
def submit_test(request, attempt_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    attempt = get_object_or_404(
        ExamAttempt.objects.select_related(
            "resource", "resource__exam", "resource__subject", "resource__year",
        ),
        id=attempt_id,
        student=student,
    )

    exam_access = _has_exam_access(request, attempt.resource.exam)
    resource_is_free = _resource_is_free(attempt.resource)

    if exam_access.has_access or resource_is_free:
        allowed = True
    else:
        allowed = _has_resource_access(request, attempt.resource).has_access

    if not allowed:
        return redirect(
            "payments:checkout",
            content_type=ContentType.EXAM_RESOURCE,
            content_id=attempt.resource.id,
        )

    if attempt.completed:
        return redirect("exam_prep:result", attempt_id=attempt.id)

    if request.method != "POST":
        return redirect("exam_prep:start_test", resource_id=attempt.resource.id)

    questions = (
        attempt.resource.questions.filter(published=True, question_type="mcq")
        .prefetch_related("choices")
        .order_by("order", "question_number")
    )

    score = 0
    total_marks = 0

    for question in questions:
        total_marks += question.marks

        selected_choice_id = request.POST.get(f"question_{question.id}")
        selected_choice = None

        if selected_choice_id:
            selected_choice = question.choices.filter(id=selected_choice_id).first()

        is_correct = bool(selected_choice and selected_choice.is_correct)
        marks_awarded = question.marks if is_correct else 0

        if is_correct:
            score += marks_awarded

        ExamAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "selected_choice": selected_choice,
                "is_correct": is_correct,
                "marks_awarded": marks_awarded,
            },
        )

    if total_marks > 0:
        percentage = (Decimal(score) / Decimal(total_marks)) * Decimal("100")
    else:
        percentage = Decimal("0")

    percentage = percentage.quantize(Decimal("0.01"))

    attempt.score = score
    attempt.total_marks = total_marks
    attempt.percentage = percentage
    attempt.passed = percentage >= Decimal("50")
    attempt.completed = True
    attempt.submitted_at = timezone.now()

    attempt.save(
        update_fields=[
            "score", "total_marks", "percentage",
            "passed", "completed", "submitted_at",
        ]
    )

    return redirect("exam_prep:result", attempt_id=attempt.id)


@login_required
def result(request, attempt_id):
    student = student_only(request)

    if student is None:
        return redirect("/")

    attempt = get_object_or_404(
        ExamAttempt.objects.select_related(
            "resource", "resource__exam", "resource__subject", "resource__year",
        ),
        id=attempt_id,
        student=student,
    )

    if not attempt.completed:
        return redirect("exam_prep:start_test", resource_id=attempt.resource.id)

    answers = (
        attempt.answers.select_related("question", "selected_choice")
        .prefetch_related("question__choices")
        .order_by("question__order", "question__question_number")
    )

    return render(
        request,
        "exam_prep/result.html",
        {
            "student": student,
            "attempt": attempt,
            "answers": answers,
        },
    )


@login_required
def attempt_history(request):
    student = student_only(request)

    if student is None:
        return redirect("/")

    attempts = (
        ExamAttempt.objects.filter(student=student, completed=True)
        .select_related("resource", "resource__exam", "resource__subject", "resource__year")
        .order_by("-submitted_at", "-started_at")
    )

    return render(
        request,
        "exam_prep/history.html",
        {
            "student": student,
            "attempts": attempts,
        },
    )