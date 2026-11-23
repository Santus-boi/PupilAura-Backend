from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .models import (
    Quiz,
    QuizAttempt,
    Answer,
    Question,
)

from enrollments.models import LessonProgress


@login_required
def quiz_detail(request, quiz_id):

    if request.user.role != "student":

        return redirect("/")

    quiz = get_object_or_404(
        Quiz.objects.select_related(
            "lesson",
            "lesson__week",
            "lesson__week__term",
            "lesson__week__term__subject",
            "lesson__week__term__subject__school_class",
            "lesson__week__term__subject__school_class__education_level",

            "week",
            "week__term",
            "week__term__subject",
            "week__term__subject__school_class",
            "week__term__subject__school_class__education_level",

            "term",
            "term__subject",
            "term__subject__school_class",
            "term__subject__school_class__education_level",
        ),
        id=quiz_id,
        published=True,
    )

    subject = None
    term = None
    week = None
    lesson = None

    assessment_type = "Assessment"

    # =========================================================
    # DETERMINE ASSESSMENT PARENT
    # =========================================================

    if quiz.lesson_id:

        lesson = quiz.lesson

        week = lesson.week

        term = week.term

        subject = term.subject

        assessment_type = "Lesson Assessment"

    elif quiz.week_id:

        week = quiz.week

        term = week.term

        subject = term.subject

        assessment_type = "Week Assessment"

    elif quiz.term_id:

        term = quiz.term

        subject = term.subject

        assessment_type = "Term Assessment"

    # =========================================================
    # INVALID ASSESSMENT
    # =========================================================

    if subject is None:

        return redirect(
            "/student/assessments/"
        )

    # =========================================================
    # CHECK STUDENT PROFILE
    # =========================================================

    student_profile = getattr(
        request.user,
        "student_profile",
        None,
    )

    if student_profile is None:

        return redirect(
            "/student/dashboard/"
        )

    # =========================================================
    # CHECK ENROLLMENT
    # =========================================================

    enrollment = (
        student_profile
        .enrollments
        .filter(
            subject=subject
        )
        .first()
    )

    if enrollment is None:

        return redirect(
            "/student/dashboard/"
        )

    # =========================================================
    # QUESTIONS
    # =========================================================

    questions = (
        quiz.questions
        .prefetch_related(
            "choices"
        )
        .order_by(
            "order",
            "id",
        )
    )

    # =========================================================
    # SUBMIT ASSESSMENT
    # =========================================================

    if request.method == "POST":

        with transaction.atomic():

            attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
            )

            for question in questions:

                # =================================================
                # OBJECTIVE QUESTION
                # =================================================

                if (
                    question.question_type
                    == Question.QuestionType.OBJECTIVE
                ):

                    selected_choice_id = (
                        request.POST.get(
                            f"question_{question.id}"
                        )
                    )

                    selected_choice = None

                    if selected_choice_id:

                        selected_choice = (
                            question.choices
                            .filter(
                                id=selected_choice_id
                            )
                            .first()
                        )

                    is_correct = bool(
                        selected_choice
                        and selected_choice.is_correct
                    )

                    points_earned = (
                        question.points
                        if is_correct
                        else 0
                    )

                    Answer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_choice=selected_choice,
                        text_answer="",
                        is_correct=is_correct,
                        points_earned=points_earned,
                        reviewed=True,
                        reviewed_at=timezone.now(),
                    )

                # =================================================
                # THEORY / PRACTICAL QUESTION
                # =================================================

                else:

                    text_answer = (
                        request.POST.get(
                            f"question_{question.id}",
                            "",
                        )
                        .strip()
                    )

                    Answer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_choice=None,
                        text_answer=text_answer,
                        is_correct=False,
                        points_earned=0,
                        reviewed=False,
                        reviewed_at=None,
                        reviewed_by=None,
                        feedback="",
                    )

            # =====================================================
            # CALCULATE INITIAL RESULT
            # =====================================================

            result = (
                attempt.recalculate_result()
            )

            # =====================================================
            # MARK ATTEMPT AS COMPLETED
            # =====================================================

            attempt.completed_at = (
                timezone.now()
            )

            attempt.save(
                update_fields=[
                    "completed_at",
                ]
            )

        # =========================================================
        # LESSON PROGRESS
        # =========================================================

        if (
            quiz.lesson_id
            and attempt.passed
        ):

            LessonProgress.objects.update_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={
                    "completed": True,
                    "completed_at": timezone.now(),
                },
            )

        # =========================================================
        # PREVIOUS ATTEMPTS
        # =========================================================

        previous_attempts = (
            QuizAttempt.objects
            .filter(
                student=request.user,
                quiz=quiz,
            )
            .order_by(
                "-started_at"
            )
        )

        # =========================================================
        # ANSWERS
        # =========================================================

        answers = (
            attempt.answers
            .select_related(
                "question",
                "selected_choice",
                "reviewed_by",
            )
            .prefetch_related(
                "question__choices",
            )
            .order_by(
                "question__order",
                "id",
            )
        )

        # =========================================================
        # RESULT INFORMATION
        # =========================================================

        has_pending_review = (
            result["has_pending_review"]
        )

        review_status = (
            result["review_status"]
        )

        # =========================================================
        # AUTOMATIC SCORE
        # =========================================================

        automatic_score = sum(
            answer.points_earned
            for answer in answers
            if (
                answer.question.question_type
                == Question.QuestionType.OBJECTIVE
            )
        )

        automatic_total = sum(
            answer.question.points
            for answer in answers
            if (
                answer.question.question_type
                == Question.QuestionType.OBJECTIVE
            )
        )

        # =========================================================
        # MANUAL SCORE
        # =========================================================

        manual_score = sum(
            answer.points_earned
            for answer in answers
            if (
                answer.question.question_type
                in [
                    Question.QuestionType.THEORY,
                    Question.QuestionType.PRACTICAL,
                ]
            )
        )

        manual_total = sum(
            answer.question.points
            for answer in answers
            if (
                answer.question.question_type
                in [
                    Question.QuestionType.THEORY,
                    Question.QuestionType.PRACTICAL,
                ]
            )
        )

        # =========================================================
        # TOTAL SCORE
        # =========================================================

        total_score = (
            automatic_score
            + manual_score
        )

        total_points = (
            automatic_total
            + manual_total
        )

        # =========================================================
        # RETURN RESULT PAGE
        # =========================================================

        return render(
            request,
            "assessments/quiz_result.html",
            {
                "quiz": quiz,
                "attempt": attempt,
                "score": total_score,
                "total_points": total_points,

                "automatic_score": automatic_score,
                "automatic_total": automatic_total,

                "manual_score": manual_score,
                "manual_total": manual_total,

                "answers": answers,

                "previous_attempts": previous_attempts,

                "enrollment": enrollment,

                "assessment_type": assessment_type,

                "subject": subject,
                "term": term,
                "week": week,
                "lesson": lesson,

                "has_pending_review": (
                    has_pending_review
                ),

                "review_status": (
                    review_status
                ),

                "review_status_display": (
                    attempt.review_status_display
                ),

                "percentage": (
                    attempt.percentage
                ),

                "passed": (
                    attempt.passed
                ),
            },
        )

    # =========================================================
    # QUIZ PAGE
    # =========================================================

    return render(
        request,
        "assessments/quiz_detail.html",
        {
            "quiz": quiz,
            "questions": questions,

            "enrollment": enrollment,

            "assessment_type": (
                assessment_type
            ),

            "subject": subject,
            "term": term,
            "week": week,
            "lesson": lesson,
        },
    )