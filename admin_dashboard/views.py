from django.contrib import messages
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import StudentProfile, User
from enrollments.models import Enrollment
from assessments.models import (Answer, Question, Quiz, QuizAttempt,
)

from learning.models import (Course, EducationLevel, Lesson, LessonImage, CurriculumMaterial,
    LessonResource, LessonVideo, SchoolClass, Subject, Term, Week, 
)

from tech.models import (
    TechCategory,
    TechCourse,
    TechModule,
    TechLesson,
    TechLessonVideo,
    TechLessonImage,
    TechLessonResource,
    
)
from exam_prep.models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamQuestion,
    ExamChoice,
)

from play_learn.models import (
    PlayGame,
    GameAttempt,
    Story,
    StoryChapter,
    StoryBookmark,
    CartoonStory,
    CartoonStoryScene,
    CartoonStoryQuestion,
    CartoonStoryAnswer,
)

from .forms import (
    CourseForm,
    EducationLevelForm,
    LessonForm,
    LessonImageForm,
    LessonResourceForm,
    CurriculumMaterialForm,
    LessonVideoForm,
    SchoolClassForm,
    SubjectForm,
    TermForm,
    TechCategoryForm,
    TechCourseForm,
    TechModuleForm,
    TechLessonForm,
    TechLessonVideoForm,
    TechLessonImageForm,
    TechLessonResourceForm,
    ExamForm,
    ExamSubjectForm,
    ExamYearForm,
    ExamResourceForm,
    ExamQuestionForm,
    ExamChoiceForm,
    WeekForm,
    ExamResourceForm,
    ExamLessonContentForm,
    ExamPracticalContentForm,
    ExamRevisionContentForm,
    ExamMockExamContentForm,
    PlayGameForm,
)

# ============================================================
# ADMIN ACCESS
# ============================================================
def admin_required(view_func):
    """
    Allow only authenticated users who are:
    - assigned the ADMIN role, or
    - staff, or
    - superusers.
    """

    @login_required
    def wrapped_view(request, *args, **kwargs):
        user = request.user

        if (
            getattr(user, "role", None) == User.Role.ADMIN
            or user.is_staff
            or user.is_superuser
        ):
            return view_func(request, *args, **kwargs)

        messages.error(
            request,
            "You do not have permission to access the PupilAura Admin Dashboard.",
        )

        return render(
            request,
            "admin_dashboard/access_denied.html",
            status=403,
        )

    return wrapped_view

# ============================================================
# DASHBOARD
# ============================================================
@admin_required
def dashboard(request):
    student_count = User.objects.filter(
        role=User.Role.STUDENT
    ).count()

    education_level_count = EducationLevel.objects.count()
    school_class_count = SchoolClass.objects.count()
    subject_count = Subject.objects.count()
    term_count = Term.objects.count()
    week_count = Week.objects.count()
    lesson_count = Lesson.objects.count()
    course_count = Course.objects.count()

    quiz_count = Quiz.objects.count()
    question_count = Question.objects.count()
    attempt_count = QuizAttempt.objects.count()

    pending_review_count = (
        Answer.objects
        .filter(reviewed=False)
        .exclude(question__question_type="objective")
        .count()
    )

    # ---- vars the dashboard template actually reads ----
    total_students = student_count
    total_assessments = attempt_count
    pending_reviews = pending_review_count
    passed_attempts = (
        QuizAttempt.objects
        .filter(passed=True)
        .count()
    )

    context = {
        "student_count": student_count,
        "education_level_count": education_level_count,
        "school_class_count": school_class_count,
        "subject_count": subject_count,
        "term_count": term_count,
        "week_count": week_count,
        "lesson_count": lesson_count,
        "course_count": course_count,
        "quiz_count": quiz_count,
        "question_count": question_count,
        "attempt_count": attempt_count,
        "pending_review_count": pending_review_count,

        # Added — aliases for the dashboard template
        "total_students": total_students,
        "total_assessments": total_assessments,
        "pending_reviews": pending_reviews,
        "passed_attempts": passed_attempts,
    }

    return render(
        request,
        "admin_dashboard/dashboard.html",
        context,
    )
# ============================================================
# STUDENTS
# ============================================================
@admin_required
def students(request):
    students_qs = (
        User.objects
        .filter(role=User.Role.STUDENT)
        .select_related("student_profile")
        .order_by("first_name", "last_name", "email")
    )

    context = {
        "students": students_qs,
        "student_count": students_qs.count(),

        # For the stats grid
        "total_students": students_qs.count(),
        "active_students": students_qs.filter(is_active=True).count(),
        "inactive_students": students_qs.filter(is_active=False).count(),

        # For base.html sidebar highlight
        "nav_active": "students",
    }

    return render(request, "admin_dashboard/students.html", context)

@admin_required
def student_detail(request, student_id):
    student = get_object_or_404(
        User.objects.select_related("student_profile"),
        id=student_id,
        role=User.Role.STUDENT,
    )

    profile = getattr(student, "student_profile", None)

    # Student enrollments
    enrollments = Enrollment.objects.none()

    if profile:
        enrollments = (
            Enrollment.objects
            .filter(student=profile)
            .select_related("subject")
            .annotate(
                total_lessons=Count(
                    "lesson_progress",
                    distinct=True,
                ),
                completed_lessons=Count(
                    "lesson_progress",
                    filter=Q(lesson_progress__completed=True),
                    distinct=True,
                ),
            )
            .order_by("-enrolled_at")
        )

    # Assessment attempts
    attempts = (
        QuizAttempt.objects
        .filter(student=student)



        .select_related("quiz")
        .order_by("-started_at")
    )

    # Attempts containing unreviewed theory or practical answers
    pending_reviews = (
        QuizAttempt.objects
        .filter(
            student=student,
            answers__question__question_type__in=[
                Question.QuestionType.THEORY,
                Question.QuestionType.PRACTICAL,
            ],
            answers__reviewed=False,
        )
        .distinct()
        .count()
    )

    enrollment_count = enrollments.count()
    assessment_count = attempts.count()

    completed_lessons_count = sum(
        enrollment.completed_lessons
        for enrollment in enrollments
    )

    context = {
        "student": student,
        "profile": profile,
        "enrollments": enrollments,
        "enrollment_count": enrollment_count,
        "attempts": attempts,
        "assessment_count": assessment_count,
        "completed_lessons_count": completed_lessons_count,
        "pending_reviews": pending_reviews,
    }

    return render(
        request,
        "admin_dashboard/student_detail.html",
        context,
    )

#===========================================================
# CURRICULUM OVERVIEW
# ============================================================
@admin_required
def curriculum(request):
    education_levels = (
        EducationLevel.objects
        .annotate(
            class_count=Count("classes"),
            subject_count=Count("classes__subjects"),
            lesson_count=Count(
                "classes__subjects__terms__weeks__lessons"
            ),
        )
        .order_by(
            "order",
            "name",
        )
    )

    total_education_levels = EducationLevel.objects.count()
    total_school_classes = SchoolClass.objects.count()
    total_subjects = Subject.objects.count()
    total_terms = Term.objects.count()
    total_weeks = Week.objects.count()
    total_lessons = Lesson.objects.count()

    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(
        published=True
    ).count()

    context = {
        "education_levels": education_levels,
        "total_education_levels": total_education_levels,
        "total_school_classes": total_school_classes,
        "total_subjects": total_subjects,
        "total_terms": total_terms,
        "total_weeks": total_weeks,
        "total_lessons": total_lessons,
        "total_courses": total_courses,
        "published_courses": published_courses,
    }

    return render(
        request,
        "admin_dashboard/curriculum.html",
        context,
    )

# ============================================================
# EDUCATION LEVELS
# ============================================================
@admin_required
def education_levels(request):
    education_levels = (
        EducationLevel.objects
        .annotate(
            class_count=Count("classes"),
            subject_count=Count("classes__subjects"),
            lesson_count=Count(
                "classes__subjects__terms__weeks__lessons"
            ),
        )
        .order_by(
            "order",
            "name",
        )
    )

    total_levels = EducationLevel.objects.count()
    total_classes = SchoolClass.objects.count()
    total_subjects = Subject.objects.count()
    total_lessons = Lesson.objects.count()

    context = {
        "education_levels": education_levels,
        "total_levels": total_levels,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_lessons": total_lessons,

        # Compatibility with existing template.
        "total_education_levels": total_levels,
        "total_school_classes": total_classes,
    }

    return render(
        request,
        "admin_dashboard/education_levels.html",
        context,
    )

@admin_required
def education_level_create(request):
    if request.method == "POST":
        form = EducationLevelForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Education level created successfully.",
            )

            return redirect(
                "admin_dashboard:education_levels"
            )
    else:
        form = EducationLevelForm()

    return render(
        request,
        "admin_dashboard/education_level_form.html",
        {
            "form": form,
            "title": "Create Education Level",
        },
    )

@login_required
def education_level_detail(request, level_id):
    level = get_object_or_404(
        EducationLevel,
        id=level_id,
    )

    school_classes = (
        level.classes
        .all()
        .annotate(
            subject_count=Count("subjects"),
        )
        .order_by(
            "order",
            "name",
        )
    )

    total_classes = school_classes.count()

    total_subjects = Subject.objects.filter(
        school_class__education_level=level
    ).count()

    total_lessons = Lesson.objects.filter(
        week__term__subject__school_class__education_level=level
    ).count()

    context = {
        "education_level": level,
        "school_classes": school_classes,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_lessons": total_lessons,
    }

    return render(
        request,
        "admin_dashboard/education_level_detail.html",
        context,
    )

@admin_required
def education_level_edit(request, level_id):
    level = get_object_or_404(
        EducationLevel,
        id=level_id,
    )

    if request.method == "POST":
        form = EducationLevelForm(
            request.POST,
            instance=level,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Education level updated successfully.",
            )

            return redirect(
                "admin_dashboard:education_levels"
            )
    else:
        form = EducationLevelForm(
            instance=level
        )

    return render(
        request,
        "admin_dashboard/education_level_form.html",
        {
            "form": form,
            "education_level": level,
            "title": "Edit Education Level",
        },
    )

@admin_required
def education_level_delete(request, level_id):
    education_level = get_object_or_404(
        EducationLevel,
        id=level_id,
    )

    if request.method == "POST":
        class_count = SchoolClass.objects.filter(
            education_level=education_level
        ).count()

        if class_count > 0:
            messages.error(
                request,
                (
                    "This education level cannot be deleted because "
                    f"it still contains {class_count} school class(es). "
                    "Delete or move those classes first."
                ),
            )

            return redirect(
                "admin_dashboard:education_levels"
            )

        try:
            education_level.delete()

            messages.success(
                request,
                "Education level deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This education level cannot be deleted because it is still in use.",
            )

    return redirect(
        "admin_dashboard:education_levels"
    )

# ============================================================
# SCHOOL CLASSES
# ============================================================
@admin_required
def school_classes(request):
    school_classes = (
        SchoolClass.objects
        .select_related(
            "education_level",
        )
        .annotate(
            subject_count=Count(
                "subjects",
                distinct=True,
            ),
            lesson_count=Count(
                "subjects__terms__weeks__lessons",
                distinct=True,
            ),
        )
        .order_by(
            "education_level__order",
            "order",
            "name",
        )
    )

    context = {
        "school_classes": school_classes,

        "total_school_classes": SchoolClass.objects.count(),
        "total_education_levels": EducationLevel.objects.count(),
        "total_subjects": Subject.objects.count(),
        "total_lessons": Lesson.objects.count(),
    }

    return render(
        request,
        "admin_dashboard/school_classes.html",
        context,
    )

@admin_required
def school_class_create(request):
    education_level_id = (
        request.GET.get("education_level")
        or request.POST.get("education_level")
    )

    if request.method == "POST":
        form = SchoolClassForm(request.POST)

        if form.is_valid():
            school_class = form.save()

            messages.success(
                request,
                f"School class '{school_class.name}' was created successfully.",
            )

            return redirect(
                "admin_dashboard:school_class_detail",
                class_id=school_class.pk,
            )

    else:
        initial = {}

        if education_level_id:
            initial["education_level"] = education_level_id

        form = SchoolClassForm(initial=initial)

    return render(
        request,
        "admin_dashboard/school_class_form.html",
        {
            "form": form,
            "edit_mode": False,
        },
    )

@admin_required
def school_class_edit(request, class_id):
    school_class = get_object_or_404(
        SchoolClass.objects.select_related("education_level"),
        pk=class_id,
    )

    if request.method == "POST":
        form = SchoolClassForm(
            request.POST,
            instance=school_class,
        )

        if form.is_valid():
            school_class = form.save()

            messages.success(
                request,
                f"School class '{school_class.name}' was updated successfully.",
            )

            return redirect(
                "admin_dashboard:school_class_detail",
                class_id=school_class.pk,
            )

    else:
        form = SchoolClassForm(instance=school_class)

    return render(
        request,
        "admin_dashboard/school_class_form.html",
        {
            "form": form,
            "school_class": school_class,
            "edit_mode": True,
        },
    )

@admin_required
def school_class_detail(request, class_id):
    school_class = get_object_or_404(
        SchoolClass.objects.select_related(
            "education_level"
        ),
        id=class_id,
    )

    subjects = (
        school_class.subjects
        .all()
        .order_by("name")
    )

    return render(
        request,
        "admin_dashboard/school_class_detail.html",
        {
            "school_class": school_class,
            "subjects": subjects,
        },
    )

@admin_required
def school_class_delete(request, class_id):
    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
    )

    if request.method == "POST":
        subject_count = Subject.objects.filter(
            school_class=school_class
        ).count()

        if subject_count > 0:
            messages.error(
                request,
                (
                    "This school class cannot be deleted because "
                    f"it still contains {subject_count} subject(s). "
                    "Delete those subjects first."
                ),
            )

            return redirect(
                "admin_dashboard:school_classes"
            )

        try:
            school_class.delete()

            messages.success(
                request,
                "School class deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This school class cannot be deleted because it is still in use.",
            )

    return redirect(
        "admin_dashboard:school_classes"
    )

