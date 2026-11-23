import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from exam_prep.models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamQuestion,
    ExamChoice,
)


class Command(BaseCommand):
    help = "Import exam preparation questions from a CSV file."

    REQUIRED_COLUMNS = {
        "exam",
        "subject",
        "year",
        "resource_type",
        "resource_title",
        "question_number",
        "question_type",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "explanation",
        "marks",
        "published",
    }

    VALID_RESOURCE_TYPES = {
        "past_questions",
        "solutions",
        "lesson",
        "practical",
        "mock_exam",
        "revision",
    }

    VALID_QUESTION_TYPES = {
        "mcq",
        "theory",
        "practical",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the exam questions CSV file.",
        )

        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish imported records.",
        )

    def handle(self, *args, **options):
        csv_file = Path(options["csv_file"])
        force_publish = options["publish"]

        if not csv_file.exists():
            raise CommandError(
                f"CSV file not found: {csv_file}"
            )

        self.stdout.write(
            self.style.WARNING(
                f"Reading exam file: {csv_file}"
            )
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
                        "The CSV file has no header row."
                    )

                missing_columns = (
                    self.REQUIRED_COLUMNS
                    - set(reader.fieldnames)
                )

                if missing_columns:
                    raise CommandError(
                        "Missing required CSV columns: "
                        + ", ".join(
                            sorted(missing_columns)
                        )
                    )

                rows = list(reader)

        except UnicodeDecodeError as exc:
            raise CommandError(
                "The CSV file must be saved as UTF-8."
            ) from exc

        if not rows:
            raise CommandError(
                "The CSV file contains no data rows."
            )

        counters = {
            "exams_created": 0,
            "subjects_created": 0,
            "years_created": 0,
            "resources_created": 0,
            "questions_created": 0,
            "questions_updated": 0,
            "choices_created": 0,
            "choices_updated": 0,
        }

        try:
            with transaction.atomic():

                for row_number, row in enumerate(
                    rows,
                    start=2,
                ):
                    self.import_row(
                        row,
                        row_number,
                        force_publish,
                        counters,
                    )

        except Exception as exc:
            raise CommandError(
                f"Error on CSV row {row_number}: {exc}"
            ) from exc

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "EXAM PREP IMPORT COMPLETED"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )

        for key, value in counters.items():
            self.stdout.write(
                f"{key.replace('_', ' ').title()}: {value}"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Exam preparation import completed successfully."
            )
        )

    def import_row(
        self,
        row,
        row_number,
        force_publish,
        counters,
    ):
        exam_name = self.clean(row.get("exam"))

        subject_name = self.clean(
            row.get("subject")
        )

        year_value = self.clean(
            row.get("year")
        )

        resource_type = self.clean(
            row.get("resource_type")
        ).lower()

        resource_title = self.clean(
            row.get("resource_title")
        )

        question_number = self.clean(
            row.get("question_number")
        )

        question_type = self.clean(
            row.get("question_type")
        ).lower()

        question_text = self.clean(
            row.get("question_text")
        )

        correct_answer = self.clean(
            row.get("correct_answer")
        ).lower()

        explanation = self.clean(
            row.get("explanation")
        )

        marks_value = self.clean(
            row.get("marks")
        )

        published_value = self.clean(
            row.get("published")
        )

        if not exam_name:
            raise ValueError(
                "exam is required"
            )

        if not subject_name:
            raise ValueError(
                "subject is required"
            )

        if not year_value:
            raise ValueError(
                "year is required"
            )

        if not resource_type:
            raise ValueError(
                "resource_type is required"
            )

        if not resource_title:
            raise ValueError(
                "resource_title is required"
            )

        if not question_number:
            raise ValueError(
                "question_number is required"
            )

        if not question_text:
            raise ValueError(
                "question_text is required"
            )

        if resource_type not in self.VALID_RESOURCE_TYPES:
            raise ValueError(
                f"Invalid resource_type: "
                f"{resource_type}"
            )

        if question_type not in self.VALID_QUESTION_TYPES:
            raise ValueError(
                f"Invalid question_type: "
                f"{question_type}"
            )

        try:
            year = int(year_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid year: {year_value}"
            ) from exc

        try:
            question_number_int = int(
                question_number
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid question_number: "
                f"{question_number}"
            ) from exc

        try:
            marks = int(marks_value or 1)
        except ValueError as exc:
            raise ValueError(
                f"Invalid marks: {marks_value}"
            ) from exc

        published = self.to_bool(
            published_value
        )

        if force_publish:
            published = True

        exam, created = Exam.objects.get_or_create(
            name=exam_name,
            defaults={
                "slug": self.unique_exam_slug(
                    exam_name
                ),
                "published": published,
            },
        )

        if created:
            counters["exams_created"] += 1
        else:
            changed = False

            if force_publish and not exam.published:
                exam.published = True
                changed = True

            if changed:
                exam.save(
                    update_fields=[
                        "published",
                    ]
                )

        subject, created = (
            ExamSubject.objects.get_or_create(
                exam=exam,
                name=subject_name,
                defaults={
                    "published": published,
                },
            )
        )

        if created:
            counters["subjects_created"] += 1

        year_obj, created = (
            ExamYear.objects.get_or_create(
                exam=exam,
                year=year,
                defaults={
                    "published": published,
                },
            )
        )

        if created:
            counters["years_created"] += 1

        resource, created = (
            ExamResource.objects.get_or_create(
                exam=exam,
                subject=subject,
                year=year_obj,
                resource_type=resource_type,
                title=resource_title,
                defaults={
                    "published": published,
                },
            )
        )

        if created:
            counters["resources_created"] += 1

        question, created = (
            ExamQuestion.objects.update_or_create(
                resource=resource,
                question_number=question_number_int,
                defaults={
                    "question_type": question_type,
                    "question_text": question_text,
                    "explanation": explanation,
                    "marks": marks,
                    "published": published,
                    "order": question_number_int,
                },
            )
        )

        if created:
            counters["questions_created"] += 1
        else:
            counters["questions_updated"] += 1

        if question_type == "mcq":
            choices = [
                (
                    1,
                    self.clean(row.get("option_a")),
                    "a",
                ),
                (
                    2,
                    self.clean(row.get("option_b")),
                    "b",
                ),
                (
                    3,
                    self.clean(row.get("option_c")),
                    "c",
                ),
                (
                    4,
                    self.clean(row.get("option_d")),
                    "d",
                ),
            ]

            for order, text, letter in choices:

                if not text:
                    continue

                is_correct = (
                    correct_answer == letter
                )

                choice, created = (
                    ExamChoice.objects.update_or_create(
                        question=question,
                        order=order,
                        defaults={
                            "text": text,
                            "is_correct": is_correct,
                        },
                    )
                )

                if created:
                    counters[
                        "choices_created"
                    ] += 1
                else:
                    counters[
                        "choices_updated"
                    ] += 1

        self.stdout.write(
            f"Row {row_number}: "
            f"IMPORTED - "
            f"{exam_name} / "
            f"{subject_name} / "
            f"{year} / "
            f"Question {question_number_int}"
        )

    @staticmethod
    def clean(value):
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def to_bool(value):
        value = str(value).strip().lower()

        return value in {
            "true",
            "1",
            "yes",
            "y",
            "published",
        }

    @staticmethod
    def unique_exam_slug(name):
        base_slug = slugify(name)

        slug = base_slug
        counter = 2

        while Exam.objects.filter(
            slug=slug
        ).exists():

            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug