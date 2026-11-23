import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from learning.models import (
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    Lesson,
)


class Command(BaseCommand):
    help = "Import or update school curriculum lessons from a CSV file."

    REQUIRED_COLUMNS = {
        "education_level",
        "level_type",
        "class_name",
        "subject",
        "term_name",
        "term_type",
        "week_number",
        "week_title",
        "week_overview",
        "week_activities",
        "lesson_order",
        "lesson_title",
        "description",
        "objectives",
        "content",
        "examples",
        "key_points",
        "activity",
        "practical",
        "published",
    }

    VALID_LEVEL_TYPES = {
        "nursery",
        "primary",
        "jss",
        "ss",
    }

    VALID_TERM_TYPES = {
        "first",
        "second",
        "third",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the lesson CSV file.",
        )

        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish imported lessons regardless of CSV published value.",
        )

        parser.add_argument(
            "--replace-week",
            action="store_true",
            help=(
                "For every week represented in the CSV, remove existing "
                "lessons whose order is not present in the CSV."
            ),
        )

    def handle(self, *args, **options):
        csv_file = Path(options["csv_file"])
        force_publish = options["publish"]
        replace_week = options["replace_week"]

        if not csv_file.exists():
            raise CommandError(
                f"CSV file not found: {csv_file}"
            )

        if not csv_file.is_file():
            raise CommandError(
                f"Path is not a file: {csv_file}"
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

                actual_columns = {
                    column.strip()
                    for column in reader.fieldnames
                    if column
                }

                missing_columns = (
                    self.REQUIRED_COLUMNS - actual_columns
                )

                if missing_columns:
                    missing = ", ".join(
                        sorted(missing_columns)
                    )

                    raise CommandError(
                        f"Missing required CSV columns: {missing}"
                    )

                rows = list(reader)

        except UnicodeDecodeError as exc:
            raise CommandError(
                "Could not read the CSV file as UTF-8."
            ) from exc

        if not rows:
            self.stdout.write(
                self.style.WARNING(
                    "The CSV file contains no lesson rows."
                )
            )
            return

        imported_count = 0
        updated_count = 0
        deleted_count = 0

        try:
            with transaction.atomic():

                imported_week_data = {}

                for row_number, raw_row in enumerate(
                    rows,
                    start=2,
                ):
                    row = self.clean_row(raw_row)

                    try:
                        result, week = self.import_row(
                            row=row,
                            force_publish=force_publish,
                        )

                    except Exception as exc:
                        raise CommandError(
                            f"Error on CSV row {row_number}: {exc}"
                        ) from exc

                    if result == "created":
                        imported_count += 1
                    else:
                        updated_count += 1

                    week_key = week.pk

                    if week_key not in imported_week_data:
                        imported_week_data[week_key] = {
                            "week": week,
                            "lesson_orders": set(),
                        }

                    lesson_order = self.integer_value(
                        row,
                        "lesson_order",
                    )

                    imported_week_data[week_key][
                        "lesson_orders"
                    ].add(lesson_order)

                if replace_week:
                    for data in imported_week_data.values():
                        week = data["week"]
                        lesson_orders = data["lesson_orders"]

                        deleted_lessons = (
                            Lesson.objects
                            .filter(week=week)
                            .exclude(order__in=lesson_orders)
                        )

                        count = deleted_lessons.count()

                        if count:
                            deleted_lessons.delete()
                            deleted_count += count

        except CommandError:
            raise

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Lesson import completed successfully."
            )
        )

        self.stdout.write(
            f"Lessons created: {imported_count}"
        )

        self.stdout.write(
            f"Lessons updated: {updated_count}"
        )

        self.stdout.write(
            f"Lessons deleted: {deleted_count}"
        )

        self.stdout.write(
            f"Total processed: "
            f"{imported_count + updated_count}"
        )

        if replace_week:
            self.stdout.write(
                self.style.WARNING(
                    "Replace-week mode was enabled."
                )
            )

    def clean_row(self, raw_row):
        row = {}

        for key, value in raw_row.items():
            clean_key = (
                key.strip()
                if key
                else key
            )

            clean_value = (
                value.strip()
                if isinstance(value, str)
                else value
            )

            row[clean_key] = clean_value

        return row

    def required_value(self, row, field_name):
        value = row.get(field_name, "")

        if value is None:
            value = ""

        value = str(value).strip()

        if not value:
            raise ValueError(
                f"'{field_name}' cannot be empty."
            )

        return value

    def optional_value(self, row, field_name):
        value = row.get(field_name, "")

        if value is None:
            return ""

        return str(value).strip()

    def boolean_value(self, value, default=False):
        if value is None:
            return default

        value = str(value).strip().lower()

        if value in {
            "1",
            "true",
            "yes",
            "y",
            "published",
        }:
            return True

        if value in {
            "0",
            "false",
            "no",
            "n",
            "unpublished",
        }:
            return False

        return default

    def integer_value(self, row, field_name):
        value = self.required_value(
            row,
            field_name,
        )

        try:
            number = int(value)
        except ValueError as exc:
            raise ValueError(
                f"'{field_name}' must be a whole number. "
                f"Received: {value}"
            ) from exc

        if number < 0:
            raise ValueError(
                f"'{field_name}' cannot be negative."
            )

        return number

    def import_row(self, row, force_publish=False):

        # ---------------------------------------------------------
        # EDUCATION LEVEL
        # ---------------------------------------------------------

        education_level_name = self.required_value(
            row,
            "education_level",
        )

        level_type = self.required_value(
            row,
            "level_type",
        ).lower()

        if level_type not in self.VALID_LEVEL_TYPES:
            raise ValueError(
                "Invalid level_type. "
                f"Use one of: "
                f"{', '.join(sorted(self.VALID_LEVEL_TYPES))}"
            )

        education_level, _ = (
            EducationLevel.objects.update_or_create(
                name=education_level_name,
                defaults={
                    "level_type": level_type,
                },
            )
        )

        # ---------------------------------------------------------
        # SCHOOL CLASS
        # ---------------------------------------------------------

        class_name = self.required_value(
            row,
            "class_name",
        )

        school_class, _ = (
            SchoolClass.objects.get_or_create(
                name=class_name,
                education_level=education_level,
                defaults={
                    "order": 0,
                },
            )
        )

        # ---------------------------------------------------------
        # SUBJECT
        # ---------------------------------------------------------

        subject_name = self.required_value(
            row,
            "subject",
        )

        subject, _ = (
            Subject.objects.get_or_create(
                name=subject_name,
                school_class=school_class,
            )
        )

        # ---------------------------------------------------------
        # TERM
        # ---------------------------------------------------------

        term_name = self.required_value(
            row,
            "term_name",
        )

        term_type = self.required_value(
            row,
            "term_type",
        ).lower()

        if term_type not in self.VALID_TERM_TYPES:
            raise ValueError(
                "Invalid term_type. "
                f"Use one of: "
                f"{', '.join(sorted(self.VALID_TERM_TYPES))}"
            )

        term, _ = Term.objects.get_or_create(
            term_type=term_type,
            subject=subject,
            defaults={
                "name": term_name,
                "order": self.term_order(term_type),
            },
        )

        changed = False

        if term.name != term_name:
            term.name = term_name
            changed = True

        expected_term_order = self.term_order(
            term_type
        )

        if term.order != expected_term_order:
            term.order = expected_term_order
            changed = True

        if changed:
            term.save(
                update_fields=[
                    "name",
                    "order",
                ]
            )

        # ---------------------------------------------------------
        # WEEK
        # ---------------------------------------------------------

        week_number = self.integer_value(
            row,
            "week_number",
        )

        week_title = self.optional_value(
            row,
            "week_title",
        )

        week_overview = self.optional_value(
            row,
            "week_overview",
        )

        week_activities = self.optional_value(
            row,
            "week_activities",
        )

        week, _ = Week.objects.update_or_create(
            term=term,
            number=week_number,
            defaults={
                "title": week_title,
                "overview": week_overview,
                "activities": week_activities,
            },
        )

        # ---------------------------------------------------------
        # LESSON
        # ---------------------------------------------------------

        lesson_order = self.integer_value(
            row,
            "lesson_order",
        )

        lesson_title = self.required_value(
            row,
            "lesson_title",
        )

        description = self.optional_value(
            row,
            "description",
        )

        objectives = self.optional_value(
            row,
            "objectives",
        )

        content = self.optional_value(
            row,
            "content",
        )

        examples = self.optional_value(
            row,
            "examples",
        )

        key_points = self.optional_value(
            row,
            "key_points",
        )

        activity = self.optional_value(
            row,
            "activity",
        )

        practical = self.optional_value(
            row,
            "practical",
        )

        published = self.boolean_value(
            row.get("published"),
            default=False,
        )

        if force_publish:
            published = True

        lesson, created = (
            Lesson.objects.update_or_create(
                week=week,
                order=lesson_order,
                defaults={
                    "title": lesson_title,
                    "description": description,
                    "objectives": objectives,
                    "content": content,
                    "examples": examples,
                    "key_points": key_points,
                    "activity": activity,
                    "practical": practical,
                    "published": published,
                },
            )
        )

        return (
            "created" if created else "updated",
            week,
        )

    def term_order(self, term_type):
        return {
            "first": 1,
            "second": 2,
            "third": 3,
        }[term_type]