# ============================================================
# SUBJECTS
# ============================================================
@admin_required
def subjects(request):
    subject_list = (
        Subject.objects
        .select_related(
            "school_class",
            "school_class__education_level",
        )
        .annotate(
            term_count=Count(
                "terms",
                distinct=True,
            ),
            week_count=Count(
                "terms__weeks",
                distinct=True,
            ),
            lesson_count=Count(
                "terms__weeks__lessons",
                distinct=True,
            ),
        )
        .order_by(
            "school_class__education_level__order",
            "school_class__order",
            "name",
        )
    )

    context = {
        "subjects": subject_list,
        "subject_count": Subject.objects.count(),
        "total_subjects": Subject.objects.count(),
        "total_terms": Term.objects.count(),
        "total_weeks": Week.objects.count(),
        "total_lessons": Lesson.objects.count(),
    }

    return render(
        request,
        "admin_dashboard/subjects.html",
        context,
    )

@admin_required
def subject_create(request):
    school_class_id = request.GET.get("school_class") or request.POST.get("school_class")

    if request.method == "POST":
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject = form.save()

            messages.success(
                request,
                f"Subject '{subject.name}' was created successfully.",
            )

            return redirect(
                "admin_dashboard:subject_detail",
                subject_id=subject.pk,
            )

    else:
        initial = {}

        if school_class_id:
            initial["school_class"] = school_class_id

        form = SubjectForm(initial=initial)

    return render(
        request,
        "admin_dashboard/subject_form.html",
        {
            "form": form,
            "edit_mode": False,
        },
    )

@admin_required
def subject_detail(request, subject_id):
    subject = get_object_or_404(
        Subject.objects.select_related(
            "school_class",
            "school_class__education_level",
        ),
        id=subject_id,
    )

    terms = (
        subject.terms
        .all()
        .order_by(
            "order",
            "term_type",
        )
    )

    return render(
        request,
        "admin_dashboard/subject_detail.html",
        {
            "subject": subject,
            "terms": terms,
        },
    )

@admin_required
def subject_edit(request, subject_id):
    subject = get_object_or_404(
        Subject.objects.select_related(
            "school_class",
            "school_class__education_level",
        ),
        pk=subject_id,
    )

    if request.method == "POST":
        form = SubjectForm(
            request.POST,
            instance=subject,
        )

        if form.is_valid():
            subject = form.save()

            messages.success(
                request,
                f"Subject '{subject.name}' was updated successfully.",
            )

            return redirect(
                "admin_dashboard:subject_detail",
                subject_id=subject.pk,
            )

    else:
        form = SubjectForm(instance=subject)

    return render(
        request,
        "admin_dashboard/subject_form.html",
        {
            "form": form,
            "subject": subject,
            "edit_mode": True,
        },
    )


@admin_required
def subject_delete(request, subject_id):
    subject = get_object_or_404(
        Subject,
        id=subject_id,
    )

    if request.method == "POST":
        term_count = Term.objects.filter(
            subject=subject
        ).count()

        if term_count > 0:
            messages.error(
                request,
                (
                    "This subject cannot be deleted because "
                    f"it still contains {term_count} term(s). "
                    "Delete those terms first."
                ),
            )

            return redirect(
                "admin_dashboard:subject_detail",
                subject_id=subject.id,
            )

        try:
            subject.delete()

            messages.success(
                request,
                "Subject deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This subject cannot be deleted because it is still in use.",
            )

    return redirect(
        "admin_dashboard:school_class_detail",
        class_id=subject.school_class_id,
    )

# ============================================================
# TERMS
# ============================================================
@admin_required
def terms(request):
    term_list = (
        Term.objects
        .select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        )
        .annotate(
            week_count=Count(
                "weeks",
                distinct=True,
            ),
            lesson_count=Count(
                "weeks__lessons",
                distinct=True,
            ),
        )
        .order_by(
            "subject__school_class__education_level__order",
            "subject__school_class__order",
            "subject__name",
            "order",
        )
    )

    context = {
        "terms": term_list,
        "term_count": Term.objects.count(),
        "total_terms": Term.objects.count(),
        "total_weeks": Week.objects.count(),
        "total_lessons": Lesson.objects.count(),
        "terms_mode": True,
    }

    return render(
        request,
        "admin_dashboard/terms.html",
        context,
    )

@admin_required
def term_create(request):
    subject_id = (
        request.GET.get("subject")
        or request.POST.get("subject")
    )

    if request.method == "POST":
        form = TermForm(request.POST)

        if form.is_valid():
            term = form.save()

            messages.success(
                request,
                "Term created successfully.",
            )

            return redirect(
                "admin_dashboard:term_detail",
                term_id=term.id,
            )
    else:
        form = TermForm(
            initial={
                "subject": subject_id,
            }
        )

    return render(
        request,
        "admin_dashboard/term_form.html",
        {
            "form": form,
            "term_form_mode": True,
        },
    )

@admin_required
def term_detail(request, term_id):
    term = get_object_or_404(
        Term.objects.select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        ),
        id=term_id,
    )

    weeks = (
        term.weeks
        .all()
        .annotate(
            lesson_count=Count("lessons"),
        )
        .order_by("number")
    )

    total_weeks = weeks.count()

    total_lessons = Lesson.objects.filter(
        week__term=term
    ).count()
    curriculum_material = CurriculumMaterial.objects.filter(
    term=term
    ).first()
    context = {
        "term": term,
        "weeks": weeks,
        "total_weeks": total_weeks,
        "total_lessons": total_lessons,
        "curriculum_material": curriculum_material,
    }

    return render(
        request,
        "admin_dashboard/term_detail.html",
        context,
    )

@admin_required
def term_edit(request, term_id):
    term = get_object_or_404(
        Term.objects.select_related(
            "subject",
            "subject__school_class",
            "subject__school_class__education_level",
        ),
        pk=term_id,
    )

    if request.method == "POST":
        form = TermForm(
            request.POST,
            instance=term,
        )

        if form.is_valid():
            term = form.save()

            messages.success(
                request,
                f"Term '{term.name}' was updated successfully.",
            )

            return redirect(
                "admin_dashboard:term_detail",
                term_id=term.pk,
            )

    else:
        form = TermForm(
            instance=term,
        )

    return render(
        request,
        "admin_dashboard/term_form.html",
        {
            "form": form,
            "term": term,
            "edit_mode": True,
        },
    )

@admin_required
def term_delete(request, term_id):
    term = get_object_or_404(
        Term.objects.select_related(
            "subject",
        ),
        id=term_id,
    )

    if request.method == "POST":
        week_count = Week.objects.filter(
            term=term
        ).count()

        if week_count > 0:
            messages.error(
                request,
                (
                    "This term cannot be deleted because "
                    f"it still contains {week_count} week(s). "
                    "Delete those weeks first."
                ),
            )

            return redirect(
                "admin_dashboard:term_detail",
                term_id=term.id,
            )

        subject_id = term.subject_id

        try:
            term.delete()

            messages.success(
                request,
                "Term deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This term cannot be deleted because it is still in use.",
            )

        return redirect(
            "admin_dashboard:subject_detail",
            subject_id=subject_id,
        )

    return redirect(
        "admin_dashboard:term_detail",
        term_id=term.id,
    )

# ============================================================
# WEEKS
# ============================================================
@admin_required
def weeks(request):
    week_list = (
        Week.objects
        .select_related(
            "term",
            "term__subject",
            "term__subject__school_class",
            "term__subject__school_class__education_level",
        )
        .annotate(
            lesson_count=Count(
                "lessons",
                distinct=True,
            ),
        )
        .order_by(
            "term__subject__school_class__education_level__order",
            "term__subject__school_class__order",
            "term__subject__name",
            "term__order",
            "number",
        )
    )

    context = {
        "weeks": week_list,
        "week_count": Week.objects.count(),
        "total_weeks": Week.objects.count(),
        "total_lessons": Lesson.objects.count(),
        "weeks_mode": True,
    }

    return render(
        request,
        "admin_dashboard/weeks.html",
        context,
    )

@admin_required
def week_create(request):
    term_id = request.GET.get("term") or request.POST.get("term")

    if request.method == "POST":
        form = WeekForm(request.POST)

        if form.is_valid():
            week = form.save()

            messages.success(
                request,
                "Week created successfully.",
            )

            return redirect(
                "admin_dashboard:week_detail",
                week_id=week.id,
            )
    else:
        form = WeekForm(
            initial={
                "term": term_id,
            }
        )

    return render(
        request,
        "admin_dashboard/week_form.html",
        {
            "form": form,
            "week_form_mode": True,
        },
    )

@admin_required
def week_detail(request, week_id):
    week = get_object_or_404(
        Week.objects.select_related(
            "term",
            "term__subject",
            "term__subject__school_class",
            "term__subject__school_class__education_level",
        ),
        id=week_id,
    )

    lessons = (
        week.lessons
        .order_by("order")
    )

    total_lessons = lessons.count()

    curriculum_material = CurriculumMaterial.objects.filter(
    week=week
    ).first()
    return render(
        request,
        "admin_dashboard/week_detail.html",
        {
            "week": week,
            "lessons": lessons,
            "total_lessons": total_lessons,
            "curriculum_material": curriculum_material,
        },
    )

@admin_required
def week_edit(request, week_id):
    week = get_object_or_404(
        Week,
        id=week_id,
    )

    if request.method == "POST":
        form = WeekForm(
            request.POST,
            instance=week,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Week updated successfully.",
            )

            return redirect(
                "admin_dashboard:curriculum"
            )
    else:
        form = WeekForm(
            instance=week
        )

    return render(
        request,
        "admin_dashboard/week_form.html",
        {
            "form": form,
            "week": week,
            "week_edit_mode": True,
        },
    )

@admin_required
def week_delete(request, week_id):
    week = get_object_or_404(
        Week.objects.select_related(
            "term",
        ),
        id=week_id,
    )

    if request.method == "POST":
        lesson_count = Lesson.objects.filter(
            week=week
        ).count()

        if lesson_count > 0:
            messages.error(
                request,
                (
                    "This week cannot be deleted because "
                    f"it still contains {lesson_count} lesson(s). "
                    "Delete those lessons first."
                ),
            )

            return redirect(
                "admin_dashboard:week_detail",
                week_id=week.id,
            )

        term_id = week.term_id

        try:
            week.delete()

            messages.success(
                request,
                "Week deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This week cannot be deleted because it is still in use.",
            )

        return redirect(
            "admin_dashboard:term_detail",
            term_id=term_id,
        )

    return redirect(
        "admin_dashboard:week_detail",
        week_id=week.id,
    )

# ============================================================
# CURRICULUM MATERIALS — WEEK / TERM PDF MANAGEMENT
# ============================================================

@admin_required
def curriculum_material_manage(request, level, object_id):
    if level == "week":
        parent = get_object_or_404(Week, pk=object_id)
        material = CurriculumMaterial.objects.filter(
            week=parent
        ).first()

        parent_label = f"Week {parent.number} — {parent.title}"

        if material is None:
            material = CurriculumMaterial(week=parent)

        redirect_name = "admin_dashboard:week_detail"
        redirect_kwargs = {"week_id": parent.pk}

    elif level == "term":
        parent = get_object_or_404(Term, pk=object_id)
        material = CurriculumMaterial.objects.filter(
            term=parent
        ).first()

        parent_label = parent.name

        if material is None:
            material = CurriculumMaterial(term=parent)

        redirect_name = "admin_dashboard:term_detail"
        redirect_kwargs = {"term_id": parent.pk}

    else:
        from django.http import Http404
        raise Http404("Invalid curriculum material type.")

    if request.method == "POST":
        form = CurriculumMaterialForm(
            request.POST,
            request.FILES,
            instance=material,
        )

        if form.is_valid():
            saved_material = form.save()

            messages.success(
                request,
                "Study material saved successfully.",
            )

            return redirect(
                redirect_name,
                **redirect_kwargs,
            )

    else:
        form = CurriculumMaterialForm(
            instance=material,
        )

    return render(
        request,
        "admin_dashboard/curriculum_material_form.html",
        {
            "form": form,
            "parent": parent,
            "parent_label": parent_label,
            "parent_type": level,
            "material": material,
            "edit_mode": material.pk is not None,
        },
    )


@admin_required
def curriculum_material_delete(request, level, object_id):
    if request.method != "POST":
        from django.http import Http404
        raise Http404("Invalid request method.")

    if level == "week":
        parent = get_object_or_404(Week, pk=object_id)
        material = CurriculumMaterial.objects.filter(
            week=parent
        ).first()

        redirect_name = "admin_dashboard:week_detail"
        redirect_kwargs = {"week_id": parent.pk}

    elif level == "term":
        parent = get_object_or_404(Term, pk=object_id)
        material = CurriculumMaterial.objects.filter(
            term=parent
        ).first()

        redirect_name = "admin_dashboard:term_detail"
        redirect_kwargs = {"term_id": parent.pk}

    else:
        from django.http import Http404
        raise Http404("Invalid curriculum material type.")

    if material:
        if material.file:
            material.file.delete(save=False)

        material.delete()

        messages.success(
            request,
            "Study material deleted successfully.",
        )
    else:
        messages.warning(
            request,
            "No study material was found to delete.",
        )

    return redirect(
        redirect_name,
        **redirect_kwargs,
    )
# ============================================================
# LESSONS
# ============================================================

@admin_required
def lessons(request):
    lesson_list = (
        Lesson.objects
        .select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",
        )
        .order_by(
            "week__term__subject__school_class__education_level__order",
            "week__term__subject__school_class__order",
            "week__term__subject__name",
            "week__term__order",
            "week__number",
            "order",
        )
    )

    context = {
        "lessons": lesson_list,
        "lesson_count": lesson_list.count(),
        "total_lessons": Lesson.objects.count(),
        "total_weeks": Week.objects.count(),
        "lessons_mode": True,
    }

    return render(
        request,
        "admin_dashboard/lessons.html",
        context,
    )

@admin_required
def lesson_create(request):
    week_id = request.GET.get("week") or request.POST.get("week")

    if request.method == "POST":

        form = LessonForm(request.POST)

        if form.is_valid():

            lesson = form.save()

            messages.success(
                request,
                "Lesson created successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=lesson.id,
            )

    else:

        form = LessonForm(
            initial={
                "week": week_id,
            }
        )

    return render(
        request,
        "admin_dashboard/lesson_form.html",
        {
            "form": form,
            "week_id": week_id,
        },
    )


