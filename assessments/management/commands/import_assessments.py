import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from assessments.models import Quiz, Question, Choice
from learning.models import (
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    Lesson,
)


class Command(BaseCommand):
    help = "Import or update curriculum assessments from a CSV file."

    REQUIRED_COLUMNS = {
        "education_level",
        "class_name",
        "subject",
        "term_type",
        "week_number",
        "lesson_order",
        "lesson_title",
        "assessment_type",
        "assessment_title",
        "assessment_description",
        "pass_mark",
        "question_order",
        "question_type",
        "question_text",
        "points",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "published",
    }

    VALID_ASSESSMENT_TYPES = {
        "lesson",
        "week",
        "term",
    }

    VALID_QUESTION_TYPES = {
        "objective",
        "theory",
        "practical",
    }

    VALID_CORRECT_ANSWERS = {
        "A",
        "B",
        "C",
        "D",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the assessment CSV file.",
        )

        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish all imported assessments.",
        )

    def handle(self, *args, **options):
        csv_file = Path(options["csv_file"])
        force_publish = options["publish"]

        if not csv_file.exists():
            raise CommandError(
                f"CSV file not found: {csv_file}"
            )

        try:
            with csv_file.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise CommandError(
                        "The CSV file does not contain a header row."
                    )

                missing_columns = (
                    self.REQUIRED_COLUMNS
                    - set(reader.fieldnames)
                )

                if missing_columns:
                    raise CommandError(
                        "Missing required CSV columns: "
                        + ", ".join(sorted(missing_columns))
                    )

                rows = list(reader)

        except UnicodeDecodeError as exc:
            raise CommandError(
                "The CSV file must be saved as UTF-8."
            ) from exc

        if not rows:
            raise CommandError(
                "The CSV file does not contain any assessment rows."
            )

        quiz_cache = {}

        stats = {
            "quizzes_created": 0,
            "quizzes_updated": 0,
            "questions_created": 0,
            "questions_updated": 0,
            "choices_created": 0,
            "choices_updated": 0,
            "total_rows": 0,
        }

        try:
            with transaction.atomic():
                for row_number, row in enumerate(
                    rows,
                    start=2,
                ):
                    self.process_row(
                        row=row,
                        row_number=row_number,
                        force_publish=force_publish,
                        quiz_cache=quiz_cache,
                        stats=stats,
                    )

        except Exception as exc:
            raise CommandError(
                f"Import failed: {exc}"
            ) from exc

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Assessment import completed successfully."
            )
        )

        self.stdout.write(
            f"Quizzes created: {stats['quizzes_created']}"
        )

        self.stdout.write(
            f"Quizzes updated: {stats['quizzes_updated']}"
        )

        self.stdout.write(
            f"Questions created: {stats['questions_created']}"
        )

        self.stdout.write(
            f"Questions updated: {stats['questions_updated']}"
        )

        self.stdout.write(
            f"Choices created: {stats['choices_created']}"
        )

        self.stdout.write(
            f"Choices updated: {stats['choices_updated']}"
        )

        self.stdout.write(
            f"Total processed: {stats['total_rows']}"
        )

    def process_row(
        self,
        row,
        row_number,
        force_publish,
        quiz_cache,
        stats,
    ):
        education_level_name = self.clean(
            row["education_level"]
        )

        class_name = self.clean(
            row["class_name"]
        )

        subject_name = self.clean(
            row["subject"]
        )

        term_type = self.clean(
            row["term_type"]
        ).lower()

        week_number = self.parse_positive_integer(
            row["week_number"],
            "week_number",
            row_number,
        )

        lesson_order = self.parse_non_negative_integer(
            row["lesson_order"],
            "lesson_order",
            row_number,
        )

        lesson_title = self.clean(
            row["lesson_title"]
        )

        assessment_type = self.clean(
            row["assessment_type"]
        ).lower()

        assessment_title = self.clean(
            row["assessment_title"]
        )

        assessment_description = self.clean(
            row["assessment_description"]
        )

        pass_mark = self.parse_pass_mark(
            row["pass_mark"],
            row_number,
        )

        question_order = self.parse_non_negative_integer(
            row["question_order"],
            "question_order",
            row_number,
        )

        question_type = self.clean(
            row["question_type"]
        ).lower()

        question_text = self.clean(
            row["question_text"]
        )

        points = self.parse_positive_integer(
            row["points"],
            "points",
            row_number,
        )

        correct_answer = self.clean(
            row["correct_answer"]
        ).upper()

        published = self.parse_boolean(
            row["published"],
            row_number,
        )

        if force_publish:
            published = True

        self.validate_assessment_type(
            assessment_type,
            row_number,
        )

        self.validate_question_type(
            question_type,
            row_number,
        )

        if not assessment_title:
            raise CommandError(
                f"Row {row_number}: assessment_title cannot be empty."
            )

        if not question_text:
            raise CommandError(
                f"Row {row_number}: question_text cannot be empty."
            )

        education_level = self.get_education_level(
            education_level_name,
            row_number,
        )

        school_class = self.get_school_class(
            education_level,
            class_name,
            row_number,
        )

        subject = self.get_subject(
            school_class,
            subject_name,
            row_number,
        )

        term = self.get_term(
            subject,
            term_type,
            row_number,
        )

        week = self.get_week(
            term,
            week_number,
            row_number,
        )

        lesson = self.get_lesson(
            week,
            lesson_order,
            lesson_title,
            row_number,
        )

        parent = self.get_assessment_parent(
            assessment_type=assessment_type,
            lesson=lesson,
            week=week,
            term=term,
        )

        cache_key = (
            assessment_type,
            parent.pk,
            assessment_title.lower(),
        )

        if cache_key in quiz_cache:
            quiz = quiz_cache[cache_key]

        else:
            quiz, created = Quiz.objects.get_or_create(
                title=assessment_title,
                **{
                    f"{assessment_type}_id": parent.pk,
                },
                defaults={
                    "description": assessment_description,
                    "pass_mark": pass_mark,
                    "published": published,
                },
            )

            if created:
                stats["quizzes_created"] += 1

            else:
                changed = False

                if quiz.description != assessment_description:
                    quiz.description = assessment_description
                    changed = True

                if quiz.pass_mark != pass_mark:
                    quiz.pass_mark = pass_mark
                    changed = True

                if quiz.published != published:
                    quiz.published = published
                    changed = True

                if changed:
                    quiz.save()
                    stats["quizzes_updated"] += 1

            quiz_cache[cache_key] = quiz

        question, question_created = Question.objects.get_or_create(
            quiz=quiz,
            order=question_order,
            defaults={
                "text": question_text,
                "question_type": question_type,
                "points": points,
            },
        )

        if question_created:
            stats["questions_created"] += 1

        else:
            changed = False

            if question.text != question_text:
                question.text = question_text
                changed = True

            if question.question_type != question_type:
                question.question_type = question_type
                changed = True

            if question.points != points:
                question.points = points
                changed = True

            if changed:
                question.save()
                stats["questions_updated"] += 1

        if question_type == Question.QuestionType.OBJECTIVE:
            self.import_choices(
                question=question,
                row=row,
                correct_answer=correct_answer,
                row_number=row_number,
                stats=stats,
            )

        else:
            self.clear_non_objective_choices(question)

        stats["total_rows"] += 1

    def import_choices(
        self,
        question,
        row,
        correct_answer,
        row_number,
        stats,
    ):
        options = {
            "A": self.clean(row["option_a"]),
            "B": self.clean(row["option_b"]),
            "C": self.clean(row["option_c"]),
            "D": self.clean(row["option_d"]),
        }

        if correct_answer not in self.VALID_CORRECT_ANSWERS:
            raise CommandError(
                f"Row {row_number}: correct_answer must be "
                f"A, B, C, or D."
            )

        if not options["A"] or not options["B"]:
            raise CommandError(
                f"Row {row_number}: objective questions must "
                f"have at least options A and B."
            )

        available_options = [
            letter
            for letter, text in options.items()
            if text
        ]

        if correct_answer not in available_options:
            raise CommandError(
                f"Row {row_number}: correct_answer "
                f"{correct_answer} has no corresponding option."
            )

        for index, letter in enumerate(
            available_options,
            start=1,
        ):
            option_text = options[letter]

            choice, created = Choice.objects.get_or_create(
                question=question,
                order=index,
                defaults={
                    "text": option_text,
                    "is_correct": (
                        letter == correct_answer
                    ),
                },
            )

            if created:
                stats["choices_created"] += 1

            else:
                changed = False

                if choice.text != option_text:
                    choice.text = option_text
                    changed = True

                should_be_correct = (
                    letter == correct_answer
                )

                if choice.is_correct != should_be_correct:
                    choice.is_correct = should_be_correct
                    changed = True

                if changed:
                    choice.save()
                    stats["choices_updated"] += 1

    def clear_non_objective_choices(
        self,
        question,
    ):
        question.choices.all().delete()

    def get_education_level(
        self,
        name,
        row_number,
    ):
        try:
            return EducationLevel.objects.get(
                name__iexact=name
            )
        except EducationLevel.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: EducationLevel "
                f"'{name}' was not found."
            )
        except EducationLevel.MultipleObjectsReturned:
            raise CommandError(
                f"Row {row_number}: Multiple education levels "
                f"matched '{name}'."
            )

    def get_school_class(
        self,
        education_level,
        name,
        row_number,
    ):
        try:
            return SchoolClass.objects.get(
                education_level=education_level,
                name__iexact=name,
            )
        except SchoolClass.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: SchoolClass "
                f"'{name}' was not found under "
                f"'{education_level.name}'."
            )
        except SchoolClass.MultipleObjectsReturned:
            raise CommandError(
                f"Row {row_number}: Multiple classes matched "
                f"'{name}' under '{education_level.name}'."
            )

    def get_subject(
        self,
        school_class,
        name,
        row_number,
    ):
        try:
            return Subject.objects.get(
                school_class=school_class,
                name__iexact=name,
            )
        except Subject.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Subject "
                f"'{name}' was not found under "
                f"'{school_class.name}'."
            )
        except Subject.MultipleObjectsReturned:
            raise CommandError(
                f"Row {row_number}: Multiple subjects matched "
                f"'{name}' under '{school_class.name}'."
            )

    def get_term(
        self,
        subject,
        term_type,
        row_number,
    ):
        try:
            return Term.objects.get(
                subject=subject,
                term_type__iexact=term_type,
            )
        except Term.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Term '{term_type}' "
                f"was not found for '{subject.name}'."
            )
        except Term.MultipleObjectsReturned:
            raise CommandError(
                f"Row {row_number}: Multiple terms matched "
                f"'{term_type}' for '{subject.name}'."
            )

    def get_week(
        self,
        term,
        number,
        row_number,
    ):
        try:
            return Week.objects.get(
                term=term,
                number=number,
            )
        except Week.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Week {number} "
                f"was not found for '{term}'."
            )

    def get_lesson(
        self,
        week,
        lesson_order,
        lesson_title,
        row_number,
    ):
        lessons = Lesson.objects.filter(
            week=week,
            order=lesson_order,
        )

        if lessons.count() == 1:
            lesson = lessons.first()

            if lesson.title.lower() != lesson_title.lower():
                raise CommandError(
                    f"Row {row_number}: Lesson order "
                    f"{lesson_order} under Week {week.number} "
                    f"is '{lesson.title}', not "
                    f"'{lesson_title}'."
                )

            return lesson

        if lessons.count() > 1:
            raise CommandError(
                f"Row {row_number}: Multiple lessons found "
                f"with order {lesson_order} in Week "
                f"{week.number}."
            )

        try:
            return Lesson.objects.get(
                week=week,
                title__iexact=lesson_title,
            )
        except Lesson.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Lesson "
                f"'{lesson_title}' was not found "
                f"under Week {week.number}."
            )
        except Lesson.MultipleObjectsReturned:
            raise CommandError(
                f"Row {row_number}: Multiple lessons matched "
                f"'{lesson_title}' under Week {week.number}."
            )

    def get_assessment_parent(
        self,
        assessment_type,
        lesson,
        week,
        term,
    ):
        if assessment_type == "lesson":
            return lesson

        if assessment_type == "week":
            return week

        if assessment_type == "term":
            return term

        raise CommandError(
            f"Unsupported assessment type: {assessment_type}"
        )

    def validate_assessment_type(
        self,
        assessment_type,
        row_number,
    ):
        if assessment_type not in self.VALID_ASSESSMENT_TYPES:
            raise CommandError(
                f"Row {row_number}: assessment_type must be "
                f"lesson, week, or term."
            )

    def validate_question_type(
        self,
        question_type,
        row_number,
    ):
        if question_type not in self.VALID_QUESTION_TYPES:
            raise CommandError(
                f"Row {row_number}: question_type must be "
                f"objective, theory, or practical."
            )

    def parse_positive_integer(
        self,
        value,
        field_name,
        row_number,
    ):
        try:
            number = int(str(value).strip())
        except ValueError as exc:
            raise CommandError(
                f"Row {row_number}: {field_name} must be "
                f"a whole number."
            ) from exc

        if number <= 0:
            raise CommandError(
                f"Row {row_number}: {field_name} must be "
                f"greater than zero."
            )

        return number

    def parse_non_negative_integer(
        self,
        value,
        field_name,
        row_number,
    ):
        try:
            number = int(str(value).strip())
        except ValueError as exc:
            raise CommandError(
                f"Row {row_number}: {field_name} must be "
                f"a whole number."
            ) from exc

        if number < 0:
            raise CommandError(
                f"Row {row_number}: {field_name} cannot be "
                f"negative."
            )

        return number

    def parse_pass_mark(
        self,
        value,
        row_number,
    ):
        try:
            pass_mark = int(str(value).strip())
        except ValueError as exc:
            raise CommandError(
                f"Row {row_number}: pass_mark must be "
                f"a whole number."
            ) from exc

        if not 0 <= pass_mark <= 100:
            raise CommandError(
                f"Row {row_number}: pass_mark must be "
                f"between 0 and 100."
            )

        return pass_mark

    def parse_boolean(
        self,
        value,
        row_number,
    ):
        normalized = self.clean(value).lower()

        if normalized in {
            "true",
            "1",
            "yes",
            "y",
            "published",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "n",
            "unpublished",
            "",
        }:
            return False

        raise CommandError(
            f"Row {row_number}: published must be "
            f"true or false."
        )

    def clean(self, value):
        if value is None:
            return ""

        return str(value).strip()