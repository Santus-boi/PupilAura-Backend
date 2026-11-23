
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from assessments.models import Quiz, Question, Choice

from learning.models import Lesson, Week

from exam_prep.models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamQuestion,
    ExamChoice,
)

from tech.models import (
    TechCategory,
    TechCourse,
    TechModule,
    TechLesson,
)

from ai_services.client import AIClientError
from ai_services.lesson_generator import generate_lesson_content
from ai_services.quiz_generator import generate_quiz_questions
from ai_services.exam_question_generator import generate_exam_questions
from ai_services.exam_resource_generator import generate_exam_resource
from ai_services.tech_course_generator import generate_tech_course
from ai_services.tech_module_generator import generate_tech_module
from ai_services.tech_lesson_generator import generate_tech_lesson

from .views import admin_required


logger = logging.getLogger(__name__)


# =========================================================
# SHARED HELPERS
# =========================================================

def _next_lesson_order(week):
    highest_order = (
        week.lessons.aggregate(highest=Max("order"))["highest"] or 0
    )
    return highest_order + 1


def _render_ai_lesson_form(request, generated_lesson=None, form_data=None):
    return render(
        request,
        "admin_dashboard/ai_lesson_generator.html",
        {
            "generated_lesson": generated_lesson,
            "form_data": form_data or {},
            "nav_active": "ai_tools",
        },
    )