@admin_required
def lesson_detail(request, lesson_id):

    lesson = get_object_or_404(
        Lesson.objects.select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",
        ),
        id=lesson_id,
    )

    videos = (
        LessonVideo.objects
        .filter(lesson=lesson)
        .order_by("order", "id")
    )

    images = (
        LessonImage.objects
        .filter(lesson=lesson)
        .order_by("order", "id")
    )

    resources = (
        LessonResource.objects
        .filter(lesson=lesson)
        .order_by("order", "id")
    )

    quizzes = (
        Quiz.objects
        .filter(lesson=lesson)
        .order_by("id")
    )

    return render(
        request,
        "admin_dashboard/lesson_detail.html",
        {
            "lesson": lesson,
            "videos": videos,
            "images": images,
            "resources": resources,
            "quizzes": quizzes,
            "total_videos": videos.count(),
            "total_images": images.count(),
            "total_resources": resources.count(),
            "total_quizzes": quizzes.count(),
        },
    )


@admin_required
def lesson_edit(request, lesson_id):

    lesson = get_object_or_404(
        Lesson.objects.select_related("week"),
        id=lesson_id,
    )

    if request.method == "POST":

        form = LessonForm(
            request.POST,
            instance=lesson,
        )

        if form.is_valid():

            try:

                form.save()

                messages.success(
                    request,
                    "Lesson updated successfully.",
                )

                return redirect(
                    "admin_dashboard:lesson_detail",
                    lesson_id=lesson.id,
                )

            except ValidationError as exc:

                form.add_error(
                    None,
                    exc,
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "A lesson with these details already exists.",
                )

    else:

        form = LessonForm(
            instance=lesson,
        )

    return render(
        request,
        "admin_dashboard/lesson_form.html",
        {
            "form": form,
            "lesson": lesson,
            "week": lesson.week,
            "edit_mode": True,
        },
    )


@admin_required
def lesson_delete(request, lesson_id):

    lesson = get_object_or_404(
        Lesson.objects.select_related("week"),
        id=lesson_id,
    )

    if request.method == "POST":

        video_count = LessonVideo.objects.filter(
            lesson=lesson
        ).count()

        image_count = LessonImage.objects.filter(
            lesson=lesson
        ).count()

        resource_count = LessonResource.objects.filter(
            lesson=lesson
        ).count()

        quiz_count = Quiz.objects.filter(
            lesson=lesson
        ).count()

        if any(
            [
                video_count,
                image_count,
                resource_count,
                quiz_count,
            ]
        ):

            messages.error(
                request,
                (
                    "This lesson cannot be deleted because it still "
                    "contains videos, images, resources, or quizzes. "
                    "Remove its associated content first."
                ),
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=lesson.id,
            )

        week_id = lesson.week_id

        try:

            lesson.delete()

            messages.success(
                request,
                "Lesson deleted successfully.",
            )

        except IntegrityError:

            messages.error(
                request,
                "This lesson cannot be deleted because it is still in use.",
            )

        return redirect(
            "admin_dashboard:week_detail",
            week_id=week_id,
        )

    return redirect(
        "admin_dashboard:lesson_detail",
        lesson_id=lesson.id,
    )

# ============================================================
# LESSON CONTENT
# ============================================================
@admin_required
def lesson_content(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",
        ),
        id=lesson_id,
    )

    videos = (
        lesson.videos
        .all()
        .order_by("order", "id")
    )

    images = (
        lesson.images
        .all()
        .order_by("order", "id")
    )

    resources = (
        lesson.resources
        .all()
        .order_by("order", "id")
    )

    quizzes = (
        Quiz.objects
        .filter(lesson=lesson)
        .prefetch_related("questions")
        .order_by(
            "-created_at",
            "title",
        )
    )

    return render(
        request,
        "admin_dashboard/lesson_content.html",
        {
            "lesson": lesson,
            "videos": videos,
            "images": images,
            "resources": resources,
            "quizzes": quizzes,
            "lesson_content_mode": True,
        },
    )

# ============================================================
# LESSON VIDEOS
# ============================================================
@admin_required
def lesson_video_add(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
    )

    if request.method == "POST":
        form = LessonVideoForm(request.POST)

        if form.is_valid():
            video = form.save(commit=False)
            video.lesson = lesson
            video.save()

            messages.success(
                request,
                "Lesson video added successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=lesson.id,
            )
    else:
        form = LessonVideoForm()

    return render(
        request,
        "admin_dashboard/lesson_video_form.html",
        {
            "form": form,
            "lesson": lesson,
            "lesson_video_form_mode": True,
        },
    )

@admin_required
def lesson_video_edit(request, video_id):
    video = get_object_or_404(
        LessonVideo.objects.select_related("lesson"),
        id=video_id,
    )

    if request.method == "POST":
        form = LessonVideoForm(
            request.POST,
            instance=video,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Lesson video updated successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=video.lesson_id,
            )
    else:
        form = LessonVideoForm(
            instance=video,
        )

    return render(
        request,
        "admin_dashboard/lesson_video_form.html",
        {
            "form": form,
            "lesson": video.lesson,
            "video": video,
            "lesson_video_form_mode": True,
            "edit_mode": True,
        },
    )

@admin_required
def lesson_video_delete(request, video_id):
    video = get_object_or_404(
        LessonVideo.objects.select_related("lesson"),
        id=video_id,
    )

    lesson_id = video.lesson_id

    if request.method == "POST":
        video.delete()

        messages.success(
            request,
            "Lesson video deleted successfully.",
        )

    return redirect(
        "admin_dashboard:lesson_detail",
        lesson_id=lesson_id,
    )

# ============================================================
# LESSON IMAGES
# ============================================================
@admin_required
def lesson_image_add(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
    )

    if request.method == "POST":
        form = LessonImageForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            image = form.save(commit=False)
            image.lesson = lesson
            image.save()

            messages.success(
                request,
                "Lesson image added successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=lesson.id,
            )
    else:
        form = LessonImageForm()

    return render(
        request,
        "admin_dashboard/lesson_image_form.html",
        {
            "form": form,
            "lesson": lesson,
            "lesson_image_form_mode": True,
        },
    )

@admin_required
def lesson_image_edit(request, image_id):
    image = get_object_or_404(
        LessonImage.objects.select_related("lesson"),
        id=image_id,
    )

    if request.method == "POST":
        form = LessonImageForm(
            request.POST,
            request.FILES,
            instance=image,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Lesson image updated successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=image.lesson_id,
            )
    else:
        form = LessonImageForm(
            instance=image,
        )

    return render(
        request,
        "admin_dashboard/lesson_image_form.html",
        {
            "form": form,
            "lesson": image.lesson,
            "image": image,
            "lesson_image_form_mode": True,
            "edit_mode": True,
        },
    )

@admin_required
def lesson_image_delete(request, image_id):
    image = get_object_or_404(
        LessonImage.objects.select_related("lesson"),
        id=image_id,
    )

    lesson_id = image.lesson_id

    if request.method == "POST":
        image.delete()

        messages.success(
            request,
            "Lesson image deleted successfully.",
        )

    return redirect(
        "admin_dashboard:lesson_detail",
        lesson_id=lesson_id,
    )

# ============================================================
# LESSON RESOURCES
# ============================================================
@admin_required
def lesson_resource_add(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
    )

    if request.method == "POST":
        form = LessonResourceForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            resource = form.save(commit=False)
            resource.lesson = lesson
            resource.save()

            messages.success(
                request,
                "Lesson resource added successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=lesson.id,
            )
    else:
        form = LessonResourceForm()

    return render(
        request,
        "admin_dashboard/lesson_resource_form.html",
        {
            "form": form,
            "lesson": lesson,
            "lesson_resource_form_mode": True,
        },
    )

@admin_required
def lesson_resource_edit(request, resource_id):
    resource = get_object_or_404(
        LessonResource.objects.select_related("lesson"),
        id=resource_id,
    )

    if request.method == "POST":
        form = LessonResourceForm(
            request.POST,
            request.FILES,
            instance=resource,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Lesson resource updated successfully.",
            )

            return redirect(
                "admin_dashboard:lesson_detail",
                lesson_id=resource.lesson_id,
            )
    else:
        form = LessonResourceForm(
            instance=resource,
        )

    return render(
        request,
        "admin_dashboard/lesson_resource_form.html",
        {
            "form": form,
            "lesson": resource.lesson,
            "resource": resource,
            "lesson_resource_form_mode": True,
            "edit_mode": True,
        },
    )

@admin_required
def lesson_resource_delete(request, resource_id):
    resource = get_object_or_404(
        LessonResource.objects.select_related("lesson"),
        id=resource_id,
    )

    lesson_id = resource.lesson_id

    if request.method == "POST":
        resource.delete()

        messages.success(
            request,
            "Lesson resource deleted successfully.",
        )

    return redirect(
        "admin_dashboard:lesson_detail",
        lesson_id=lesson_id,
    )
# ============================================================
# INDEPENDENT COURSES
# ============================================================
@admin_required
def courses(request):
    course_list = (
        Course.objects
        .select_related(
            "category",
            "education_level",
            "subject",
        )
        .order_by(
            "-created_at",
            "title",
        )
    )

    return render(
        request,
        "admin_dashboard/curriculum.html",
        {
            "courses": course_list,
            "course_count": course_list.count(),
            "courses_mode": True,
        },
    )

@admin_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            course = form.save()

            messages.success(
                request,
                "Course created successfully.",
            )

            return redirect(
                "admin_dashboard:curriculum"
            )
    else:
        form = CourseForm()

    return render(
        request,
        "admin_dashboard/course_form.html",
        {
            "form": form,
            "course_create_mode": True,
        },
    )

@admin_required
def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related(
            "category",
            "education_level",
            "subject",
        ),
        id=course_id,
    )

    return render(
        request,
        "admin_dashboard/curriculum.html",
        {
            "course": course,
            "course_detail_mode": True,
        },
    )

@admin_required
def course_edit(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
    )

    if request.method == "POST":
        form = CourseForm(
            request.POST,
            request.FILES,
            instance=course,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Course updated successfully.",
            )

            return redirect(
                "admin_dashboard:curriculum"
            )
    else:
        form = CourseForm(
            instance=course
        )

    return render(
        request,
        "admin_dashboard/course_form.html",
        {
            "form": form,
            "course": course,
            "course_edit_mode": True,
        },
    )

@admin_required
def course_delete(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
    )

    if request.method == "POST":
        try:
            course.delete()

            messages.success(
                request,
                "Course deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This course cannot be deleted because it is still in use.",
            )

    return redirect(
        "admin_dashboard:curriculum"
    )


# ============================================================
# TECH CATEGORIES
# ============================================================

@admin_required
def tech_categories(request):
    category_list = (
        TechCategory.objects
        .annotate(
            course_count=Count(
                "courses",
                distinct=True,
            ),
        )
        .order_by(
            "order",
            "name",
        )
    )

    context = {
        "tech_categories": category_list,
        "tech_category_count": TechCategory.objects.count(),
        "published_tech_categories": TechCategory.objects.filter(
            published=True
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/tech_categories.html",
        context,
    )


@admin_required
def tech_category_create(request):
    if request.method == "POST":
        form = TechCategoryForm(request.POST)

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                f"Tech category '{category.name}' was created successfully.",
            )

            return redirect(
                "admin_dashboard:tech_category_detail",
                category_id=category.id,
            )

    else:
        form = TechCategoryForm()

    return render(
        request,
        "admin_dashboard/tech_category_form.html",
        {
            "form": form,
            "tech_category_form_mode": True,
            "edit_mode": False,
            "title": "Create Tech Category",
        },
    )

@admin_required
def tech_category_detail(request, category_id):
    category = get_object_or_404(
        TechCategory,
        id=category_id,
    )

    courses = (
        category.courses
        .all()
        .order_by(
            "-created_at",
            "title",
        )
    )

    return render(
        request,
        "admin_dashboard/tech_category_detail.html",
        {
            "category": category,
            "courses": courses,
            "course_count": courses.count(),
        },
    )

@admin_required
def tech_category_edit(request, category_id):
    category = get_object_or_404(
        TechCategory,
        id=category_id,
    )

    if request.method == "POST":
        form = TechCategoryForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                f"Tech category '{category.name}' was updated successfully.",
            )

            return redirect(
                "admin_dashboard:tech_category_detail",
                category_id=category.id,
            )

    else:
        form = TechCategoryForm(
            instance=category,
        )

    return render(
        request,
        "admin_dashboard/tech_category_form.html",
        {
            "form": form,
            "tech_category": category,
            "tech_category_form_mode": True,
            "edit_mode": True,
            "title": "Edit Tech Category",
        },
    )

@admin_required
def tech_category_delete(request, category_id):
    category = get_object_or_404(
        TechCategory,
        id=category_id,
    )

    if request.method == "POST":
        course_count = category.courses.count()

        if course_count > 0:
            messages.error(
                request,
                (
                    "This tech category cannot be deleted because "
                    f"it still contains {course_count} course(s). "
                    "Delete or move those courses first."
                ),
            )

            return redirect(
                "admin_dashboard:tech_category_detail",
                category_id=category.id,
            )

        try:
            category.delete()

            messages.success(
                request,
                "Tech category deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This tech category cannot be deleted because it is still in use.",
            )

    return redirect(
        "admin_dashboard:tech_categories"
    )

