from calendar import week
from decimal import Decimal
from django.db.models import Prefetch
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from assessments.models import Quiz, QuizAttempt
from enrollments.models import Enrollment, LessonProgress
from exam_prep.models import ExamAttempt
from learning.models import (
    EducationLevel,
    Lesson,
    LessonImage,
    LessonResource,
    LessonVideo,
    SchoolClass,
    Subject,
    Term,
    Week,
    CurriculumMaterial,
)
from payments.services import has_access
from tech.models import TechEnrollment, TechLessonProgress


# ==============================================================
# STUDENT HELPERS
# ==============================================================

def student_only(request):
    """
    Return the student's profile for an authenticated student.
    """

    if not request.user.is_authenticated:
        return None

    if request.user.role != "student":
        return None

    return getattr(
        request.user,
        "student_profile",
        None,
    )


def get_subject_lessons(subject):
    """
    Return all published lessons belonging to a school subject.

    School Curriculum:

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

    if not subject:
        return Lesson.objects.none()

    return (
        Lesson.objects
        .filter(
            week__term__subject=subject,
            published=True,
        )
        .select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
        )
        .order_by(
            "week__term__order",
            "week__number",
            "order",
            "id",
        )
    )


# ==============================================================
# SCHOOL CURRICULUM PROGRESS
# ==============================================================

def calculate_enrollment_progress(enrollment):
    """
    Calculate progress for one school-subject enrollment.
    """

    if not enrollment.subject_id:

        enrollment.total_lessons = 0
        enrollment.completed_lessons = 0
        enrollment.progress = 0
        enrollment.progress_percentage = 0
        enrollment.first_lesson = None
        enrollment.current_lesson = None
        enrollment.completed = False

        return enrollment

    lessons = get_subject_lessons(
        enrollment.subject
    )

    lesson_list = list(
        lessons
    )

    total_lessons = len(
        lesson_list
    )

    completed_lesson_ids = set(
        enrollment.lesson_progress
        .filter(
            completed=True,
            lesson__in=lesson_list,
        )
        .values_list(
            "lesson_id",
            flat=True,
        )
    )

    completed_lessons = len(
        completed_lesson_ids
    )

    if total_lessons:

        progress = round(
            (
                completed_lessons
                / total_lessons
            )
            * 100
        )

    else:

        progress = 0

    next_lesson = None

    for lesson in lesson_list:

        if lesson.id not in completed_lesson_ids:

            next_lesson = lesson

            break

    if (
        next_lesson is None
        and lesson_list
    ):

        next_lesson = lesson_list[0]

    enrollment.total_lessons = (
        total_lessons
    )

    enrollment.completed_lessons = (
        completed_lessons
    )

    enrollment.progress = (
        progress
    )

    enrollment.progress_percentage = (
        progress
    )

    enrollment.first_lesson = (
        next_lesson
    )

    enrollment.current_lesson = (
        next_lesson
    )

    enrollment.completed = (
        total_lessons > 0
        and completed_lessons >= total_lessons
    )

    enrollment.course = (
        enrollment.subject
    )

    return enrollment


# ==============================================================
# TECH ACADEMY PROGRESS
# ==============================================================

def calculate_tech_enrollment_progress(enrollment):
    """
    Calculate progress for one Tech Academy course.
    """

    modules = (
        enrollment.course.modules
        .filter(
            published=True,
        )
        .prefetch_related(
            "lessons"
        )
        .order_by(
            "order",
            "id",
        )
    )

    lesson_list = []

    for module in modules:

        for lesson in module.lessons.all():

            if lesson.published:

                lesson_list.append(
                    lesson
                )

    lesson_ids = {
        lesson.id
        for lesson in lesson_list
    }

    total_lessons = len(
        lesson_ids
    )

    completed_lesson_ids = set(
        TechLessonProgress.objects
        .filter(
            enrollment=enrollment,
            completed=True,
            lesson_id__in=lesson_ids,
        )
        .values_list(
            "lesson_id",
            flat=True,
        )
    )

    completed_lessons = len(
        completed_lesson_ids
    )

    if total_lessons:

        progress = round(
            (
                completed_lessons
                / total_lessons
            )
            * 100
        )

    else:

        progress = 0

    enrollment.total_lessons = (
        total_lessons
    )

    enrollment.completed_lessons = (
        completed_lessons
    )

    enrollment.progress = (
        progress
    )

    enrollment.progress_percentage = (
        progress
    )

    enrollment.completed = (
        total_lessons > 0
        and completed_lessons >= total_lessons
    )

    enrollment.current_lesson = None

    for lesson in lesson_list:

        if lesson.id not in completed_lesson_ids:

            enrollment.current_lesson = (
                lesson
            )

            break

    if (
        enrollment.current_lesson is None
        and lesson_list
    ):

        enrollment.current_lesson = (
            lesson_list[0]
        )

    return enrollment


# ==============================================================
# DASHBOARD
# ==============================================================

@login_required
def dashboard(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    enrollments = (
        student_profile.enrollments
        .select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        )
        .prefetch_related(
            "lesson_progress",
        )
    )

    for enrollment in enrollments:

        calculate_enrollment_progress(
            enrollment
        )

    tech_enrollments = (
        TechEnrollment.objects
        .filter(
            student=request.user,
            course__published=True,
        )
        .select_related(
            "course",
            "course__category",
        )
        .prefetch_related(
            "course__modules__lessons",
            "lesson_progress",
        )
        .order_by(
            "-enrolled_at"
        )
    )

    for enrollment in tech_enrollments:

        calculate_tech_enrollment_progress(
            enrollment
        )

    exam_attempts = (
        ExamAttempt.objects
        .filter(
            student=request.user,
            completed=True,
        )
        .select_related(
            "resource",
            "resource__exam",
            "resource__subject",
            "resource__year",
        )
        .order_by(
            "-submitted_at",
            "-started_at",
        )
    )

    recent_exam_attempts = (
        exam_attempts[:5]
    )

    exam_attempt_count = (
        exam_attempts.count()
    )

    exam_passed_count = (
        exam_attempts
        .filter(
            passed=True,
        )
        .count()
    )

    exam_failed_count = (
        exam_attempt_count
        - exam_passed_count
    )

    exam_average_result = (
        exam_attempts
        .aggregate(
            average=Avg(
                "percentage"
            )
        )["average"]
    )

    if exam_average_result is None:

        exam_average_percentage = (
            Decimal("0.00")
        )

    else:

        exam_average_percentage = (
            Decimal(
                str(
                    exam_average_result
                )
            )
            .quantize(
                Decimal("0.01")
            )
        )

    school_total_lessons = 0
    school_completed_lessons = 0

    for enrollment in enrollments:

        school_total_lessons += (
            enrollment.total_lessons
        )

        school_completed_lessons += (
            enrollment.completed_lessons
        )

    tech_total_lessons = 0
    tech_completed_lessons = 0

    for enrollment in tech_enrollments:

        tech_total_lessons += (
            enrollment.total_lessons
        )

        tech_completed_lessons += (
            enrollment.completed_lessons
        )

    total_lessons = (
        school_total_lessons
        + tech_total_lessons
    )

    completed_lessons = (
        school_completed_lessons
        + tech_completed_lessons
    )

    if total_lessons:

        overall_progress = round(
            (
                completed_lessons
                / total_lessons
            )
            * 100
        )

    else:

        overall_progress = 0

    return render(
        request,
        "student/dashboard.html",
        {
            "student": student_profile,
            "enrollments": enrollments,
            "tech_enrollments": tech_enrollments,

            "exam_attempts": recent_exam_attempts,
            "exam_attempt_count": exam_attempt_count,
            "exam_passed_count": exam_passed_count,
            "exam_failed_count": exam_failed_count,
            "exam_average_percentage": exam_average_percentage,

            "recent_exam_attempts": recent_exam_attempts,
            "exam_total_attempts": exam_attempt_count,
            "exam_passed_attempts": exam_passed_count,
            "exam_failed_attempts": exam_failed_count,
            "exam_average_result": exam_average_percentage,

            "school_total_lessons": school_total_lessons,
            "school_completed_lessons": school_completed_lessons,

            "tech_total_lessons": tech_total_lessons,
            "tech_completed_lessons": tech_completed_lessons,

            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "overall_progress": overall_progress,
        },
    )


# ==============================================================
# MY COURSES
# ==============================================================

@login_required
def my_courses(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    enrollments = (
        student_profile.enrollments
        .select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        )
        .prefetch_related(
            "lesson_progress",
        )
    )

    for enrollment in enrollments:

        calculate_enrollment_progress(
            enrollment
        )

    tech_enrollments = (
        TechEnrollment.objects
        .filter(
            student=request.user,
            course__published=True,
        )
        .select_related(
            "course",
            "course__category",
        )
        .prefetch_related(
            "course__modules__lessons",
            "lesson_progress",
        )
        .order_by(
            "-enrolled_at"
        )
    )

    for enrollment in tech_enrollments:

        calculate_tech_enrollment_progress(
            enrollment
        )

    return render(
        request,
        "student/my_courses.html",
        {
            "student": student_profile,
            "enrollments": enrollments,
            "tech_enrollments": tech_enrollments,
        },
    )


# ==============================================================
# PROGRESS
# ==============================================================

@login_required
def my_progress(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    enrollments = (
        student_profile.enrollments
        .select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        )
        .prefetch_related(
            "lesson_progress",
        )
    )

    school_total_lessons = 0
    school_completed_lessons = 0

    for enrollment in enrollments:

        calculate_enrollment_progress(
            enrollment
        )

        school_total_lessons += (
            enrollment.total_lessons
        )

        school_completed_lessons += (
            enrollment.completed_lessons
        )

    tech_enrollments = (
        TechEnrollment.objects
        .filter(
            student=request.user,
            course__published=True,
        )
        .select_related(
            "course",
            "course__category",
        )
        .prefetch_related(
            "course__modules__lessons",
            "lesson_progress",
        )
        .order_by(
            "-enrolled_at"
        )
    )

    tech_total_lessons = 0
    tech_completed_lessons = 0

    for enrollment in tech_enrollments:

        calculate_tech_enrollment_progress(
            enrollment
        )

        tech_total_lessons += (
            enrollment.total_lessons
        )

        tech_completed_lessons += (
            enrollment.completed_lessons
        )

    total_lessons = (
        school_total_lessons
        + tech_total_lessons
    )

    completed_lessons = (
        school_completed_lessons
        + tech_completed_lessons
    )

    if total_lessons:

        overall_progress = round(
            (
                completed_lessons
                / total_lessons
            )
            * 100
        )

    else:

        overall_progress = 0

    return render(
        request,
        "student/my_progress.html",
        {
            "student": student_profile,
            "enrollments": enrollments,
            "tech_enrollments": tech_enrollments,

            "school_total_lessons": school_total_lessons,
            "school_completed_lessons": school_completed_lessons,

            "tech_total_lessons": tech_total_lessons,
            "tech_completed_lessons": tech_completed_lessons,

            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "overall_progress": overall_progress,
        },
    )


# ==============================================================
# ASSESSMENTS


@login_required
def assessments(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    enrolled_subject_ids = (
        student_profile.enrollments
        .exclude(
            subject_id=None
        )
        .values_list(
            "subject_id",
            flat=True,
        )
    )

    # ----------------------------------------------------------
    # ALL SCHOOL ASSESSMENTS
    #
    # A quiz can belong to exactly one of:
    #
    #   Lesson
    #   Week
    #   Term
    # ----------------------------------------------------------

    quizzes = (
        Quiz.objects
        .filter(
            published=True,
        )
        .filter(
            Q(
                lesson__week__term__subject_id__in=(
                    enrolled_subject_ids
                )
            )
            |
            Q(
                week__term__subject_id__in=(
                    enrolled_subject_ids
                )
            )
            |
            Q(
                term__subject_id__in=(
                    enrolled_subject_ids
                )
            )
        )
        .select_related(
            # Lesson assessment
            "lesson",
            "lesson__week",
            "lesson__week__term",
            "lesson__week__term__subject",
            "lesson__week__term__subject__school_class",

            # Week assessment
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",

            # Term assessment
            "term",
            "term__subject",
            "term__subject__school_class",
            "term__subject__school_class__education_level",
        )
        .prefetch_related(
            "questions",
        )
        .distinct()
    )

    # Convert QuerySet to a list because we will attach
    # temporary display information to each Quiz object.
    quizzes = list(
        quizzes
    )

    # ----------------------------------------------------------
    # NORMALISE ASSESSMENT INFORMATION
    #
    # IMPORTANT:
    # Do NOT assign to quiz.assessment_type.
    #
    # Quiz.assessment_type is a read-only property on the
    # Quiz model.
    # ----------------------------------------------------------

    for quiz in quizzes:

        # These are temporary attributes used by the
        # student assessment page.

        quiz.assessment_subject = None
        quiz.assessment_term = None
        quiz.assessment_week = None
        quiz.assessment_lesson = None

        # ------------------------------------------------------
        # LESSON ASSESSMENT
        # ------------------------------------------------------

        if quiz.lesson_id:

            quiz.assessment_lesson = (
                quiz.lesson
            )

            quiz.assessment_week = (
                quiz.lesson.week
            )

            quiz.assessment_term = (
                quiz.lesson.week.term
            )

            quiz.assessment_subject = (
                quiz.lesson.week.term.subject
            )

        # ------------------------------------------------------
        # WEEK ASSESSMENT
        # ------------------------------------------------------

        elif quiz.week_id:

            quiz.assessment_week = (
                quiz.week
            )

            quiz.assessment_term = (
                quiz.week.term
            )

            quiz.assessment_subject = (
                quiz.week.term.subject
            )

        # ------------------------------------------------------
        # TERM ASSESSMENT
        # ------------------------------------------------------

        elif quiz.term_id:

            quiz.assessment_term = (
                quiz.term
            )

            quiz.assessment_subject = (
                quiz.term.subject
            )

    # ----------------------------------------------------------
    # STUDENT PASSED STATUS
    # ----------------------------------------------------------

    quiz_ids = [
        quiz.id
        for quiz in quizzes
    ]

    passed_quiz_ids = set()

    if quiz_ids:

        passed_quiz_ids = set(
            QuizAttempt.objects
            .filter(
                student=request.user,
                quiz_id__in=quiz_ids,
                passed=True,
            )
            .values_list(
                "quiz_id",
                flat=True,
            )
        )

    for quiz in quizzes:

        quiz.student_passed = (
            quiz.id in passed_quiz_ids
        )

    # ----------------------------------------------------------
    # SORT ASSESSMENTS
    #
    # Curriculum order:
    #
    # Subject
    #   ↓
    # Term
    #   ↓
    # Week
    #   ↓
    # Lesson / Week / Term assessment
    # ----------------------------------------------------------

    def assessment_sort_key(quiz):

        subject = (
            quiz.assessment_subject
        )

        term = (
            quiz.assessment_term
        )

        week = (
            quiz.assessment_week
        )

        lesson = (
            quiz.assessment_lesson
        )

        subject_name = (
            subject.name
            if subject
            else ""
        )

        term_order = (
            getattr(
                term,
                "order",
                0,
            )
            if term
            else 0
        )

        week_number = (
            getattr(
                week,
                "number",
                0,
            )
            if week
            else 0
        )

        lesson_order = (
            getattr(
                lesson,
                "order",
                0,
            )
            if lesson
            else 0
        )

        # Lesson assessments first
        if quiz.lesson_id:

            assessment_order = 1

        # Week assessments second
        elif quiz.week_id:

            assessment_order = 2

        # Term assessments third
        elif quiz.term_id:

            assessment_order = 3

        else:

            assessment_order = 4

        return (
            subject_name,
            term_order,
            week_number,
            assessment_order,
            lesson_order,
            quiz.id,
        )

    quizzes.sort(
        key=assessment_sort_key
    )

    return render(
        request,
        "student/assessments.html",
        {
            "student": student_profile,
            "quizzes": quizzes,
        },
    )


# ==============================================================
# ASSESSMENT RESULT
# ==============================================================

@login_required
def assessment_result(request, attempt_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    attempt = get_object_or_404(
        QuizAttempt.objects
        .select_related(
            "quiz",
            "quiz__lesson",
            "quiz__week",
            "quiz__term",
        )
        .prefetch_related(
            "answers__question",
            "answers__selected_choice",
        ),
        id=attempt_id,
        student=request.user,
    )

    answers = list(
        attempt.answers.all()
    )

    has_pending_review = any(
        answer.question.question_type
        in [
            answer.question.QuestionType.THEORY,
            answer.question.QuestionType.PRACTICAL,
        ]
        and not answer.reviewed
        for answer in answers
    )

    all_reviewed = not has_pending_review

    return render(
        request,
        "student/assessment_result.html",
        {
            "student": student_profile,
            "attempt": attempt,
            "quiz": attempt.quiz,
            "answers": answers,
            "has_pending_review": has_pending_review,
            "all_reviewed": all_reviewed,
        },
    )


# ==============================================================
# CERTIFICATES
# ==============================================================

@login_required
def certificates(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    return render(
        request,
        "student/certificates.html",
        {
            "student": student_profile,
        },
    )


# ==============================================================
# PROFILE
# ==============================================================

@login_required
def profile(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    education_levels = (
        EducationLevel.objects
        .all()
        .order_by(
            "order",
            "name",
        )
    )

    school_classes = (
        SchoolClass.objects
        .select_related(
            "education_level"
        )
        .all()
        .order_by(
            "education_level__order",
            "order",
            "name",
        )
    )

    if request.method == "POST":

        curriculum_level_id = request.POST.get(
            "curriculum_level"
        )

        school_class_id = request.POST.get(
            "school_class"
        )

        school_name = request.POST.get(
            "school",
            "",
        ).strip()

        curriculum_level = None

        if curriculum_level_id:

            curriculum_level = get_object_or_404(
                EducationLevel,
                id=curriculum_level_id,
            )

        selected_class = None

        if school_class_id:

            selected_class = get_object_or_404(
                SchoolClass.objects.select_related(
                    "education_level"
                ),
                id=school_class_id,
            )

            if (
                curriculum_level
                and selected_class.education_level_id
                != curriculum_level.id
            ):

                return render(
                    request,
                    "student/profile.html",
                    {
                        "student": student_profile,
                        "education_levels": education_levels,
                        "school_classes": school_classes,
                        "error_message": (
                            "The selected school class does not "
                            "belong to the selected education level."
                        ),
                    },
                )

        student_profile.curriculum_level = (
            curriculum_level
        )

        student_profile.school_class = (
            selected_class
        )

        student_profile.education_level = (
            curriculum_level.name
            if curriculum_level
            else ""
        )

        student_profile.class_name = (
            selected_class.name
            if selected_class
            else ""
        )

        student_profile.school = (
            school_name
        )

        student_profile.save()

        return render(
            request,
            "student/profile.html",
            {
                "student": student_profile,
                "education_levels": education_levels,
                "school_classes": school_classes,
                "success_message": (
                    "Your profile has been updated successfully!"
                ),
            },
        )

    return render(
        request,
        "student/profile.html",
        {
            "student": student_profile,
            "education_levels": education_levels,
            "school_classes": school_classes,
        },
    )


# ==============================================================
# SETTINGS
# ==============================================================

@login_required
def settings(request):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    return render(
        request,
        "student/settings.html",
        {
            "student": student_profile,
        },
    )


# ==============================================================
# CURRICULUM — CLASSES
# ==============================================================
@login_required
def classes(request):
    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    education_levels = (
        EducationLevel.objects
        .filter(classes__isnull=False)
        .distinct()
        .prefetch_related(
            Prefetch(
                "classes",
                queryset=SchoolClass.objects.order_by("order", "name"),
            )
        )
        .order_by("order", "name")
    )

    return render(request, "student/classes.html", {
        "student": student_profile,
        "education_levels": education_levels,
    })

# ==============================================================
# CURRICULUM — SUBJECTS
# ==============================================================


@login_required
def subjects(request, class_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    school_class = get_object_or_404(
        SchoolClass.objects.select_related(
            "education_level"
        ),
        id=class_id,
    )

    # ----------------------------------------------------------
    # SHOW ALL SUBJECTS
    #
    # Students can explore any available class without
    # completing or updating their profile.
    #
    # Paid subjects still require valid access/payment.
    # Free and previously purchased subjects remain accessible.
    # ----------------------------------------------------------

    subjects = list(
        Subject.objects
        .filter(
            school_class=school_class,
        )
        .order_by(
            "name"
        )
    )

    for subject in subjects:

        access = has_access(
            request.user,
            "subject",
            subject.id,
        )

        subject.has_access = (
            access.has_access
        )

        subject.days_remaining = (
            access.days_remaining
        )

        subject.is_free = (
            subject.price is None
            or subject.price <= 0
        )

    return render(
        request,
        "student/subjects.html",
        {
            "student": student_profile,
            "school_class": school_class,
            "subjects": subjects,
        },
    )

# ==============================================================
# CURRICULUM — START SUBJECT
# ==============================================================
#
# Entry point for any subject click.
#
# If the student has access (free or paid or promo token),
# ensure an Enrollment exists, then go to the terms list.
#
# If the student has no access, redirect to the payment
# checkout so they can buy or redeem a promo token.
#
# ==============================================================

@login_required
def start_subject(request, subject_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    subject = get_object_or_404(
        Subject.objects.select_related(
            "school_class",
        ),
        id=subject_id,
    )

    # ----------------------------------------------------------
    # VERIFY SUBJECT ACCESS
    #
    # Students can start subjects from any available class.
    # Profile class selection is not required.
    # Paid subjects still require valid payment/access.
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        subject.id,
    )

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=subject.id,
        )

    # ----------------------------------------------------------
    # CREATE OR RETRIEVE ENROLLMENT
    # ----------------------------------------------------------

    Enrollment.objects.get_or_create(
        student=student_profile,
        subject=subject,
    )

    return redirect(
        "student_terms",
        subject_id=subject.id,
    )

# ==============================================================
# CURRICULUM — TERMS
# ==============================================================

@login_required
def terms(request, subject_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    subject = get_object_or_404(
        Subject.objects.select_related(
            "school_class",
            "school_class__education_level",
        ),
        id=subject_id,
    )

    # ----------------------------------------------------------
    # CHECK PURCHASE ACCESS
    #
    # Free subjects and active purchases pass through.
    # Expired purchases must be renewed through checkout.
    # Students do not need a saved profile class.
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        subject.id,
    )

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=subject.id,
        )

    # ----------------------------------------------------------
    # ENSURE ENROLLMENT EXISTS
    # ----------------------------------------------------------

    Enrollment.objects.get_or_create(
        student=student_profile,
        subject=subject,
    )

    terms = list(
        subject.terms
        .all()
        .order_by("order")
    )

    # ----------------------------------------------------------
    # ATTACH TERM ASSESSMENT
    # ----------------------------------------------------------

    for term in terms:

        term.term_quiz = (
            Quiz.objects
            .filter(
                term=term,
                published=True,
            )
            .first()
        )

        term.has_assessment = (
            term.term_quiz is not None
        )

    return render(
        request,
        "student/terms.html",
        {
            "student": student_profile,
            "subject": subject,
            "terms": terms,
            "access": access,
        },
    )

# ==============================================================
# CURRICULUM — WEEKS
# ==============================================================

@login_required
def weeks(request, term_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    term = get_object_or_404(
        Term.objects.select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        ),
        id=term_id,
        subject__enrollments__student=student_profile,
    )

    # ----------------------------------------------------------
    # CHECK PURCHASE ACCESS
    #
    # Students can access enrolled subjects from any class.
    # Profile class selection is not required.
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        term.subject_id,
    )

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=term.subject_id,
        )

    weeks = list(
        term.weeks
        .all()
        .order_by(
            "number",
            "id",
        )
    )

    # ----------------------------------------------------------
    # TERM ASSESSMENT
    # ----------------------------------------------------------

    term.term_quiz = (
        Quiz.objects
        .filter(
            term=term,
            published=True,
        )
        .first()
    )

    # ----------------------------------------------------------
    # WEEK CONTENT + WEEK ASSESSMENTS
    # ----------------------------------------------------------

    for week in weeks:

        week.published_lessons = list(
            week.lessons
            .filter(
                published=True,
            )
            .order_by(
                "order",
                "id",
            )
        )

        week.week_quiz = (
            Quiz.objects
            .filter(
                week=week,
                published=True,
            )
            .first()
        )

        week.has_assessment = (
            week.week_quiz is not None
        )

    return render(
        request,
        "student/weeks.html",
        {
            "student": student_profile,
            "term": term,
            "weeks": weeks,
            "access": access,
        },
    )


# ==============================================================
# CURRICULUM — LESSONS
# ==============================================================

@login_required
def lessons(request, week_id):

    student_profile = student_only(request)

    if student_profile is None:
        return redirect("/")

    week = get_object_or_404(
        Week.objects.select_related(
            "term",
            "term__subject",
            "term__subject__school_class",
            "term__subject__school_class__education_level",
        ),
        id=week_id,
        term__subject__enrollments__student=student_profile,
    )

    # ----------------------------------------------------------
    # CHECK PURCHASE ACCESS
    #
    # Students can access enrolled subjects from any class.
    # Profile class selection is not required.
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        week.term.subject_id,
    )

    if not access.has_access:
        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=week.term.subject_id,
        )

    # ----------------------------------------------------------
    # GET STUDENT ENROLLMENT
    # ----------------------------------------------------------

    enrollment = get_object_or_404(
        student_profile.enrollments,
        subject=week.term.subject,
    )

    lessons = list(
        week.lessons
        .filter(
            published=True,
        )
        .select_related(
            "week",
            "week__term",
            "week__term__subject",
        )
        .prefetch_related(
            "videos",
            "images",
            "resources",
            "quizzes",
        )
        .order_by(
            "order",
            "id",
        )
    )

    # ----------------------------------------------------------
    # LESSON COMPLETION
    # ----------------------------------------------------------

    completed_lesson_ids = set(
        enrollment.lesson_progress
        .filter(
            completed=True,
            lesson__in=lessons,
        )
        .values_list(
            "lesson_id",
            flat=True,
        )
    )

    for lesson in lessons:

        lesson.is_completed = (
            lesson.id in completed_lesson_ids
        )

        lesson.status = (
            "completed"
            if lesson.is_completed
            else "not_started"
        )

        lesson.published_videos = [
            video
            for video in lesson.videos.all()
            if video.published
        ]

        lesson.published_images = [
            image
            for image in lesson.images.all()
            if image.published
        ]

        lesson.published_resources = [
            resource
            for resource in lesson.resources.all()
            if resource.published
        ]

        lesson.published_quizzes = [
            quiz
            for quiz in lesson.quizzes.all()
            if quiz.published
        ]

        lesson.has_videos = bool(
            lesson.published_videos
        )

        lesson.has_images = bool(
            lesson.published_images
        )

        lesson.has_resources = bool(
            lesson.published_resources
        )

        lesson.has_assessment = bool(
            lesson.published_quizzes
        )

        lesson.has_practical = bool(
            lesson.practical
        )

    # ----------------------------------------------------------
    # WEEK PROGRESS
    # ----------------------------------------------------------

    total_lessons = len(lessons)

    completed_lessons = len(
        completed_lesson_ids
    )

    if total_lessons:
        week_progress = round(
            (completed_lessons / total_lessons) * 100
        )
    else:
        week_progress = 0

    # ----------------------------------------------------------
    # CURRENT LESSON
    # ----------------------------------------------------------

    current_lesson = None

    for lesson in lessons:

        if not lesson.is_completed:
            current_lesson = lesson
            break

    if current_lesson is None and lessons:
        current_lesson = lessons[-1]

    return render(
        request,
        "student/lessons.html",
        {
            "student": student_profile,
            "week": week,
            "lessons": lessons,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "week_progress": week_progress,
            "current_lesson": current_lesson,
            "enrollment": enrollment,
            "access": access,
        },
    )

# ==============================================================
# LESSON DETAIL
# ==============================================================

@login_required
def lesson_detail(request, lesson_id):

    student_profile = student_only(
        request
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
        )
        .prefetch_related(
            "videos",
            "images",
            "resources",
            "quizzes",
        ),
        id=lesson_id,
        week__term__subject__enrollments__student=student_profile,
        published=True,
    )

    week = lesson.week
    term = week.term
    subject = term.subject
    school_class = subject.school_class
    # -----------------------------------------------------
    # PUBLISHED WEEK / TERM STUDY MATERIALS
    # ------------------------------------------------------

    week_material = (
        CurriculumMaterial.objects
        .filter(
            week=week,
            published=True,
        )
        .first()
    )

    term_material = (
        CurriculumMaterial.objects
        .filter(
            term=term,
            published=True,
        )
        .first()
    )

    if (
        student_profile.school_class_id
        and school_class
        and school_class.id
        != student_profile.school_class_id
    ):

        return redirect(
            "student_classes"
        )

        # ----------------------------------------------------------
    # CHECK PURCHASE ACCESS
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        subject.id,
    )

    if not access.has_access:

        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=subject.id,
        )

    enrollment = get_object_or_404(
        student_profile.enrollments,
        subject=subject,
    )

    calculate_enrollment_progress(
        enrollment
    )

    progress = (
        enrollment.lesson_progress
        .filter(
            lesson=lesson,
        )
        .first()
    )

    lesson_completed = (
        progress is not None
        and progress.completed
    )

    # ----------------------------------------------------------
    # PUBLISHED LESSON CONTENT
    # ----------------------------------------------------------

    published_videos = [
        video
        for video in lesson.videos.all()
        if video.published
    ]

    published_images = [
        image
        for image in lesson.images.all()
        if image.published
    ]

    published_resources = [
        resource
        for resource in lesson.resources.all()
        if resource.published
    ]

    published_quizzes = [
        quiz
        for quiz in lesson.quizzes.all()
        if quiz.published
    ]

    quiz = (
        published_quizzes[0]
        if published_quizzes
        else None
    )

    quiz_passed = False

    if quiz is not None:

        quiz_passed = (
            QuizAttempt.objects
            .filter(
                student=request.user,
                quiz=quiz,
                passed=True,
            )
            .exists()
        )

    # ----------------------------------------------------------
    # CONTENT AVAILABILITY
    # ----------------------------------------------------------

    has_videos = bool(
        published_videos
    )

    has_images = bool(
        published_images
    )

    has_practical = bool(
        lesson.practical
    )

    has_assessment = (
        quiz is not None
    )

    has_resources = bool(
        published_resources
    )

    has_objectives = bool(
        lesson.objectives
    )

    has_examples = bool(
        lesson.examples
    )

    has_key_points = bool(
        lesson.key_points
    )

    has_activity = bool(
        lesson.activity
    )

    has_lesson_content = bool(
        lesson.content
    )

    # ----------------------------------------------------------
    # PREVIOUS / NEXT LESSON
    # ----------------------------------------------------------

    week_lessons = list(
        Lesson.objects
        .filter(
            week=week,
            published=True,
        )
        .order_by(
            "order",
            "id",
        )
    )

    previous_lesson = None
    next_lesson = None
    current_index = None

    for index, week_lesson in enumerate(
        week_lessons
    ):

        if week_lesson.id == lesson.id:

            current_index = index

            break

    if current_index is not None:

        if current_index > 0:

            previous_lesson = (
                week_lessons[
                    current_index - 1
                ]
            )

        if current_index < (
            len(week_lessons) - 1
        ):

            next_lesson = (
                week_lessons[
                    current_index + 1
                ]
            )

    return render(
        request,
        "student/lesson_detail.html",
        {
            "student": student_profile,

            "lesson": lesson,

            "school_class": school_class,

            "subject": subject,

            "term": term,

            "week": week,

            "enrollment": enrollment,

            "progress": progress,

            "lesson_completed": lesson_completed,

            "quiz": quiz,
            "quiz_passed": quiz_passed,

            "published_videos": published_videos,
            "published_images": published_images,
            "published_resources": published_resources,

            "has_videos": has_videos,
            "has_images": has_images,
            "has_practical": has_practical,
            "has_assessment": has_assessment,
            "has_resources": has_resources,

            "has_objectives": has_objectives,
            "has_examples": has_examples,
            "has_key_points": has_key_points,
            "has_activity": has_activity,
            "has_lesson_content": has_lesson_content,

            "previous_lesson": previous_lesson,
            "next_lesson": next_lesson,

            "access": access,
            "week_material": week_material,
            "term_material": term_material,
        },
    )


# ==============================================================
# COMPLETE LESSON
# ==============================================================

@login_required
def complete_lesson(request, lesson_id):

    student_profile = student_only(
        request
    )

    if student_profile is None:
        return redirect("/")

    if request.method != "POST":

        return redirect(
            "student_lesson_detail",
            lesson_id=lesson_id,
        )

    lesson = get_object_or_404(
        Lesson.objects.select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
        ),
        id=lesson_id,
        week__term__subject__enrollments__student=student_profile,
        published=True,
    )

    if (
        student_profile.school_class_id
        and lesson.week.term.subject.school_class_id
        != student_profile.school_class_id
    ):

        return redirect(
            "student_classes"
        )

    # ----------------------------------------------------------
    # CHECK PURCHASE ACCESS
    # ----------------------------------------------------------

    access = has_access(
        request.user,
        "subject",
        lesson.week.term.subject_id,
    )

    if not access.has_access:

        return redirect(
            "payments:checkout",
            content_type="subject",
            content_id=lesson.week.term.subject_id,
        )

    enrollment = get_object_or_404(
        student_profile.enrollments,
        subject=lesson.week.term.subject,
    )

    quiz = (
        lesson.quizzes
        .filter(
            published=True,
        )
        .first()
    )

    if quiz is not None:

        quiz_passed = (
            QuizAttempt.objects
            .filter(
                student=request.user,
                quiz=quiz,
                passed=True,
            )
            .exists()
        )

        if not quiz_passed:

            messages.warning(
                request,
                (
                    "Please complete and pass the quiz "
                    "before marking this lesson as completed."
                ),
            )

            return redirect(
                "student_lesson_detail",
                lesson_id=lesson.id,
            )

    progress, created = (
        LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )
    )

    progress.completed = True

    progress.completed_at = (
        timezone.now()
    )

    progress.save(
        update_fields=[
            "completed",
            "completed_at",
        ]
    )

    calculate_enrollment_progress(
        enrollment
    )

    enrollment.save(
        update_fields=[
            "completed",
        ]
    )

    messages.success(
        request,
        f'"{lesson.title}" has been marked as completed.',
    )

    return redirect(
        "student_lesson_detail",
        lesson_id=lesson.id,
    )


# ==============================================================
# HOME
# ==============================================================

def home(request):

    return render(
        request,
        "home.html",
    )