def _render_ai_selection_picker(
    request,
    title,
    description,
    records,
    empty_title,
    empty_message,
    empty_url,
    empty_label,
):
    return render(
        request,
        "admin_dashboard/ai_selection_picker.html",
        {
            "selection_title": title,
            "selection_description": description,
            "records": records,
            "empty_title": empty_title,
            "empty_message": empty_message,
            "empty_url": empty_url,
            "empty_label": empty_label,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI EXAM QUESTION GENERATOR
# =========================================================

@admin_required
def ai_exam_question_generator(request, resource_id):
    resource = get_object_or_404(
        ExamResource.objects.select_related(
            "exam",
            "subject",
            "year",
        ),
        id=resource_id,
    )

    # Only Past Questions and Mock Exams support generated questions.
    if resource.resource_type not in ("past_questions", "mock_exam"):
        messages.error(
            request,
            "AI question generation is only available for Past Questions "
            "and Mock Exam resources.",
        )
        return redirect(
            "admin_dashboard:exam_resource_detail",
            resource_id=resource.id,
        )

    if request.method == "POST":
        try:
            count = int(request.POST.get("count") or 10)
        except (TypeError, ValueError):
            count = 10

        if not 1 <= count <= 60:
            messages.error(
                request,
                "Question count must be between 1 and 60.",
            )
            return render(
                request,
                "admin_dashboard/ai_exam_question_generator.html",
                {
                    "resource": resource,
                    "exam": resource.exam,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        difficulty = (
            request.POST.get("difficulty") or "standard"
        ).strip()

        try:
            payload = generate_exam_questions(
                user=request.user,
                exam_name=resource.exam.name,
                subject_name=resource.subject.name,
                year=resource.year.year,
                count=count,
                difficulty=difficulty,
            )

        except AIClientError as exc:
            logger.exception(
                "AI exam question generation failed"
            )
            messages.error(
                request,
                f"AI generation failed: {exc}",
            )
            return render(
                request,
                "admin_dashboard/ai_exam_question_generator.html",
                {
                    "resource": resource,
                    "exam": resource.exam,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        questions_data = payload.get("questions", [])

        if not questions_data:
            messages.error(
                request,
                "The AI did not return any questions. Try again.",
            )
            return redirect(
                "admin_dashboard:ai_exam_question_generator",
                resource_id=resource.id,
            )

        try:
            with transaction.atomic():
                # Continue numbering after the highest existing question.
                highest_question_number = (
                    resource.questions.aggregate(
                        highest=Max("question_number")
                    )["highest"] or 0
                )

                # Continue ordering after the highest existing order.
                highest_order = (
                    resource.questions.aggregate(
                        highest=Max("order")
                    )["highest"] or 0
                )

                for index, question_data in enumerate(
                    questions_data,
                    start=1,
                ):
                    question_number = highest_question_number + index

                    question = ExamQuestion(
                        resource=resource,
                        question_number=question_number,
                        question_type="mcq",
                        question_text=question_data["question_text"],
                        explanation=question_data["explanation"],
                        marks=question_data["marks"],
                        published=False,
                        order=highest_order + index,
                    )

                    question.full_clean()
                    question.save()

                    for choice_index, letter in enumerate(
                        ("A", "B", "C", "D"),
                        start=1,
                    ):
                        option_key = f"option_{letter.lower()}"

                        choice = ExamChoice(
                            question=question,
                            text=question_data[option_key],
                            is_correct=(
                                letter == question_data["correct"]
                            ),
                            order=choice_index,
                        )

                        choice.full_clean()
                        choice.save()

        except Exception as exc:
            logger.exception(
                "Failed to persist AI exam questions"
            )
            messages.error(
                request,
                f"Failed to save generated questions: {exc}",
            )
            return redirect(
                "admin_dashboard:exam_questions",
                resource_id=resource.id,
            )

        messages.success(
            request,
            f"{len(questions_data)} AI-generated draft questions "
            f"were added to '{resource.title}'. "
            "Review them before publishing.",
        )

        return redirect(
            "admin_dashboard:exam_questions",
            resource_id=resource.id,
        )

    return render(
        request,
        "admin_dashboard/ai_exam_question_generator.html",
        {
            "resource": resource,
            "exam": resource.exam,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI EXAM RESOURCE GENERATOR
# =========================================================

@admin_required
def ai_exam_resource_generator(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    subjects = exam.subjects.all()
    years = exam.years.all()

    allowed_resource_types = {
        "past_questions",
        "solutions",
        "lesson",
        "practical",
        "mock_exam",
        "revision",
    }

    topic_required_types = {
        "lesson",
        "practical",
        "revision",
    }

    def render_generator(form_data=None):
        return render(
            request,
            "admin_dashboard/ai_exam_resource_generator.html",
            {
                "exam": exam,
                "subjects": subjects,
                "years": years,
                "nav_active": "ai_tools",
                "form_data": form_data,
            },
        )

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        year_id = request.POST.get("year")

        resource_type = (
            request.POST.get("resource_type") or "lesson"
        ).strip().lower()

        topic = (request.POST.get("topic") or "").strip()

        difficulty = (
            request.POST.get("difficulty") or "standard"
        ).strip().lower()

        # -------------------------------------------------
        # Validate resource type
        # -------------------------------------------------

        if resource_type not in allowed_resource_types:
            messages.error(
                request,
                "Invalid resource type selected.",
            )
            return render_generator(request.POST)

        # -------------------------------------------------
        # Validate required fields
        # -------------------------------------------------

        if not subject_id or not year_id:
            messages.error(
                request,
                "Please select an examination subject and year.",
            )
            return render_generator(request.POST)

        if resource_type in topic_required_types and not topic:
            messages.error(
                request,
                "A topic is required for this resource type.",
            )
            return render_generator(request.POST)

        # -------------------------------------------------
        # Validate subject and year
        # -------------------------------------------------

        try:
            subject = exam.subjects.get(id=subject_id)
            year = exam.years.get(id=year_id)

        except (ExamSubject.DoesNotExist, ExamYear.DoesNotExist):
            messages.error(
                request,
                "Invalid subject or year for this examination.",
            )
            return render_generator(request.POST)

        # -------------------------------------------------
        # Determine generation topic
        # -------------------------------------------------

        generation_topic = topic or "the full subject syllabus"

        # -------------------------------------------------
        # Generate resource
        # -------------------------------------------------

        try:
            payload = generate_exam_resource(
                user=request.user,
                exam_name=exam.name,
                subject_name=subject.name,
                year=year.year,
                resource_type=resource_type,
                topic=generation_topic,
                difficulty=difficulty,
            )

        except AIClientError as exc:
            logger.exception(
                "AI exam resource generation failed."
            )

            messages.error(
                request,
                f"AI generation failed: {exc}",
            )

            return render_generator(request.POST)

        # -------------------------------------------------
        # Save resource and generated questions atomically
        # -------------------------------------------------

        try:
            with transaction.atomic():

                resource = ExamResource(
                    exam=exam,
                    subject=subject,
                    year=year,
                    resource_type=resource_type,
                    title=payload["title"],
                    description=payload["description"],
                    content=payload["content"],
                    structured_content=payload.get(
                        "structured_content",
                        {},
                    ),
                    published=False,
                )

                resource.full_clean()
                resource.save()

                questions_data = payload.get("questions", [])

                for index, question_data in enumerate(
                    questions_data,
                    start=1,
                ):
                    question = ExamQuestion(
                        resource=resource,
                        question_number=question_data["question_number"],
                        question_type=question_data["question_type"],
                        question_text=question_data["question_text"],
                        correct_answer=question_data["correct_answer"],
                        solution=question_data["solution"],
                        explanation=question_data["explanation"],
                        marks=question_data["marks"],
                        published=False,
                        order=index,
                    )

                    question.full_clean()
                    question.save()

                    for choice_index, choice_data in enumerate(
                        question_data["choices"],
                        start=1,
                    ):
                        choice = ExamChoice(
                            question=question,
                            text=choice_data["text"],
                            is_correct=choice_data["is_correct"],
                            order=choice_index,
                        )

                        choice.full_clean()
                        choice.save()

        except Exception as exc:
            logger.exception(
                "Failed to save AI-generated exam resource."
            )

            messages.error(
                request,
                f"Failed to save generated resource: {exc}",
            )

            return redirect(
                "admin_dashboard:exam_resources",
                exam_id=exam.id,
            )

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        if questions_data:
            success_message = (
                f"Draft resource '{resource.title}' created "
                f"with {len(questions_data)} generated questions."
            )
        else:
            success_message = (
                f"Draft resource '{resource.title}' created."
            )

        messages.success(
            request,
            success_message + " Review before publishing.",
        )

        return redirect(
            "admin_dashboard:exam_resource_detail",
            resource_id=resource.id,
        )

    return render_generator()


# =========================================================
# AI TECH COURSE GENERATOR
# =========================================================

@admin_required
def ai_tech_course_generator(request):
    categories = TechCategory.objects.all().order_by("order", "name")

    if request.method == "POST":
        category_id = request.POST.get("category")
        topic = (request.POST.get("topic") or "").strip()
        audience = (request.POST.get("audience") or "beginners").strip()
        difficulty = (
            request.POST.get("difficulty") or "standard"
        ).strip()

        try:
            length = int(request.POST.get("length") or 6)
        except (TypeError, ValueError):
            length = 6

        if not category_id or not topic:
            messages.error(request, "Category and topic are required.")
            return render(
                request,
                "admin_dashboard/ai_tech_course_generator.html",
                {
                    "categories": categories,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        category = get_object_or_404(TechCategory, id=category_id)

        try:
            payload = generate_tech_course(
                user=request.user,
                category=category.name,
                topic=topic,
                audience=audience,
                difficulty=difficulty,
                length=length,
            )
        except AIClientError as exc:
            logger.exception("AI tech course generation failed")
            messages.error(request, f"AI generation failed: {exc}")
            return render(
                request,
                "admin_dashboard/ai_tech_course_generator.html",
                {
                    "categories": categories,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        module_titles = payload.get("module_titles", [])

        try:
            with transaction.atomic():
                course = TechCourse.objects.create(
                    category=category,
                    title=payload["title"],
                    description=payload["description"],
                    price=None,
                    published=False,
                )

                for i, module_title in enumerate(module_titles, start=1):
                    TechModule.objects.create(
                        course=course,
                        title=module_title,
                        description="",
                        order=i,
                        published=False,
                    )

        except Exception as exc:
            logger.exception("Failed to persist AI tech course")
            messages.error(
                request,
                f"Failed to save generated course: {exc}",
            )
            return redirect("admin_dashboard:tech_courses")

        messages.success(
            request,
            f"Draft course '{course.title}' created with "
            f"{len(module_titles)} modules. Review before publishing.",
        )

        return redirect(
            "admin_dashboard:tech_course_detail",
            course_id=course.id,
        )

    return render(
        request,
        "admin_dashboard/ai_tech_course_generator.html",
        {
            "categories": categories,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI TECH MODULE GENERATOR
# =========================================================

@admin_required
def ai_tech_module_generator(request, course_id):
    course = get_object_or_404(TechCourse, id=course_id)

    if request.method == "POST":
        topic = (request.POST.get("topic") or "").strip()
        difficulty = (
            request.POST.get("difficulty") or "standard"
        ).strip()

        try:
            lesson_count = int(request.POST.get("lesson_count") or 4)
        except (TypeError, ValueError):
            lesson_count = 4

        if not topic:
            messages.error(request, "Module topic is required.")
            return render(
                request,
                "admin_dashboard/ai_tech_module_generator.html",
                {
                    "course": course,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        try:
            payload = generate_tech_module(
                user=request.user,
                course_title=course.title,
                topic=topic,
                lesson_count=lesson_count,
                difficulty=difficulty,
            )
        except AIClientError as exc:
            logger.exception("AI tech module generation failed")
            messages.error(request, f"AI generation failed: {exc}")
            return render(
                request,
                "admin_dashboard/ai_tech_module_generator.html",
                {
                    "course": course,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        lessons_data = payload.get("lessons", [])

        try:
            with transaction.atomic():
                module = TechModule.objects.create(
                    course=course,
                    title=payload["title"],
                    description=payload["description"],
                    order=course.modules.count() + 1,
                    published=False,
                )

                for i, lesson_data in enumerate(lessons_data, start=1):
                    TechLesson.objects.create(
                        module=module,
                        title=lesson_data["title"],
                        description=lesson_data["description"],
                        order=i,
                        published=False,
                    )

        except Exception as exc:
            logger.exception("Failed to persist AI tech module")
            messages.error(
                request,
                f"Failed to save generated module: {exc}",
            )
            return redirect(
                "admin_dashboard:tech_course_detail",
                course_id=course.id,
            )

        messages.success(
            request,
            f"Draft module '{module.title}' created with "
            f"{len(lessons_data)} lessons. Review before publishing.",
        )

        return redirect(
            "admin_dashboard:tech_module_detail",
            module_id=module.id,
        )

    return render(
        request,
        "admin_dashboard/ai_tech_module_generator.html",
        {
            "course": course,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI TECH LESSON GENERATOR
# =========================================================

@admin_required
def ai_tech_lesson_generator(request, module_id):
    module = get_object_or_404(
        TechModule.objects.select_related("course"),
        id=module_id,
    )

    if request.method == "POST":
        topic = (request.POST.get("topic") or "").strip()
        difficulty = (
            request.POST.get("difficulty") or "standard"
        ).strip()

        if not topic:
            messages.error(request, "Lesson topic is required.")
            return render(
                request,
                "admin_dashboard/ai_tech_lesson_generator.html",
                {
                    "module": module,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        try:
            payload = generate_tech_lesson(
                user=request.user,
                course_title=module.course.title,
                module_title=module.title,
                topic=topic,
                difficulty=difficulty,
            )
        except AIClientError as exc:
            logger.exception("AI tech lesson generation failed")
            messages.error(request, f"AI generation failed: {exc}")
            return render(
                request,
                "admin_dashboard/ai_tech_lesson_generator.html",
                {
                    "module": module,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        try:
            with transaction.atomic():
                lesson = TechLesson.objects.create(
                    module=module,
                    title=payload["title"],
                    description=payload["description"],
                    content=payload["content"],
                    practical=payload["practical"],
                    project=payload["project"],
                    order=module.lessons.count() + 1,
                    published=False,
                )

        except Exception as exc:
            logger.exception("Failed to persist AI tech lesson")
            messages.error(
                request,
                f"Failed to save generated lesson: {exc}",
            )
            return redirect(
                "admin_dashboard:tech_module_detail",
                module_id=module.id,
            )

        messages.success(
            request,
            f"Draft lesson '{lesson.title}' created. "
            "Review before publishing.",
        )

        return redirect(
            "admin_dashboard:tech_lesson_detail",
            lesson_id=lesson.id,
        )

    return render(
        request,
        "admin_dashboard/ai_tech_lesson_generator.html",
        {
            "module": module,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI CURRICULUM LESSON GENERATOR
# =========================================================

@admin_required
def ai_lesson_generator(request):
    generated_lesson = None
    form_data = request.POST if request.method == "POST" else {}

    if request.method == "POST":
        topic = (request.POST.get("topic") or "").strip()
        subject_name = (request.POST.get("subject") or "").strip()
        school_class_name = (
            request.POST.get("school_class") or ""
        ).strip()
        education_level_name = (
            request.POST.get("education_level") or ""
        ).strip()
        term_name = (request.POST.get("term") or "").strip()
        week_name = (request.POST.get("week") or "").strip()

        week_id = (
            request.POST.get("week_id")
            or request.GET.get("week_id")
            or ""
        ).strip()

        if not topic or not subject_name:
            messages.error(
                request,
                "Lesson topic and subject are required.",
            )
        else:
            selected_week = None
            invalid_week = False

            if week_id:
                try:
                    selected_week = Week.objects.select_related(
                        "term__subject__school_class__education_level"
                    ).get(pk=week_id)
                except (Week.DoesNotExist, ValueError, TypeError):
                    invalid_week = True
                    messages.error(
                        request,
                        "The selected curriculum week is invalid. "
                        "Select an existing week or leave the week ID empty "
                        "to generate a preview.",
                    )

            if not invalid_week:
                if selected_week:
                    subject = selected_week.term.subject
                    school_class = subject.school_class

                    subject_name = subject.name
                    term_name = selected_week.term.name
                    week_name = (
                        selected_week.title
                        or f"Week {selected_week.number}"
                    )

                    if school_class:
                        school_class_name = school_class.name

                        if school_class.education_level:
                            education_level_name = (
                                school_class.education_level.name
                            )

                try:
                    generated_lesson = generate_lesson_content(
                        user=request.user,
                        topic=topic,
                        subject=subject_name,
                        school_class=school_class_name or "Not specified",
                        education_level=(
                            education_level_name or "Not specified"
                        ),
                        term=term_name,
                        week=week_name,
                        level_description=(
                            education_level_name or "standard curriculum"
                        ),
                    )
                except AIClientError as exc:
                    logger.exception(
                        "AI curriculum lesson generation failed"
                    )
                    messages.error(
                        request,
                        f"AI generation failed: {exc}",
                    )
                except ValueError as exc:
                    messages.error(request, str(exc))
                else:
                    if selected_week:
                        try:
                            with transaction.atomic():
                                lesson = Lesson(
                                    week=selected_week,
                                    title=generated_lesson["title"],
                                    description=generated_lesson["description"],
                                    objectives=generated_lesson["objectives"],
                                    content=generated_lesson["content"],
                                    examples=generated_lesson["examples"],
                                    key_points=generated_lesson["key_points"],
                                    activity=generated_lesson["activity"],
                                    practical=generated_lesson["practical"],
                                    order=_next_lesson_order(selected_week),
                                    published=False,
                                )
                                lesson.full_clean()
                                lesson.save()

                        except Exception as exc:
                            logger.exception(
                                "Failed to save AI-generated curriculum lesson"
                            )
                            messages.error(
                                request,
                                f"Generated lesson could not be saved: {exc}",
                            )
                        else:
                            messages.success(
                                request,
                                f"Draft lesson '{lesson.title}' created. "
                                "Review before publishing.",
                            )
                            return redirect(
                                "admin_dashboard:lesson_detail",
                                lesson.id,
                            )
                    else:
                        messages.success(
                            request,
                            "Lesson generated successfully. "
                            "This is a preview and has not been saved.",
                        )

    return _render_ai_lesson_form(
        request,
        generated_lesson=generated_lesson,
        form_data=form_data,
    )


# =========================================================
# AI QUIZ GENERATOR — LESSON-SPECIFIC
# =========================================================

@admin_required
def ai_quiz_generator(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            "week__term__subject__school_class"
        ),
        id=lesson_id,
    )

    if request.method == "POST":
        try:
            count = int(request.POST.get("count") or 5)
            pass_mark = int(request.POST.get("pass_mark") or 50)
        except (TypeError, ValueError):
            messages.error(
                request,
                "Question count and pass mark must be valid numbers.",
            )
            return render(
                request,
                "admin_dashboard/ai_quiz_generator.html",
                {
                    "lesson": lesson,
                    "nav_active": "ai_tools",
                    "form_data": request.POST,
                },
            )

        if not 1 <= count <= 30:
            messages.error(
                request,
                "Question count must be between 1 and 30.",
            )
        elif not 0 <= pass_mark <= 100:
            messages.error(
                request,
                "Pass mark must be between 0 and 100.",
            )
        else:
            difficulty = (
                request.POST.get("difficulty") or "standard"
            ).strip()

            try:
                payload = generate_quiz_questions(
                    user=request.user,
                    lesson_title=lesson.title,
                    lesson_content=lesson.content,
                    count=count,
                    pass_mark=pass_mark,
                    difficulty=difficulty,
                )
            except AIClientError as exc:
                logger.exception("AI quiz generation failed")
                messages.error(request, f"AI generation failed: {exc}")
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                questions_data = payload.get("questions", [])

                try:
                    if not questions_data:
                        raise ValueError(
                            "The AI returned no quiz questions."
                        )

                    with transaction.atomic():
                        quiz = Quiz(
                            lesson=lesson,
                            title=payload["title"],
                            description=(
                                f"AI-generated multiple-choice quiz "
                                f"for {lesson.title}."
                            ),
                            pass_mark=payload["pass_mark"],
                            published=False,
                        )
                        quiz.full_clean()
                        quiz.save()

                        for question_index, question_data in enumerate(
                            questions_data,
                            start=1,
                        ):
                            choices_data = question_data["choices"]

                            if not choices_data:
                                raise ValueError(
                                    "An AI-generated question has no choices."
                                )

                            question = Question.objects.create(
                                quiz=quiz,
                                text=question_data["question_text"],
                                question_type="objective",
                                points=question_data["marks"],
                                order=question_index,
                            )

                            for choice_index, choice_data in enumerate(
                                choices_data,
                                start=1,
                            ):
                                Choice.objects.create(
                                    question=question,
                                    text=choice_data["text"],
                                    is_correct=choice_data["is_correct"],
                                    order=choice_index,
                                )

                        for question in quiz.questions.all():
                            if not question.choices.filter(
                                is_correct=True
                            ).exists():
                                raise ValueError(
                                    "A generated question has no correct answer."
                                )

                except Exception as exc:
                    logger.exception("Failed to persist AI-generated quiz")
                    messages.error(
                        request,
                        f"Quiz could not be saved: {exc}",
                    )
                else:
                    messages.success(
                        request,
                        f"Draft quiz '{quiz.title}' created with "
                        f"{len(questions_data)} questions. "
                        "Review before publishing.",
                    )
                    return redirect(
                        "admin_dashboard:lesson_detail",
                        lesson.id,
                    )

    return render(
        request,
        "admin_dashboard/ai_quiz_generator.html",
        {
            "lesson": lesson,
            "nav_active": "ai_tools",
            "form_data": (
                request.POST if request.method == "POST" else {}
            ),
        },
    )


# =========================================================
# AI QUIZ PICKER — EXISTING WORKFLOW
# =========================================================

@admin_required
def ai_quiz_picker(request):
    lessons = (
        Lesson.objects
        .filter(week__isnull=False)
        .select_related("week__term__subject__school_class")
        .order_by(
            "week__term__subject__name",
            "week__number",
            "order",
        )
    )

    return render(
        request,
        "admin_dashboard/ai_quiz_picker.html",
        {
            "lessons": lessons,
            "nav_active": "ai_tools",
        },
    )


# =========================================================
# AI SELECTION PICKERS
# =========================================================

@admin_required
def ai_lesson_week_picker(request):
    weeks = (
        Week.objects
        .select_related(
            "term__subject__school_class__education_level"
        )
        .order_by(
            "term__subject__name",
            "term__name",
            "number",
        )
    )

    records = []

    for week in weeks:
        subject = week.term.subject
        school_class = subject.school_class

        details = (
            f"{subject.name} · {week.term.name} · "
            f"{school_class.name if school_class else 'No class assigned'}"
        )

        records.append({
            "title": week.title or f"Week {week.number}",
            "details": details,
            "action_url": (
                f"{reverse('admin_dashboard:ai_lesson_generator')}"
                f"?week_id={week.id}"
            ),
        })

    return _render_ai_selection_picker(
        request,
        "Select a Curriculum Week",
        "Choose the week where the AI-generated lesson should be saved.",
        records,
        "No curriculum weeks found",
        "Create a curriculum week before generating a lesson.",
        reverse("admin_dashboard:weeks"),
        "Manage Weeks",
    )


@admin_required
def ai_exam_picker(request):
    exams = Exam.objects.all().order_by("name")

    records = [
        {
            "title": exam.name,
            "details": "Examination",
            "action_url": reverse(
                "admin_dashboard:ai_exam_resource_generator",
                args=[exam.id],
            ),
        }
        for exam in exams
    ]

    return _render_ai_selection_picker(
        request,
        "Select an Examination",
        "Choose the examination for which you want to generate a study resource.",
        records,
        "No examinations found",
        "Create an examination before generating an exam resource.",
        reverse("admin_dashboard:exams"),
        "Manage Examinations",
    )


@admin_required
def ai_exam_resource_picker(request):
    resources = (
        ExamResource.objects
        .select_related("exam", "subject", "year")
        .order_by("exam__name", "subject__name", "year__year", "title")
    )

    records = [
        {
            "title": resource.title,
            "details": (
                f"{resource.exam.name} · "
                f"{resource.subject.name} · "
                f"{resource.year.year}"
            ),
            "action_url": reverse(
                "admin_dashboard:ai_exam_question_generator",
                args=[resource.id],
            ),
        }
        for resource in resources
    ]

    return _render_ai_selection_picker(
        request,
        "Select an Exam Resource",
        "Choose an existing exam resource to generate questions from.",
        records,
        "No exam resources found",
        "Create an exam resource before generating questions.",
        reverse("admin_dashboard:exams"),
        "Manage Examinations",
    )


@admin_required
def ai_tech_course_picker(request):
    courses = (
        TechCourse.objects
        .select_related("category")
        .order_by("title")
    )

    records = [
        {
            "title": course.title,
            "details": (
                course.category.name
                if course.category
                else "Uncategorised course"
            ),
            "action_url": reverse(
                "admin_dashboard:ai_tech_module_generator",
                args=[course.id],
            ),
        }
        for course in courses
    ]

    return _render_ai_selection_picker(
        request,
        "Select a Technology Course",
        "Choose the course that should contain the new AI-generated module.",
        records,
        "No Technology courses found",
        "Create a Technology course before generating a module.",
        reverse("admin_dashboard:tech_courses"),
        "Manage Tech Courses",
    )


@admin_required
def ai_tech_module_picker(request):
    modules = (
        TechModule.objects
        .select_related("course")
        .order_by("course__title", "order", "title")
    )

    records = [
        {
            "title": module.title,
            "details": (
                f"{module.course.title} · Module {module.order}"
            ),
            "action_url": reverse(
                "admin_dashboard:ai_tech_lesson_generator",
                args=[module.id],
            ),
        }
        for module in modules
    ]

    return _render_ai_selection_picker(
        request,
        "Select a Technology Module",
        "Choose the module where the new AI-generated lesson should be added.",
        records,
        "No Technology modules found",
        "Create a Technology module before generating a lesson.",
        reverse("admin_dashboard:tech_modules"),
        "Manage Tech Modules",
    )


# =========================================================
# AI HUB
# =========================================================

@admin_required
def ai_index(request):
    return render(
        request,
        "admin_dashboard/ai_index.html",
        {
            "nav_active": "ai_tools",
        },
    )