@admin_required
def tech_courses(request):
    courses = (
        TechCourse.objects
        .select_related("category")
        .annotate(
            module_count=Count("modules", distinct=True),
            lesson_count=Count(
                "modules__lessons",
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )

    total_tech_courses = courses.count()

    published_tech_courses = courses.filter(
        published=True
    ).count()

    draft_tech_courses = courses.filter(
        published=False
    ).count()

    total_tech_modules = TechModule.objects.count()

    total_tech_lessons = TechLesson.objects.count()

    return render(
        request,
        "admin_dashboard/tech_courses.html",
        {
            "courses": courses,
            "total_tech_courses": total_tech_courses,
            "published_tech_courses": published_tech_courses,
            "draft_tech_courses": draft_tech_courses,
            "total_tech_modules": total_tech_modules,
            "total_tech_lessons": total_tech_lessons,
        },
    )

@admin_required
def tech_course_create(request):
    if request.method == "POST":
        form = TechCourseForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            course = form.save()

            messages.success(
                request,
                f'Tech course "{course.title}" was created successfully.',
            )

            return redirect(
                "admin_dashboard:tech_course_detail",
                course_id=course.id,
            )

    else:
        form = TechCourseForm()

    return render(
        request,
        "admin_dashboard/tech_course_form.html",
        {
            "form": form,
            "page_title": "Create Tech Course",
            "form_title": "Create Tech Course",
            "submit_text": "Create Course",
        },
    )


@admin_required
def tech_course_detail(request, course_id):
    course = get_object_or_404(
        TechCourse.objects.select_related("category"),
        id=course_id,
    )

    modules = course.modules.all().order_by(
        "order",
        "id",
    )

    return render(
        request,
        "admin_dashboard/tech_course_detail.html",
        {
            "course": course,
            "modules": modules,
        },
    )

@admin_required
def tech_course_edit(request, course_id):
    course = get_object_or_404(
        TechCourse,
        id=course_id,
    )

    if request.method == "POST":
        form = TechCourseForm(
            request.POST,
            request.FILES,
            instance=course,
        )

        if form.is_valid():
            course = form.save()

            messages.success(
                request,
                f'Tech course "{course.title}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:tech_course_detail",
                course_id=course.id,
            )

    else:
        form = TechCourseForm(
            instance=course,
        )

    return render(
        request,
        "admin_dashboard/tech_course_form.html",
        {
            "form": form,
            "course": course,
            "page_title": "Edit Tech Course",
            "form_title": "Edit Tech Course",
            "submit_text": "Save Changes",
        },
    )

@admin_required
def tech_course_delete(request, course_id):
    course = get_object_or_404(
        TechCourse,
        id=course_id,
    )

    if request.method == "POST":
        course_title = course.title

        course.delete()

        messages.success(
            request,
            f'Tech course "{course_title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:tech_courses"
        )

    modules = course.modules.all().order_by(
        "order",
        "id",
    )

    return render(
        request,
        "admin_dashboard/tech_course_detail.html",
        {
            "course": course,
            "modules": modules,
            "delete_confirmation": True,
        },
    )

@admin_required
def tech_modules(request):
    modules = TechModule.objects.select_related(
        "course",
        "course__category",
    ).order_by(
        "course",
        "order",
        "id",
    )

    return render(
        request,
        "admin_dashboard/tech_modules.html",
        {"modules": modules},
    )

@admin_required
def tech_module_create(request):
    course_id = request.GET.get("course")

    if request.method == "POST":
        form = TechModuleForm(request.POST)

        if form.is_valid():
            module = form.save()

            messages.success(
                request,
                f'Module "{module.title}" was created successfully.',
            )

            return redirect(
                "admin_dashboard:tech_module_detail",
                module_id=module.id,
            )

    else:
        initial = {}

        if course_id:
            initial["course"] = course_id

        form = TechModuleForm(initial=initial)

    return render(
        request,
        "admin_dashboard/tech_module_form.html",
        {
            "form": form,
            "page_title": "Create Tech Module",
            "form_title": "Create Tech Module",
            "submit_text": "Create Module",
        },
    )

@admin_required
def tech_module_detail(request, module_id):
    module = get_object_or_404(
        TechModule.objects.select_related(
            "course",
            "course__category",
        ),
        id=module_id,
    )

    lessons = module.lessons.all().order_by(
        "order",
        "id",
    )

    return render(
        request,
        "admin_dashboard/tech_module_detail.html",
        {
            "module": module,
            "lessons": lessons,
        },
    )

@admin_required
def tech_module_edit(request, module_id):
    module = get_object_or_404(
        TechModule,
        id=module_id,
    )

    if request.method == "POST":
        form = TechModuleForm(
            request.POST,
            instance=module,
        )

        if form.is_valid():
            module = form.save()

            messages.success(
                request,
                f'Module "{module.title}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:tech_module_detail",
                module_id=module.id,
            )

    else:
        form = TechModuleForm(
            instance=module,
        )

    return render(
        request,
        "admin_dashboard/tech_module_form.html",
        {
            "form": form,
            "module": module,
            "page_title": "Edit Tech Module",
            "form_title": "Edit Tech Module",
            "submit_text": "Save Changes",
        },
    )

@admin_required
def tech_module_delete(request, module_id):
    module = get_object_or_404(
        TechModule,
        id=module_id,
    )

    if request.method == "POST":
        module_title = module.title
        course_id = module.course_id

        module.delete()

        messages.success(
            request,
            f'Module "{module_title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:tech_course_detail",
            course_id=course_id,
        )

    lessons = module.lessons.all().order_by(
        "order",
        "id",
    )

    return render(
        request,
        "admin_dashboard/tech_module_detail.html",
        {
            "module": module,
            "lessons": lessons,
            "delete_confirmation": True,
        },
    )

@admin_required
def tech_lessons(request):
    tech_lessons = (
        TechLesson.objects
        .select_related(
            "module",
            "module__course",
            "module__course__category",
        )
        .order_by(
            "module__course__title",
            "module__order",
            "order",
            "id",
        )
    )

    total_tech_lessons = TechLesson.objects.count()

    published_tech_lessons = TechLesson.objects.filter(
        published=True
    ).count()

    draft_tech_lessons = TechLesson.objects.filter(
        published=False
    ).count()

    total_tech_content = (
        TechLessonVideo.objects.count()
        + TechLessonImage.objects.count()
        + TechLessonResource.objects.count()
    )

    return render(
        request,
        "admin_dashboard/tech_lessons.html",
        {
            "tech_lessons": tech_lessons,
            "total_tech_lessons": total_tech_lessons,
            "published_tech_lessons": published_tech_lessons,
            "draft_tech_lessons": draft_tech_lessons,
            "total_tech_content": total_tech_content,
        },
    )

@admin_required
def tech_lesson_create(request):
    module_id = request.GET.get("module")

    if request.method == "POST":
        form = TechLessonForm(request.POST)

        if form.is_valid():
            lesson = form.save()

            messages.success(
                request,
                f'Lesson "{lesson.title}" was created successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=lesson.id,
            )

    else:
        initial = {}

        if module_id:
            initial["module"] = module_id

        form = TechLessonForm(initial=initial)

    return render(
        request,
        "admin_dashboard/tech_lesson_form.html",
        {
            "form": form,
            "page_title": "Create Tech Lesson",
            "form_title": "Create Tech Lesson",
            "submit_text": "Create Lesson",
        },
    )

@admin_required
def tech_lesson_detail(request, lesson_id):
    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
            "module__course__category",
        ),
        id=lesson_id,
    )

    videos = lesson.videos.all().order_by("order", "id")
    images = lesson.images.all().order_by("order", "id")
    resources = lesson.resources.all().order_by("order", "id")

    quiz = getattr(lesson, "quiz", None)

    return render(
        request,
        "admin_dashboard/tech_lesson_detail.html",
        {
            "lesson": lesson,
            "videos": videos,
            "images": images,
            "resources": resources,
            "quiz": quiz,
        },
    )


@admin_required
def tech_lesson_edit(request, lesson_id):
    lesson = get_object_or_404(
        TechLesson,
        id=lesson_id,
    )

    if request.method == "POST":
        form = TechLessonForm(
            request.POST,
            instance=lesson,
        )

        if form.is_valid():
            lesson = form.save()

            messages.success(
                request,
                f'Lesson "{lesson.title}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=lesson.id,
            )

    else:
        form = TechLessonForm(
            instance=lesson,
        )

    return render(
        request,
        "admin_dashboard/tech_lesson_form.html",
        {
            "form": form,
            "lesson": lesson,
            "page_title": "Edit Tech Lesson",
            "form_title": "Edit Tech Lesson",
            "submit_text": "Save Changes",
        },
    )


@admin_required
def tech_lesson_delete(request, lesson_id):
    lesson = get_object_or_404(
        TechLesson,
        id=lesson_id,
    )

    if request.method == "POST":
        lesson_title = lesson.title
        module_id = lesson.module_id

        lesson.delete()

        messages.success(
            request,
            f'Lesson "{lesson_title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:tech_module_detail",
            module_id=module_id,
        )

    videos = lesson.videos.all().order_by("order", "id")
    images = lesson.images.all().order_by("order", "id")
    resources = lesson.resources.all().order_by("order", "id")
    quiz = getattr(lesson, "quiz", None)

    return render(
        request,
        "admin_dashboard/tech_lesson_detail.html",
        {
            "lesson": lesson,
            "videos": videos,
            "images": images,
            "resources": resources,
            "quiz": quiz,
            "delete_confirmation": True,
        },
    )


# ==========================================================
# TECH LESSON VIDEO
#==========================================================

@admin_required
def tech_lesson_video_create(request, lesson_id):
    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
        ),
        id=lesson_id,
    )

    if request.method == "POST":
        form = TechLessonVideoForm(request.POST)

        if form.is_valid():
            video = form.save(commit=False)
            video.lesson = lesson
            video.save()

            messages.success(
                request,
                f'Video "{video.title}" was added successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=lesson.id,
            )

    else:
        form = TechLessonVideoForm()

    return render(
        request,
        "admin_dashboard/tech_lesson_video_form.html",
        {
            "form": form,
            "lesson": lesson,
            "page_title": "Add Lesson Video",
            "form_title": "Add Lesson Video",
            "submit_text": "Add Video",
        },
    )


@admin_required
def tech_lesson_video_edit(request, video_id):
    video = get_object_or_404(
        TechLessonVideo.objects.select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
        ),
        id=video_id,
    )

    if request.method == "POST":
        form = TechLessonVideoForm(
            request.POST,
            instance=video,
        )

        if form.is_valid():
            video = form.save()

            messages.success(
                request,
                f'Video "{video.title}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=video.lesson_id,
            )

    else:
        form = TechLessonVideoForm(instance=video)

    return render(
        request,
        "admin_dashboard/tech_lesson_video_form.html",
        {
            "form": form,
            "lesson": video.lesson,
            "video": video,
            "page_title": "Edit Lesson Video",
            "form_title": "Edit Lesson Video",
            "submit_text": "Save Changes",
        },
    )


@admin_required
def tech_lesson_video_delete(request, video_id):
    video = get_object_or_404(
        TechLessonVideo.objects.select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
        ),
        id=video_id,
    )

    lesson_id = video.lesson_id
    video_title = video.title

    if request.method == "POST":
        video.delete()

        messages.success(
            request,
            f'Video "{video_title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:tech_lesson_detail",
            lesson_id=lesson_id,
        )

    return render(
        request,
        "admin_dashboard/tech_lesson_detail.html",
        {
            "lesson": video.lesson,
            "videos": video.lesson.videos.all().order_by(
                "order",
                "id",
            ),
            "images": video.lesson.images.all().order_by(
                "order",
                "id",
            ),
            "resources": video.lesson.resources.all().order_by(
                "order",
                "id",
            ),
            "quiz": getattr(video.lesson, "quiz", None),
            "video_delete_confirmation": True,
            "video_to_delete": video,
        },
    )

@admin_required
def tech_lesson_image_create(request, lesson_id):
    lesson = get_object_or_404(
        TechLesson.objects.select_related(
            "module",
            "module__course",
            "module__course__category",
        ),
        id=lesson_id,
    )

    if request.method == "POST":
        form = TechLessonImageForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            image = form.save(commit=False)
            image.lesson = lesson
            image.save()

            messages.success(
                request,
                f'Image "{image.title}" was added successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=lesson.id,
            )
    else:
        form = TechLessonImageForm()

    return render(
        request,
        "admin_dashboard/tech_lesson_image_form.html",
        {
            "form": form,
            "lesson": lesson,
            "page_title": "Add Lesson Image",
            "form_title": "Add Lesson Image",
            "submit_text": "Add Image",
        },
    )


@admin_required
def tech_lesson_image_edit(request, image_id):
    image = get_object_or_404(
        TechLessonImage.objects.select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
            "lesson__module__course__category",
        ),
        id=image_id,
    )

    lesson = image.lesson

    if request.method == "POST":
        form = TechLessonImageForm(
            request.POST,
            request.FILES,
            instance=image,
        )

        if form.is_valid():
            image = form.save()

            messages.success(
                request,
                f'Image "{image.title}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:tech_lesson_detail",
                lesson_id=lesson.id,
            )
    else:
        form = TechLessonImageForm(instance=image)

    return render(
        request,
        "admin_dashboard/tech_lesson_image_form.html",
        {
            "form": form,
            "lesson": lesson,
            "image": image,
            "page_title": "Edit Lesson Image",
            "form_title": "Edit Lesson Image",
            "submit_text": "Save Changes",
        },
    )


@admin_required
def tech_lesson_image_delete(request, image_id):
    image = get_object_or_404(
        TechLessonImage.objects.select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
        ),
        id=image_id,
    )

    lesson = image.lesson

    if request.method == "POST":
        image_title = image.title
        image.delete()

        messages.success(
            request,
            f'Image "{image_title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:tech_lesson_detail",
            lesson_id=lesson.id,
        )

    videos = lesson.videos.all().order_by("order", "id")
    images = lesson.images.all().order_by("order", "id")
    resources = lesson.resources.all().order_by("order", "id")
    quiz = getattr(lesson, "quiz", None)

    return render(
        request,
        "admin_dashboard/tech_lesson_detail.html",
        {
            "lesson": lesson,
            "videos": videos,
            "images": images,
            "resources": resources,
            "quiz": quiz,
            "delete_image": image,
        },
    )


@admin_required
def tech_lesson_resource_create(request, lesson_id):

    lesson = get_object_or_404(

        TechLesson.objects.select_related(

            "module",

            "module__course",

        ),

        id=lesson_id,

    )

    if request.method == "POST":

        form = TechLessonResourceForm(

            request.POST,

            request.FILES,

        )

        if form.is_valid():

            resource = form.save(commit=False)

            resource.lesson = lesson

            resource.save()

            messages.success(

                request,

                "Resource added successfully.",

            )

            return redirect(

                "admin_dashboard:tech_lesson_detail",

                lesson_id=lesson.id,

            )

    else:

        form = TechLessonResourceForm()

    return render(

        request,

        "admin_dashboard/tech_lesson_resource_form.html",

        {

            "form": form,

            "lesson": lesson,

            "resource": None,

            "title": "Add Resource",

        },

    )


@admin_required
def tech_lesson_resource_edit(request, resource_id):

    resource = get_object_or_404(

        TechLessonResource.objects.select_related(

            "lesson",

            "lesson__module",

            "lesson__module__course",

        ),

        id=resource_id,

    )

    if request.method == "POST":

        form = TechLessonResourceForm(

            request.POST,

            request.FILES,

            instance=resource,

        )

        if form.is_valid():

            form.save()

            messages.success(

                request,

                "Resource updated successfully.",

            )

            return redirect(

                "admin_dashboard:tech_lesson_detail",

                lesson_id=resource.lesson.id,

            )

    else:

        form = TechLessonResourceForm(

            instance=resource,

        )

    return render(

        request,

        "admin_dashboard/tech_lesson_resource_form.html",

        {

            "form": form,

            "lesson": resource.lesson,

            "resource": resource,

            "title": "Edit Resource",

        },

    )


@admin_required
def tech_lesson_resource_delete(request, resource_id):

    resource = get_object_or_404(

        TechLessonResource,

        id=resource_id,

    )

    lesson_id = resource.lesson_id

    if request.method == "POST":

        resource.delete()

        messages.success(

            request,

            "Resource deleted successfully.",

        )

        return redirect(

            "admin_dashboard:tech_lesson_detail",

            lesson_id=lesson_id,

        )

    return redirect(

        "admin_dashboard:tech_lesson_detail",

        lesson_id=lesson_id,

    )


# =========================================================
# EXAM PREPARATION
# =========================================================

@admin_required
def exams(request):
    exams = Exam.objects.all().order_by("order", "name")

    context = {
        "exams": exams,
        "exam_count": exams.count(),
        "published_exams": exams.filter(published=True).count(),
        "unpublished_exams": exams.filter(published=False).count(),
    }

    return render(
        request,
        "admin_dashboard/exams.html",
        context,
    )

@admin_required
def exam_create(request):

    if request.method == "POST":
        form = ExamForm(request.POST)

        if form.is_valid():
            exam = form.save()

            messages.success(
                request,
                f'Exam "{exam.name}" was created successfully.',
            )

            return redirect(
                "admin_dashboard:exams"
            )

    else:
        form = ExamForm()

    return render(
        request,
        "admin_dashboard/exam_form.html",
        {
            "form": form,
            "page_title": "Create Examination",
            "page_subtitle": "Add a new examination to PupilAura Exam Preparation.",
            "form_action": "Create Examination",
            "is_edit": False,
        },
    )

@admin_required
def exam_detail(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    subjects = exam.subjects.all().order_by(
        "order",
        "name",
    )

    years = exam.years.all().order_by(
        "-year",
        "order",
    )

    resources = exam.resources.select_related(
        "subject",
        "year",
    ).order_by(
        "order",
        "title",
    )

    context = {
        "exam": exam,
        "subjects": subjects,
        "years": years,
        "resources": resources,
        "subject_count": subjects.count(),
        "year_count": years.count(),
        "resource_count": resources.count(),
    }

    return render(
        request,
        "admin_dashboard/exam_detail.html",
        context,
    )

@admin_required
def exam_edit(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    if request.method == "POST":
        form = ExamForm(
            request.POST,
            instance=exam,
        )

        if form.is_valid():
            exam = form.save()

            messages.success(
                request,
                f'Exam "{exam.name}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:exam_detail",
                exam_id=exam.id,
            )

    else:
        form = ExamForm(
            instance=exam,
        )

    return render(
        request,
        "admin_dashboard/exam_form.html",
        {
            "form": form,
            "exam": exam,
            "page_title": "Edit Examination",
            "page_subtitle": f"Update the settings for {exam.name}.",
            "form_action": "Save Changes",
            "is_edit": True,
        },
    )

@admin_required
def exam_delete(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    if request.method == "POST":

        exam_name = exam.name

        exam.delete()

        messages.success(
            request,
            f'Exam "{exam_name}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:exams"
        )

    return redirect(
        "admin_dashboard:exam_detail",
        exam_id=exam.id,
    )

# =========================================================
# EXAM SUBJECTS
# =========================================================

@admin_required
def exam_subjects(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    subjects = (
        ExamSubject.objects
        .filter(exam=exam)
        .order_by("order", "name")
    )

    context = {
        "exam": exam,
        "subjects": subjects,
        "subject_count": subjects.count(),
        "published_subjects": subjects.filter(published=True).count(),
        "unpublished_subjects": subjects.filter(published=False).count(),
        "nav_active": "exams",
        "pending_reviews": (
            Answer.objects
            .filter(reviewed=False)
            .exclude(question__question_type="objective")
            .count()
        ),
    }

    return render(request, "admin_dashboard/exam_subjects.html", context)

@admin_required
def exam_subject_create(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    if request.method == "POST":

        form = ExamSubjectForm(
            request.POST,
        )

        if form.is_valid():

            subject = form.save(
                commit=False
            )

            subject.exam = exam
            subject.save()

            messages.success(
                request,
                f'Subject "{subject.name}" was created successfully.',
            )

            return redirect(
                "admin_dashboard:exam_subjects",
                exam_id=exam.id,
            )

    else:

        form = ExamSubjectForm(
            initial={
                "exam": exam,
            }
        )

    return render(
        request,
        "admin_dashboard/exam_subject_form.html",
        {
            "form": form,
            "exam": exam,
            "page_title": "Create Exam Subject",
            "page_subtitle": f"Add a subject to {exam.name}.",
            "form_action": "Create Subject",
            "is_edit": False,
        },
    )

@admin_required
def exam_subject_detail(request, subject_id):

    subject = get_object_or_404(
        ExamSubject.objects.select_related("exam"),
        id=subject_id,
    )

    resources = subject.resources.select_related(
        "exam",
        "year",
    ).order_by(
        "order",
        "title",
    )

    context = {
        "subject": subject,
        "exam": subject.exam,
        "resources": resources,
        "resource_count": resources.count(),
    }

    return render(
        request,
        "admin_dashboard/exam_subject_detail.html",
        context,
    )


@admin_required
def exam_subject_edit(request, subject_id):

    subject = get_object_or_404(
        ExamSubject.objects.select_related("exam"),
        id=subject_id,
    )

    if request.method == "POST":

        form = ExamSubjectForm(
            request.POST,
            instance=subject,
        )

        if form.is_valid():

            subject = form.save()

            messages.success(
                request,
                f'Subject "{subject.name}" was updated successfully.',
            )

            return redirect(
                "admin_dashboard:exam_subject_detail",
                subject_id=subject.id,
            )

    else:

        form = ExamSubjectForm(
            instance=subject,
        )

    return render(
        request,
        "admin_dashboard/exam_subject_form.html",
        {
            "form": form,
            "exam": subject.exam,
            "subject": subject,
            "page_title": "Edit Exam Subject",
            "page_subtitle": f"Update the settings for {subject.name}.",
            "form_action": "Save Changes",
            "is_edit": True,
        },
    )


@admin_required
def exam_subject_delete(request, subject_id):

    subject = get_object_or_404(
        ExamSubject.objects.select_related("exam"),
        id=subject_id,
    )

    exam_id = subject.exam.id
    subject_name = subject.name

    if request.method == "POST":

        subject.delete()

        messages.success(
            request,
            f'Subject "{subject_name}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:exam_subjects",
            exam_id=exam_id,
        )

    return redirect(
        "admin_dashboard:exam_subject_detail",
        subject_id=subject.id,
    )

@admin_required
def exam_years(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    years = exam.years.all().order_by("-year", "order")

    context = {
        "exam": exam,
        "years": years,
        "year_count": years.count(),
        "published_years": years.filter(published=True).count(),
        "unpublished_years": years.filter(published=False).count(),
    }

    return render(
        request,
        "admin_dashboard/exam_years.html",
        context,
    )


@admin_required
def exam_year_create(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == "POST":
        form = ExamYearForm(request.POST)

        if form.is_valid():
            exam_year = form.save(commit=False)
            exam_year.exam = exam
            exam_year.save()

            messages.success(
                request,
                f"Exam year {exam_year.year} was created successfully.",
            )

            return redirect(
                "admin_dashboard:exam_years",
                exam_id=exam.id,
            )
    else:
        form = ExamYearForm(initial={"exam": exam})

    return render(
        request,
        "admin_dashboard/exam_year_form.html",
        {
            "form": form,
            "exam": exam,
            "page_title": "Create Exam Year",
            "page_subtitle": f"Add an exam year to {exam.name}.",
            "form_action": "Create Year",
            "is_edit": False,
        },
    )


@admin_required
def exam_year_detail(request, year_id):
    exam_year = get_object_or_404(
        ExamYear.objects.select_related("exam"),
        id=year_id,
    )

    resources = exam_year.resources.select_related(
        "exam",
        "subject",
    ).order_by("order", "title")

    context = {
        "exam_year": exam_year,
        "exam": exam_year.exam,
        "resources": resources,
        "resource_count": resources.count(),
        "published_resource_count": resources.filter(
            published=True
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/exam_year_detail.html",
        context,
    )


@admin_required
def exam_year_edit(request, year_id):
    exam_year = get_object_or_404(
        ExamYear.objects.select_related("exam"),
        id=year_id,
    )

    if request.method == "POST":
        form = ExamYearForm(
            request.POST,
            instance=exam_year,
        )

        if form.is_valid():
            exam_year = form.save()

            messages.success(
                request,
                f"Exam year {exam_year.year} was updated successfully.",
            )

            return redirect(
                "admin_dashboard:exam_year_detail",
                year_id=exam_year.id,
            )
    else:
        form = ExamYearForm(instance=exam_year)

    return render(
        request,
        "admin_dashboard/exam_year_form.html",
        {
            "form": form,
            "exam": exam_year.exam,
            "exam_year": exam_year,
            "page_title": "Edit Exam Year",
            "page_subtitle": f"Update the settings for {exam_year.year}.",
            "form_action": "Save Changes",
            "is_edit": True,
        },
    )


@admin_required
def exam_year_delete(request, year_id):
    exam_year = get_object_or_404(
        ExamYear.objects.select_related("exam"),
        id=year_id,
    )

    if request.method == "POST":
        exam_id = exam_year.exam_id
        year = exam_year.year

        exam_year.delete()

        messages.success(
            request,
            f"Exam year {year} and its associated resources were deleted.",
        )

        return redirect(
            "admin_dashboard:exam_years",
            exam_id=exam_id,
        )

    return redirect(
        "admin_dashboard:exam_year_detail",
        year_id=exam_year.id,
    )




# =========================================================
# EXAM RESOURCE CONTENT CONFIGURATION
# =========================================================

EXAM_RESOURCE_CONTENT_FORMS = {
    "lesson": (ExamLessonContentForm, "lesson"),
    "practical": (ExamPracticalContentForm, "practical"),
    "revision": (ExamRevisionContentForm, "revision"),
    "mock_exam": (ExamMockExamContentForm, "mock_exam"),
}


def get_exam_resource_content_forms(request, resource=None):
    """
    Build the type-specific content forms.

    Only the form matching the selected resource type is bound
    to POST data. The other forms remain available for the
    template to display conditionally.

    Past Questions and Solutions use ExamQuestion records
    instead of structured resource content.
    """

    if request.method == "POST":
        selected_type = request.POST.get(
            "resource_type",
            resource.resource_type if resource else "",
        )
    else:
        selected_type = (
            request.GET.get("resource_type")
            or (resource.resource_type if resource else "")
        )

    content_forms = {}

    for resource_type, (form_class, prefix) in (
        EXAM_RESOURCE_CONTENT_FORMS.items()
    ):
        initial = {}

        # Only reuse saved structured content when editing
        # the same resource type.
        if (
            resource
            and resource.resource_type == resource_type
        ):
            initial = resource.structured_content or {}

        if request.method == "POST" and selected_type == resource_type:
            content_form = form_class(
                request.POST,
                prefix=prefix,
                initial=initial,
            )
        else:
            content_form = form_class(
                prefix=prefix,
                initial=initial,
            )

        content_forms[resource_type] = content_form

    selected_content_form = None

    if selected_type in content_forms:
        selected_content_form = content_forms[selected_type]

    return selected_type, selected_content_form, content_forms


def get_exam_resource_content_data(
    selected_type,
    content_form,):
    """
    Return validated structured content for the selected
    resource type.

    Past Questions and Solutions intentionally return an
    empty dictionary because their content is stored in
    individual ExamQuestion records.
    """

    if selected_type not in EXAM_RESOURCE_CONTENT_FORMS:
        return {}

    if content_form is None:
        return {}

    return dict(content_form.cleaned_data)


# =========================================================
# EXAM RESOURCES
# =========================================================

@admin_required
def exam_resources(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    resources = exam.resources.select_related(
        "subject",
        "year",
    ).order_by("order", "title")

    context = {
        "exam": exam,
        "resources": resources,
        "resource_count": resources.count(),
        "published_resources": resources.filter(
            published=True,
        ).count(),
        "unpublished_resources": resources.filter(
            published=False,
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/exam_resources.html",
        context,
    )


@admin_required
def exam_resource_create(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == "POST":
        form = ExamResourceForm(
            request.POST,
            request.FILES,
        )
    else:
        form = ExamResourceForm(
            initial={"exam": exam},
        )

    # Lock the resource to the exam in the URL.
    form.fields["exam"].queryset = Exam.objects.filter(
        id=exam.id,
    )
    form.fields["exam"].initial = exam
    form.fields["exam"].disabled = True

    form.fields["subject"].queryset = exam.subjects.all()
    form.fields["year"].queryset = exam.years.all()

    (
        selected_type,
        content_form,
        content_forms,
    ) = get_exam_resource_content_forms(request)

    if request.method == "POST":
        resource_form_valid = form.is_valid()

        content_form_valid = (
            content_form.is_valid()
            if content_form is not None
            else True
        )

        if resource_form_valid and content_form_valid:
            resource = form.save(commit=False)
            resource.exam = exam

            resource.structured_content = (
                get_exam_resource_content_data(
                    selected_type,
                    content_form,
                )
            )

            try:
                with transaction.atomic():
                    resource.full_clean()
                    resource.save()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    f'Resource "{resource.title}" was created successfully.',
                )

                return redirect(
                    "admin_dashboard:exam_resource_detail",
                    resource_id=resource.id,
                )

    return render(
        request,
        "admin_dashboard/exam_resource_form.html",
        {
            "form": form,
            "exam": exam,
            "page_title": "Create Exam Resource",
            "page_subtitle": (
                f"Add past questions, solutions, lessons, or "
                f"study materials for {exam.name}."
            ),
            "form_action": "Create Resource",
            "is_edit": False,

            # Type-specific content forms.
            "selected_resource_type": selected_type,
            "content_form": content_form,
            "content_forms": content_forms,
        },
    )


@admin_required
def exam_resource_detail(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ).prefetch_related("questions"),
        id=resource_id,
    )

    questions = resource.questions.prefetch_related(
        "choices",
        "source_question",
    ).order_by(
        "order",
        "question_number",
    )

    return render(
        request,
        "admin_dashboard/exam_resource_detail.html",
        {
            "resource": resource,
            "exam": resource.exam,
            "questions": questions,
            "question_count": questions.count(),
        },
    )


@admin_required
def exam_resource_edit(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
    )

    exam = resource.exam

    if request.method == "POST":
        form = ExamResourceForm(
            request.POST,
            request.FILES,
            instance=resource,
        )
    else:
        form = ExamResourceForm(
            instance=resource,
        )

    # Keep the resource attached to its original exam.
    form.fields["exam"].queryset = Exam.objects.filter(
        id=exam.id,
    )
    form.fields["exam"].initial = exam
    form.fields["exam"].disabled = True

    form.fields["subject"].queryset = exam.subjects.all()
    form.fields["year"].queryset = exam.years.all()

    (
        selected_type,
        content_form,
        content_forms,
    ) = get_exam_resource_content_forms(
        request,
        resource=resource,
    )

    if request.method == "POST":
        resource_form_valid = form.is_valid()

        content_form_valid = (
            content_form.is_valid()
            if content_form is not None
            else True
        )

        if resource_form_valid and content_form_valid:
            updated_resource = form.save(commit=False)
            updated_resource.exam = exam

            # Save the content belonging to the selected type.
            #
            # This also clears old structured content when
            # changing to Past Questions or Solutions, or
            # switching between resource types.
            updated_resource.structured_content = (
                get_exam_resource_content_data(
                    selected_type,
                    content_form,
                )
            )

            try:
                with transaction.atomic():
                    updated_resource.full_clean()
                    updated_resource.save()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    f'Resource "{updated_resource.title}" was updated successfully.',
                )

                return redirect(
                    "admin_dashboard:exam_resource_detail",
                    resource_id=updated_resource.id,
                )

    return render(
        request,
        "admin_dashboard/exam_resource_form.html",
        {
            "form": form,
            "exam": exam,
            "resource": resource,
            "page_title": "Edit Exam Resource",
            "page_subtitle": f"Update {resource.title}.",
            "form_action": "Save Changes",
            "is_edit": True,

            # Type-specific content forms.
            "selected_resource_type": selected_type,
            "content_form": content_form,
            "content_forms": content_forms,
        },
    )


@admin_required
def exam_resource_delete(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related("exam"),
        id=resource_id,
    )

    if request.method == "POST":
        exam_id = resource.exam_id
        title = resource.title

        resource.delete()

        messages.success(
            request,
            f'Resource "{title}" was deleted successfully.',
        )

        return redirect(
            "admin_dashboard:exam_resources",
            exam_id=exam_id,
        )

    return redirect(
        "admin_dashboard:exam_resource_detail",
        resource_id=resource.id,
    )


# =========================================================
# EXAM QUESTION HELPERS
# =========================================================

from django.forms import inlineformset_factory
from django.db import transaction


def get_exam_question_source_queryset(resource):
    """
    Only allow a Solutions resource to reference questions from
    a Past Questions resource belonging to the same exam,
    subject, and year.
    """

    if resource.resource_type != "solutions":
        return ExamQuestion.objects.none()

    queryset = ExamQuestion.objects.filter(
        resource__resource_type="past_questions",
        resource__exam_id=resource.exam_id,
        resource__subject_id=resource.subject_id,
    )

    if resource.year_id:
        queryset = queryset.filter(
            resource__year_id=resource.year_id,
        )

    return queryset.select_related(
        "resource",
        "resource__exam",
        "resource__subject",
        "resource__year",
    ).order_by(
        "resource__year__year",
        "question_number",
    )


def configure_exam_question_form(form, resource):
    """
    Lock the question to its parent resource and configure
    the optional source-question field when that field exists.
    """

    form.fields["resource"].queryset = ExamResource.objects.filter(
        id=resource.id,
    )
    form.fields["resource"].initial = resource
    form.fields["resource"].disabled = True

    if "source_question" in form.fields:
        form.fields["source_question"].queryset = (
            get_exam_question_source_queryset(resource)
        )

        if resource.resource_type != "solutions":
            form.fields["source_question"].required = False
            form.fields["source_question"].help_text = (
                "Source-question linking is only available for Solutions resources."
            )
        else:
            form.fields["source_question"].help_text = (
                "Optionally link this solution to the corresponding "
                "question in a Past Questions resource."
            )


def get_exam_choice_formset(extra=0):
    """
    Build an inline formset for managing all answer choices
    directly inside the question create/edit page.

    The template uses the prefix 'choices'.
    """

    return inlineformset_factory(
        ExamQuestion,
        ExamChoice,
        form=ExamChoiceForm,
        extra=extra,
        can_delete=True,
        max_num=20,
        validate_max=True,
    )


def validate_exam_question_choices(choice_formset):
    """
    Validate MCQ answer choices.

    An MCQ must have:
    - At least four non-empty choices.
    - Exactly one correct answer.
    """

    active_choices = []

    for choice_form in choice_formset.forms:
        if not hasattr(choice_form, "cleaned_data"):
            continue

        cleaned_data = choice_form.cleaned_data

        if not cleaned_data:
            continue

        if cleaned_data.get("DELETE"):
            continue

        choice_text = (cleaned_data.get("text") or "").strip()

        if not choice_text:
            continue

        active_choices.append(cleaned_data)

    if len(active_choices) < 4:
        choice_formset._non_form_errors = (
            choice_formset.error_class([
                "A multiple-choice question must have at least four answer choices."
            ])
        )
        return False

    correct_count = sum(
        1 for choice in active_choices
        if choice.get("is_correct")
    )

    if correct_count != 1:
        choice_formset._non_form_errors = (
            choice_formset.error_class([
                "Select exactly one correct answer for this question."
            ])
        )
        return False

    return True


def save_exam_question_choices(question, choice_formset):
    """
    Save the submitted choices for an MCQ.

    Existing choices marked for deletion are removed.
    New and edited choices are saved with the question.
    """

    deleted_objects = getattr(
        choice_formset,
        "deleted_objects",
        [],
    )

    for deleted_choice in deleted_objects:
        deleted_choice.delete()

    saved_choices = choice_formset.save(commit=False)

    for index, choice in enumerate(saved_choices, start=1):
        choice.question = question
        choice.order = index
        choice.save()

    choice_formset.save_m2m()


# =========================================================
# EXAM QUESTIONS
# =========================================================

@admin_required
def exam_questions(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
    )

    questions = resource.questions.prefetch_related(
        "choices",
        "source_question",
    ).order_by(
        "order",
        "question_number",
    )

    context = {
        "resource": resource,
        "exam": resource.exam,
        "questions": questions,
        "question_count": questions.count(),
        "published_questions": questions.filter(
            published=True,
        ).count(),
        "unpublished_questions": questions.filter(
            published=False,
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/exam_questions.html",
        context,
    )


@admin_required
def exam_question_create(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
    )

    ChoiceFormSet = get_exam_choice_formset(extra=4)

    if request.method == "POST":
        form = ExamQuestionForm(
            request.POST,
            request.FILES,
        )
    else:
        last_question_number = (
            resource.questions.order_by("-question_number")
            .values_list("question_number", flat=True)
            .first()
            or 0
        )

        form = ExamQuestionForm(
            initial={
                "resource": resource,
                "question_number": last_question_number + 1,
                "question_type": "mcq",
                "marks": 1,
                "published": True,
            }
        )

    configure_exam_question_form(form, resource)

    choice_formset = ChoiceFormSet(
        request.POST or None,
        request.FILES or None,
        instance=form.instance,
        prefix="choices",
    )

    if request.method == "POST":
        question_valid = form.is_valid()

        question_type = (
            form.cleaned_data.get("question_type")
            if question_valid
            else request.POST.get("question_type", "mcq")
        )

        choices_valid = True

        if question_type == "mcq":
            choices_valid = choice_formset.is_valid()

            if choices_valid:
                choices_valid = validate_exam_question_choices(
                    choice_formset,
                )

        if question_valid and choices_valid:
            try:
                with transaction.atomic():
                    question = form.save(commit=False)
                    question.resource = resource

                    question.full_clean()
                    question.save()

                    if question.question_type == "mcq":
                        choice_formset.instance = question
                        save_exam_question_choices(
                            question,
                            choice_formset,
                        )
                    else:
                        question.choices.all().delete()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            if field in form.fields:
                                form.add_error(field, error)
                            else:
                                form.add_error(None, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    f"Question {question.question_number} and its answer choices "
                    "were created successfully.",
                )

                return redirect(
                    "admin_dashboard:exam_question_detail",
                    question_id=question.id,
                )

    return render(
        request,
        "admin_dashboard/exam_question_form.html",
        {
            "form": form,
            "choice_formset": choice_formset,
            "resource": resource,
            "exam": resource.exam,
            "page_title": "Create Exam Question",
            "page_subtitle": (
                f"Add a question and its answer choices to {resource.title}."
            ),
            "form_action": "Create Question",
            "is_edit": False,
        },
    )


@admin_required
def exam_question_detail(request, question_id):
    question = get_object_or_404(
        ExamQuestion.objects.select_related(
            "resource",
            "resource__exam",
            "resource__subject",
            "resource__year",
            "source_question",
            "source_question__resource",
        ).prefetch_related("choices"),
        id=question_id,
    )

    return render(
        request,
        "admin_dashboard/exam_question_detail.html",
        {
            "question": question,
            "resource": question.resource,
            "exam": question.resource.exam,
            "choices": question.choices.all(),
        },
    )


@admin_required
def exam_question_edit(request, question_id):
    question = get_object_or_404(
        ExamQuestion.objects.select_related(
            "resource",
            "resource__exam",
            "resource__subject",
            "resource__year",
        ).prefetch_related("choices"),
        id=question_id,
    )

    resource = question.resource

    ChoiceFormSet = get_exam_choice_formset(extra=0)

    if request.method == "POST":
        form = ExamQuestionForm(
            request.POST,
            request.FILES,
            instance=question,
        )
    else:
        form = ExamQuestionForm(
            instance=question,
        )

    configure_exam_question_form(form, resource)

    choice_formset = ChoiceFormSet(
        request.POST or None,
        request.FILES or None,
        instance=question,
        prefix="choices",
    )

    if request.method == "POST":
        question_valid = form.is_valid()

        question_type = (
            form.cleaned_data.get("question_type")
            if question_valid
            else request.POST.get(
                "question_type",
                question.question_type,
            )
        )

        choices_valid = True

        if question_type == "mcq":
            choices_valid = choice_formset.is_valid()

            if choices_valid:
                choices_valid = validate_exam_question_choices(
                    choice_formset,
                )

        if question_valid and choices_valid:
            try:
                with transaction.atomic():
                    updated_question = form.save(commit=False)
                    updated_question.resource = resource

                    updated_question.full_clean()
                    updated_question.save()

                    if updated_question.question_type == "mcq":
                        choice_formset.instance = updated_question
                        save_exam_question_choices(
                            updated_question,
                            choice_formset,
                        )
                    else:
                        updated_question.choices.all().delete()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            if field in form.fields:
                                form.add_error(field, error)
                            else:
                                form.add_error(None, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    "Exam question and its answer choices were updated successfully.",
                )

                return redirect(
                    "admin_dashboard:exam_question_detail",
                    question_id=updated_question.id,
                )

    return render(
        request,
        "admin_dashboard/exam_question_form.html",
        {
            "form": form,
            "choice_formset": choice_formset,
            "question": question,
            "resource": resource,
            "exam": resource.exam,
            "page_title": "Edit Exam Question",
            "page_subtitle": (
                f"Update Question {question.question_number} "
                "and its answer choices."
            ),
            "form_action": "Save Changes",
            "is_edit": True,
        },
    )


@admin_required
def exam_question_delete(request, question_id):
    question = get_object_or_404(
        ExamQuestion.objects.select_related("resource"),
        id=question_id,
    )

    if request.method == "POST":
        resource_id = question.resource_id
        question_number = question.question_number

        question.delete()

        messages.success(
            request,
            f"Question {question_number} was deleted successfully.",
        )

        return redirect(
            "admin_dashboard:exam_questions",
            resource_id=resource_id,
        )

    return redirect(
        "admin_dashboard:exam_question_detail",
        question_id=question.id,
    )

# =========================================================
# BULK EXAM QUESTION ENTRY
# =========================================================

@admin_required
def exam_question_bulk_create(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
    )

    # Bulk question entry is exclusively for Past Questions.
    if resource.resource_type != "past_questions":
        messages.error(
            request,
            "Bulk question entry is only available for Past Questions resources.",
        )
        return redirect(
            "admin_dashboard:exam_resource_detail",
            resource_id=resource.id,
        )

    last_question_number = (
        resource.questions.order_by("-question_number")
        .values_list("question_number", flat=True)
        .first()
        or 0
    )

    last_order = (
        resource.questions.order_by("-order")
        .values_list("order", flat=True)
        .first()
        or 0
    )

    initial_question = {
        "question_number": last_question_number + 1,
        "question_type": "mcq",
        "question_text": "",
        "explanation": "",
        "marks": 1,
        "order": last_order + 1,
        "choices": ["", "", "", ""],
        "correct_choice": "0",
        "published": True,
        "errors": [],
    }

    bulk_errors = []
    form_data = [initial_question]

    if request.method == "POST":
        try:
            question_count = int(
                request.POST.get("question_count", "0")
            )
        except (TypeError, ValueError):
            question_count = 0

        if question_count < 1:
            bulk_errors.append(
                "Add at least one question before submitting."
            )
            question_count = 1

        if question_count > 50:
            bulk_errors.append(
                "You can submit a maximum of 50 questions at a time."
            )
            question_count = 50

        form_data = []
        validated_questions = []
        used_question_numbers = set()

        for index in range(question_count):
            prefix = f"question_{index}_"

            data = {
                "question_number": request.POST.get(
                    prefix + "question_number", ""
                ).strip(),
                "question_type": request.POST.get(
                    prefix + "question_type", "mcq"
                ).strip(),
                "question_text": request.POST.get(
                    prefix + "question_text", ""
                ).strip(),
                "explanation": request.POST.get(
                    prefix + "explanation", ""
                ).strip(),
                "marks": request.POST.get(
                    prefix + "marks", "1"
                ).strip(),
                "order": request.POST.get(
                    prefix + "order",
                    str(last_order + index + 1),
                ).strip(),
                "choices": [
                    request.POST.get(
                        f"{prefix}choice_{choice_index}", ""
                    ).strip()
                    for choice_index in range(4)
                ],
                "correct_choice": request.POST.get(
                    prefix + "correct_choice", ""
                ).strip(),
                "published": (
                    prefix + "published" in request.POST
                ),
                "errors": [],
            }

            form_data.append(data)

            if data["question_type"] not in (
                "mcq",
                "theory",
                "practical",
            ):
                data["errors"].append(
                    "Select a valid question type."
                )
                continue

            if not data["question_text"]:
                data["errors"].append(
                    "Question text is required."
                )
                continue

            try:
                question_number = int(data["question_number"])
                marks = int(data["marks"])
                order = int(data["order"])
            except (TypeError, ValueError):
                data["errors"].append(
                    "Question number, marks and order must be valid numbers."
                )
                continue

            if question_number < 1:
                data["errors"].append(
                    "Question number must be greater than zero."
                )

            if marks < 1:
                data["errors"].append(
                    "Marks must be at least 1."
                )

            if order < 0:
                data["errors"].append(
                    "Order cannot be negative."
                )

            if question_number in used_question_numbers:
                data["errors"].append(
                    f"Question number {question_number} appears more than once in this batch."
                )
            else:
                used_question_numbers.add(question_number)

            # Prevent duplicate question numbers already in this resource.
            if resource.questions.filter(
                question_number=question_number,
            ).exists():
                data["errors"].append(
                    f"Question number {question_number} already exists in this resource."
                )

            correct_choice_index = None

            if data["question_type"] == "mcq":
                if any(not choice for choice in data["choices"]):
                    data["errors"].append(
                        "All four answer choices are required for an MCQ."
                    )

                if data["correct_choice"] not in (
                    "0",
                    "1",
                    "2",
                    "3",
                ):
                    data["errors"].append(
                        "Select exactly one correct answer."
                    )
                else:
                    correct_choice_index = int(
                        data["correct_choice"]
                    )

            if data["errors"]:
                continue

            image_file = request.FILES.get(
                prefix + "image"
            )

            question = ExamQuestion(
                resource=resource,
                question_number=question_number,
                question_type=data["question_type"],
                question_text=data["question_text"],
                explanation=data["explanation"],
                marks=marks,
                order=order,
                published=data["published"],
            )

            if image_file:
                question.image = image_file

            try:
                question.full_clean()
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field_errors in exc.message_dict.values():
                        data["errors"].extend(field_errors)
                else:
                    data["errors"].extend(exc.messages)

                continue

            validated_questions.append({
                "question": question,
                "choices": data["choices"],
                "correct_choice_index": correct_choice_index,
                "question_type": data["question_type"],
            })

        has_question_errors = any(
            data["errors"] for data in form_data
        )

        if not bulk_errors and not has_question_errors:
            try:
                with transaction.atomic():
                    for item in validated_questions:
                        question = item["question"]
                        question.save()

                        if item["question_type"] == "mcq":
                            for choice_index, choice_text in enumerate(
                                item["choices"]
                            ):
                                choice = ExamChoice(
                                    question=question,
                                    text=choice_text,
                                    is_correct=(
                                        choice_index
                                        == item["correct_choice_index"]
                                    ),
                                    order=choice_index + 1,
                                )

                                choice.full_clean()
                                choice.save()

            except ValidationError as exc:
                bulk_errors.extend(exc.messages)

            except IntegrityError:
                bulk_errors.append(
                    "The questions could not be saved because of a database conflict. "
                    "Check question numbers and try again."
                )

            else:
                messages.success(
                    request,
                    f"{len(validated_questions)} questions "
                    f"were added successfully to {resource.title}.",
                )

                return redirect(
                    "admin_dashboard:exam_questions",
                    resource_id=resource.id,
                )

    return render(
        request,
        "admin_dashboard/exam_question_bulk_form.html",
        {
            "resource": resource,
            "exam": resource.exam,
            "form_data": form_data,
            "bulk_errors": bulk_errors,
            "next_question_number": last_question_number + 1,
            "page_title": "Bulk Add Exam Questions",
            "page_subtitle": (
                f"Add multiple questions to {resource.title}."
            ),
        },
    )


# =========================================================
# EXAM QUESTION ANSWER CHOICES
# =========================================================

@admin_required
def exam_choices(request, question_id):
    question = get_object_or_404(
        ExamQuestion.objects.select_related(
            "resource",
            "resource__exam",
        ).prefetch_related("choices"),
        id=question_id,
    )

    choices = question.choices.order_by("order", "id")

    context = {
        "question": question,
        "resource": question.resource,
        "exam": question.resource.exam,
        "choices": choices,
        "choice_count": choices.count(),
        "correct_choice_count": choices.filter(
            is_correct=True,
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/exam_choices.html",
        context,
    )


@admin_required
def exam_choice_create(request, question_id):
    question = get_object_or_404(
        ExamQuestion.objects.select_related(
            "resource",
            "resource__exam",
        ),
        id=question_id,
    )

    if question.question_type != "mcq":
        messages.error(
            request,
            "Answer choices can only be added to multiple-choice questions.",
        )
        return redirect(
            "admin_dashboard:exam_question_detail",
            question_id=question.id,
        )

    if request.method == "POST":
        form = ExamChoiceForm(request.POST)

        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question

            try:
                choice.full_clean()

                with transaction.atomic():
                    if choice.is_correct:
                        question.choices.update(is_correct=False)

                    choice.save()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    "Answer choice created successfully.",
                )

                return redirect(
                    "admin_dashboard:exam_choices",
                    question_id=question.id,
                )
    else:
        form = ExamChoiceForm(
            initial={
                "order": question.choices.count() + 1,
            }
        )

    return render(
        request,
        "admin_dashboard/exam_choice_form.html",
        {
            "form": form,
            "question": question,
            "resource": question.resource,
            "exam": question.resource.exam,
            "page_title": "Add Answer Choice",
            "page_subtitle": (
                f"Add an answer option to Question "
                f"{question.question_number}."
            ),
            "form_action": "Create Choice",
            "is_edit": False,
        },
    )


@admin_required
def exam_choice_edit(request, choice_id):
    choice = get_object_or_404(
        ExamChoice.objects.select_related(
            "question",
            "question__resource",
            "question__resource__exam",
        ),
        id=choice_id,
    )

    question = choice.question

    if request.method == "POST":
        form = ExamChoiceForm(
            request.POST,
            instance=choice,
        )

        if form.is_valid():
            updated_choice = form.save(commit=False)

            try:
                updated_choice.full_clean()

                with transaction.atomic():
                    if updated_choice.is_correct:
                        question.choices.exclude(
                            id=updated_choice.id,
                        ).update(is_correct=False)

                    updated_choice.save()

            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, exc)

            else:
                messages.success(
                    request,
                    "Answer choice updated successfully.",
                )

                return redirect(
                    "admin_dashboard:exam_choices",
                    question_id=question.id,
                )
    else:
        form = ExamChoiceForm(instance=choice)

    return render(
        request,
        "admin_dashboard/exam_choice_form.html",
        {
            "form": form,
            "choice": choice,
            "question": question,
            "resource": question.resource,
            "exam": question.resource.exam,
            "page_title": "Edit Answer Choice",
            "page_subtitle": (
                f"Update an option for Question "
                f"{question.question_number}."
            ),
            "form_action": "Save Changes",
            "is_edit": True,
        },
    )


@admin_required
def exam_choice_delete(request, choice_id):
    choice = get_object_or_404(
        ExamChoice.objects.select_related("question"),
        id=choice_id,
    )

    question_id = choice.question_id

    if request.method == "POST":
        choice.delete()

        messages.success(
            request,
            "Answer choice deleted successfully.",
        )

    return redirect(
        "admin_dashboard:exam_choices",
        question_id=question_id,
    )

# ============================================================
# ASSESSMENTS
# ============================================================

from django.db.models import Count

@admin_required
def assessment_attempts(request):
    attempts = (
        QuizAttempt.objects
        .select_related("student", "quiz")
        .order_by("-started_at")
    )

    pending_answers = (
        Answer.objects
        .filter(reviewed=False)
        .exclude(question__question_type="objective")
    )

    context = {
        "attempts": attempts,

        # Stats for the cards
        "total_attempts": attempts.count(),
        "passed_attempts": attempts.filter(passed=True).count(),
        "failed_attempts": attempts.filter(passed=False).count(),
        "pending_reviews": pending_answers.count(),

        # Sidebar highlight
        "nav_active": "assessments",
    }

    return render(
        request,
        "admin_dashboard/assessment_attempts.html",
        context,
    )

@admin_required
def attempt_detail(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("student", "quiz"),
        id=attempt_id,
    )

    answers = (
        Answer.objects
        .filter(attempt=attempt)
        .select_related("question", "selected_choice", "reviewed_by")
        .order_by("question__order", "id")
    )

    objective_answers = answers.filter(
        question__question_type="objective"
    ).count()

    theory_answers = answers.filter(
        question__question_type="theory"
    ).count()

    practical_answers = answers.filter(
        question__question_type="practical"
    ).count()

    pending_manual_reviews = (
        answers
        .filter(reviewed=False)
        .exclude(question__question_type="objective")
        .count()
    )

    context = {
        "attempt": attempt,
        "answers": answers,

        # For the summary cards
        "objective_answers": objective_answers,
        "theory_answers": theory_answers,
        "practical_answers": practical_answers,
        "pending_manual_reviews": pending_manual_reviews,

        # Sidebar highlight
        "nav_active": "assessments",
    }

    return render(
        request,
        "admin_dashboard/attempt_detail.html",
        context,
    )

@admin_required
def pending_reviews(request):
    answers = (
        Answer.objects
        .filter(
            reviewed=False
        )
        .exclude(
            question__question_type="objective"
        )
        .select_related(
            "attempt",
            "attempt__student",
            "attempt__quiz",
            "question",
        )
        .order_by(
            "attempt__started_at",
            "question__order",
        )
    )

    return render(
        request,
        "admin_dashboard/pending_reviews.html",
        {
            "answers": answers,
        },
    )

@admin_required
def review_attempt(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related(
            "student",
            "quiz",
        ),
        id=attempt_id,
    )

    answers = list(
        Answer.objects
        .filter(attempt=attempt)
        .select_related(
            "question",
            "selected_choice",
        )
        .order_by(
            "question__order",
            "id",
        )
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                total_score = 0.0

                for answer in answers:
                    points_field = f"points_{answer.id}"
                    feedback_field = f"feedback_{answer.id}"
                    correct_field = f"correct_{answer.id}"

                    raw_points = (
                        request.POST
                        .get(points_field, "")
                        .strip()
                    )

                    feedback = (
                        request.POST
                        .get(feedback_field, "")
                        .strip()
                    )

                    is_correct = (
                        request.POST.get(correct_field) == "on"
                    )

                    if raw_points == "":
                        points = 0.0
                    else:
                        points = float(raw_points)

                    max_points = float(
                        answer.question.points or 0
                    )

                    if points < 0:
                        points = 0.0

                    if points > max_points:
                        points = max_points

                    answer.points_earned = points
                    answer.feedback = feedback
                    answer.is_correct = is_correct
                    answer.reviewed = True
                    answer.reviewed_at = timezone.now()
                    answer.reviewed_by = request.user

                    answer.save(
                        update_fields=[
                            "points_earned",
                            "feedback",
                            "is_correct",
                            "reviewed",
                            "reviewed_at",
                            "reviewed_by",
                        ]
                    )

                    total_score += points

                total_possible = sum(
                    float(answer.question.points or 0)
                    for answer in answers
                )

                attempt.score = total_score

                if total_possible > 0:
                    attempt.percentage = (
                        total_score / total_possible
                    ) * 100
                else:
                    attempt.percentage = 0

                pass_mark = float(
                    attempt.quiz.pass_mark or 0
                )

                attempt.passed = (
                    attempt.percentage >= pass_mark
                )

                attempt.save(
                    update_fields=[
                        "score",
                        "percentage",
                        "passed",
                    ]
                )

            messages.success(
                request,
                "Attempt reviewed and result updated successfully.",
            )

            return redirect(
                "admin_dashboard:attempt_detail",
                attempt_id=attempt.id,
            )

        except (
            ValueError,
            IntegrityError,
        ) as exc:
            messages.error(
                request,
                f"Unable to save the review: {exc}",
            )

    return render(
        request,
        "admin_dashboard/review_attempt.html",
        {
            "attempt": attempt,
            "answers": answers,
        },
    )

#============================================================
# PRICING OVERVIEW AND PRICE EDITING
# ============================================================

class PriceUpdateForm(forms.Form):
    price = forms.DecimalField(
        label="Price (₦)",
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter price, or leave blank for free",
                "min": "0",
                "step": "0.01",
            }
        ),
    )


@admin_required
def pricing_overview(request):
    """Review prices and edit individual prices from the admin dashboard."""

    # Only these approved model types can be edited through this view.
    price_models = {
        "school_class": SchoolClass,
        "subject": Subject,
        "course": Course,
        "exam": Exam,
        "exam_subject": ExamSubject,
        "exam_resource": ExamResource,
        "tech_course": TechCourse,
        "tech_module": TechModule,
        "tech_lesson": TechLesson,
        "tech_lesson_resource": TechLessonResource,
    }

    edit_type = request.GET.get("edit_type", "")
    edit_id = request.GET.get("edit_id", "")
    edit_item = None
    price_form = None

    # Handle an edit request only when its model type is permitted.
    if edit_type and edit_type not in price_models:
        messages.error(request, "Invalid pricing item.")
        return redirect("admin_dashboard:pricing_overview")

    if edit_type:
        model = price_models[edit_type]
        edit_item = get_object_or_404(model, pk=edit_id)

        if request.method == "POST":
            price_form = PriceUpdateForm(request.POST)

            if price_form.is_valid():
                new_price = price_form.cleaned_data["price"]
                price_field = model._meta.get_field("price")

                # School classes, subjects, and courses use zero for free.
                # Exam and Tech models allow a blank/None price.
                if new_price is None and not price_field.null:
                    new_price = 0

                edit_item.price = new_price
                edit_item.save(update_fields=["price"])

                messages.success(
                    request,
                    f"Price for '{edit_item}' updated successfully.",
                )

                return redirect("admin_dashboard:pricing_overview")
        else:
            price_form = PriceUpdateForm(
                initial={"price": edit_item.price}
            )

    pricing_sections = [
        {
            "title": "School Classes",
            "description": "Packages for complete school classes.",
            "items": list(SchoolClass.objects.all()),
            "name_field": "name",
            "model_key": "school_class",
        },
        {
            "title": "School Subjects",
            "description": "Individual school subjects.",
            "items": list(Subject.objects.all()),
            "name_field": "name",
            "model_key": "subject",
        },
        {
            "title": "Independent Courses",
            "description": "Courses outside the school-class structure.",
            "items": list(Course.objects.all()),
            "name_field": "title",
            "model_key": "course",
        },
        {
            "title": "Exam Packages",
            "description": "Complete examination packages.",
            "items": list(Exam.objects.all()),
            "name_field": "name",
            "model_key": "exam",
        },
        {
            "title": "Exam Subjects",
            "description": "Individual subjects within an examination.",
            "items": list(
                ExamSubject.objects.select_related("exam").all()
            ),
            "name_field": "name",
            "model_key": "exam_subject",
        },
        {
            "title": "Exam Resources",
            "description": "Past questions, solutions, and other resources.",
            "items": list(
                ExamResource.objects.select_related(
                    "exam", "subject", "year"
                ).all()
            ),
            "name_field": "title",
            "model_key": "exam_resource",
        },
        {
            "title": "Tech Courses",
            "description": "Complete digital-skills courses.",
            "items": list(
                TechCourse.objects.select_related("category").all()
            ),
            "name_field": "title",
            "model_key": "tech_course",
        },
        {
            "title": "Tech Modules",
            "description": "Individual modules within Tech courses.",
            "items": list(
                TechModule.objects.select_related("course").all()
            ),
            "name_field": "title",
            "model_key": "tech_module",
        },
        {
            "title": "Tech Lessons",
            "description": "Individual lessons within Tech modules.",
            "items": list(
                TechLesson.objects.select_related(
                    "module", "module__course"
                ).all()
            ),
            "name_field": "title",
            "model_key": "tech_lesson",
        },
        {
            "title": "Tech Lesson Resources",
            "description": "Downloadable resources for Tech lessons.",
            "items": list(
                TechLessonResource.objects.select_related("lesson").all()
            ),
            "name_field": "title",
            "model_key": "tech_lesson_resource",
        },
    ]

    total_items = 0
    paid_items = 0
    free_items = 0
    paid_value = 0

    for section in pricing_sections:
        section_paid = 0
        section_free = 0

        for item in section["items"]:
            price = item.price
            item.display_price = price
            item.display_price_formatted = (
                f"{price:,.2f}" if price is not None else "0.00"
            )
            item.is_paid = price is not None and price > 0
            item.is_free = not item.is_paid

            if item.is_paid:
                section_paid += 1
                paid_value += price
            else:
                section_free += 1

        section["total_count"] = len(section["items"])
        section["paid_count"] = section_paid
        section["free_count"] = section_free

        total_items += section["total_count"]
        paid_items += section_paid
        free_items += section_free

    context = {
        "pricing_sections": pricing_sections,
        "total_items": total_items,
        "paid_items": paid_items,
        "free_items": free_items,
        "paid_value": paid_value,
        "paid_value_formatted": f"{paid_value:,.2f}",
        "edit_item": edit_item,
        "edit_type": edit_type,
        "price_form": price_form,
    }

    return render(
        request,
        "admin_dashboard/pricing_overview.html",
        context,
    )



# ==============================================================
# RESOURCE GENERATOR (CSV → ExamResource + ExamQuestion + ExamChoice)
# ==============================================================
#
# Two modes:
#
#   NEW       — creates a fresh ExamResource, then imports all questions
#   EXISTING  — appends imported questions to an existing ExamResource
#
# CSV schema (one row = one question with four options):
#
#   question_number,question_text,option_a,option_b,option_c,option_d,correct,explanation,marks
#   1,What is 2+2?,3,4,5,6,B,Two plus two equals four,1
#   2,Capital of Nigeria?,Lagos,Abuja,Kano,Ibadan,B,Abuja is the capital,1
#
# "correct" is A, B, C, or D (case-insensitive).
# "marks" is optional; defaults to 1.
# "explanation" is optional.
#
# All-or-nothing: any row with an error rolls back the entire import.
# ==============================================================

@admin_required
def resource_generator(request):
    import csv
    import io
    from decimal import Decimal

    from django.db import transaction
    from django.utils import timezone

    # ---------- helpers ----------

    def _parse_bool(value):
        return str(value).strip().lower() in (
            "1", "true", "yes", "y", "on",
        )

    def _parse_int(value, default=1):
        try:
            return int(str(value).strip() or default)
        except (TypeError, ValueError):
            return default

    def _clean(value):
        return str(value or "").strip()

    # ---------- available exams ----------

    exams = Exam.objects.all().order_by("order", "name")
    existing_resources = (
        ExamResource.objects
        .select_related("exam", "subject", "year")
        .order_by("-id", "title")
    )

    # ---------- handle upload ----------

    if request.method == "POST":

        import_result = None
        import_errors = []

        mode = request.POST.get("mode", "new")

        selected_exam_id = request.POST.get("exam") or None
        selected_resource_id = request.POST.get("resource") or None

        # NEW-mode extras
        new_title = _clean(request.POST.get("new_title"))
        new_subject_id = request.POST.get("new_subject") or None
        new_year_id = request.POST.get("new_year") or None
        new_resource_type = (
            request.POST.get("new_resource_type") or "past_questions"
        )
        new_price_raw = _clean(request.POST.get("new_price"))
        new_published = request.POST.get("new_published") == "on"

        uploaded = request.FILES.get("csv_file")

        # ---------- validation ----------

        if not uploaded:
            import_errors.append("Please select a CSV file to upload.")

        elif not uploaded.name.lower().endswith(".csv"):
            import_errors.append("File must have a .csv extension.")

        if mode == "new":
            if not selected_exam_id:
                import_errors.append("Please choose an examination.")
            if not new_title:
                import_errors.append("Please provide a resource title.")
            if not new_subject_id:
                import_errors.append("Please choose a subject.")
            if not new_year_id:
                import_errors.append("Please choose a year.")

        elif mode == "existing":
            if not selected_resource_id:
                import_errors.append("Please choose an existing resource.")

        else:
            import_errors.append("Invalid import mode.")

        # ---------- parse and import ----------

        if not import_errors:

            try:
                # decode the file
                raw = uploaded.read()
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1")

                reader = csv.DictReader(io.StringIO(text))

                required_columns = {
                    "question_number",
                    "question_text",
                    "option_a",
                    "option_b",
                    "option_c",
                    "option_d",
                    "correct",
                }
                missing = required_columns - set(reader.fieldnames or [])

                if missing:
                    raise ValueError(
                        "CSV is missing required column(s): "
                        + ", ".join(sorted(missing))
                    )

                rows = list(reader)

                if not rows:
                    raise ValueError("CSV file is empty.")

                # ---- resolve resource ----
                if mode == "existing":
                    resource = get_object_or_404(
                        ExamResource, id=selected_resource_id
                    )
                else:
                    exam = get_object_or_404(Exam, id=selected_exam_id)
                    subject = get_object_or_404(
                        ExamSubject, id=new_subject_id, exam=exam
                    )
                    year = get_object_or_404(
                        ExamYear, id=new_year_id, exam=exam
                    )

                    price = None
                    if new_price_raw:
                        price = Decimal(new_price_raw)

                    resource = ExamResource(
                        exam=exam,
                        subject=subject,
                        year=year,
                        resource_type=new_resource_type,
                        title=new_title,
                        price=price,
                        published=new_published,
                    )
                    resource.full_clean()
                    resource.save()

                # ---- questions + choices ----
                imported_questions = 0
                imported_choices = 0
                start_order = resource.questions.count()

                with transaction.atomic():
                    for index, row in enumerate(rows, start=1):
                        qn_raw = _clean(row.get("question_number"))
                        qn = _parse_int(qn_raw, default=index)

                        qtext = _clean(row.get("question_text"))
                        if not qtext:
                            raise ValueError(
                                f"Row {index}: question_text is empty."
                            )

                        correct = _clean(row.get("correct")).upper()
                        if correct not in ("A", "B", "C", "D"):
                            raise ValueError(
                                f"Row {index}: 'correct' must be A, B, C or D "
                                f"(got '{correct}')."
                            )

                        marks = _parse_int(row.get("marks"), default=1)
                        explanation = _clean(row.get("explanation"))

                        question = ExamQuestion.objects.create(
                            resource=resource,
                            question_number=qn,
                            question_type="mcq",
                            question_text=qtext,
                            explanation=explanation,
                            marks=marks,
                            published=True,
                            order=start_order + index,
                        )
                        imported_questions += 1

                        option_fields = [
                            ("A", "option_a"),
                            ("B", "option_b"),
                            ("C", "option_c"),
                            ("D", "option_d"),
                        ]

                        for letter, field in option_fields:
                            choice_text = _clean(row.get(field))
                            if not choice_text:
                                raise ValueError(
                                    f"Row {index}: {field} is empty."
                                )
                            ExamChoice.objects.create(
                                question=question,
                                text=choice_text,
                                is_correct=(letter == correct),
                                order="ABCD".index(letter) + 1,
                            )
                            imported_choices += 1

                import_result = {
                    "resource_id": resource.id,
                    "resource_title": resource.title,
                    "exam_name": resource.exam.name,
                    "subject_name": resource.subject.name,
                    "year": resource.year.year,
                    "questions": imported_questions,
                    "choices": imported_choices,
                    "mode": mode,
                }

            except ValueError as exc:
                import_errors.append(str(exc))
            except Exception as exc:
                import_errors.append(
                    f"Unexpected error: {exc}"
                )

        # ---------- render result ----------

        if import_result:
            messages.success(
                request,
                (
                    f"Imported {import_result['questions']} question(s) "
                    f"and {import_result['choices']} choice(s) "
                    f"into '{import_result['resource_title']}'."
                ),
            )

        return render(
            request,
            "admin_dashboard/resource_generator.html",
            {
                "exams": exams,
                "existing_resources": existing_resources,
                "import_result": import_result,
                "import_errors": import_errors,
                "mode": mode,
            },
        )

    # ---------- GET: render empty form ----------

    return render(
        request,
        "admin_dashboard/resource_generator.html",
        {
            "exams": exams,
            "existing_resources": existing_resources,
            "import_result": None,
            "import_errors": [],
            "mode": "new",
        },
    )


# ============================================================
# PLAY & LEARN — GAMES MANAGEMENT
# ============================================================

@admin_required
def play_games(request):
    """Display and filter all Play & Learn games."""

    games = PlayGame.objects.all().order_by("order", "name")

    search = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        games = games.filter(name__icontains=search)

    if category:
        games = games.filter(category=category)

    if status == "published":
        games = games.filter(is_published=True)
    elif status == "unpublished":
        games = games.filter(is_published=False)

    context = {
        "games": games,
        "search": search,
        "selected_category": category,
        "selected_status": status,
        "categories": PlayGame.Category.choices,
        "total_games": PlayGame.objects.count(),
        "published_games": PlayGame.objects.filter(
            is_published=True
        ).count(),
        "unpublished_games": PlayGame.objects.filter(
            is_published=False
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/play_games.html",
        context,
    )


@admin_required
def play_game_create(request):
    """Create a new Play & Learn game."""

    if request.method == "POST":
        form = PlayGameForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            game = form.save()

            messages.success(
                request,
                f"Game '{game.name}' created successfully.",
            )

            return redirect(
                "admin_dashboard:play_game_detail",
                game_id=game.pk,
            )
    else:
        form = PlayGameForm()

    return render(
        request,
        "admin_dashboard/play_game_form.html",
        {
            "form": form,
            "page_title": "Create Game",
            "form_title": "Add a New Game",
            "submit_text": "Create Game",
        },
    )


@admin_required
def play_game_detail(request, game_id):
    """Display game information and its recent attempts."""

    game = get_object_or_404(
        PlayGame,
        pk=game_id,
    )

    attempts = (
        GameAttempt.objects
        .filter(game=game)
        .select_related("user")
        .order_by("-started_at")
    )

    context = {
        "game": game,
        "attempts": attempts[:30],
        "total_attempts": attempts.count(),
        "completed_attempts": attempts.filter(
            status="completed"
        ).count(),
    }

    return render(
        request,
        "admin_dashboard/play_game_detail.html",
        context,
    )


@admin_required
def play_game_edit(request, game_id):
    """Edit an existing Play & Learn game."""

    game = get_object_or_404(
        PlayGame,
        pk=game_id,
    )

    if request.method == "POST":
        form = PlayGameForm(
            request.POST,
            request.FILES,
            instance=game,
        )

        if form.is_valid():
            game = form.save()

            messages.success(
                request,
                f"Game '{game.name}' updated successfully.",
            )

            return redirect(
                "admin_dashboard:play_game_detail",
                game_id=game.pk,
            )
    else:
        form = PlayGameForm(instance=game)

    return render(
        request,
        "admin_dashboard/play_game_form.html",
        {
            "form": form,
            "game": game,
            "page_title": "Edit Game",
            "form_title": f"Edit {game.name}",
            "submit_text": "Save Changes",
        },
    )


@admin_required
def play_game_delete(request, game_id):
    """Delete a game after explicit POST confirmation."""

    game = get_object_or_404(
        PlayGame,
        pk=game_id,
    )

    if request.method == "POST":
        game_name = game.name

        try:
            game.delete()

            messages.success(
                request,
                f"Game '{game_name}' deleted successfully.",
            )

        except IntegrityError:
            messages.error(
                request,
                "This game could not be deleted because related records "
                "prevent its removal.",
            )

        return redirect("admin_dashboard:play_games")

    return redirect(
        "admin_dashboard:play_game_detail",
        game_id=game.pk,
    )
