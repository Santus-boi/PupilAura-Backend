from pathlib import Path
import csv

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from learning.models import (
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    Lesson,
    LessonVideo,
    LessonImage,
    LessonResource,
)


class Command(BaseCommand):
    help = "Import lesson videos, images, and resources from CSV."

    REQUIRED_COLUMNS = {
        "education_level",
        "class_name",
        "subject",
        "term_type",
        "week_number",
        "lesson_order",
        "lesson_title",
        "media_type",
        "title",
        "description",
        "file_path",
        "video_url",
        "caption",
        "resource_type",
        "media_order",
        "published",
    }

    VALID_MEDIA_TYPES = {
        "video",
        "image",
        "resource",
    }

    VALID_RESOURCE_TYPES = {
        "pdf",
        "notes",
        "worksheet",
        "exercise",
        "slides",
        "project",
        "other",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the media CSV file.",
        )

        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish all imported media.",
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

                actual_columns = {
                    column.strip()
                    for column in reader.fieldnames
                    if column
                }

                missing_columns = (
                    self.REQUIRED_COLUMNS - actual_columns
                )

                if missing_columns:
                    raise CommandError(
                        "Missing required CSV columns: "
                        + ", ".join(sorted(missing_columns))
                    )

                rows = list(reader)

        except UnicodeDecodeError as exc:
            raise CommandError(
                "Could not read the CSV file as UTF-8."
            ) from exc

        if not rows:
            self.stdout.write(
                self.style.WARNING(
                    "The CSV file contains no rows."
                )
            )
            return

        created = 0
        updated = 0

        with transaction.atomic():

            for row_number, raw_row in enumerate(
                rows,
                start=2,
            ):
                row = self.clean_row(raw_row)

                try:
                    result = self.import_row(
                        row,
                        force_publish,
                    )

                except Exception as exc:
                    raise CommandError(
                        f"Error on CSV row {row_number}: {exc}"
                    ) from exc

                if result == "created":
                    created += 1
                else:
                    updated += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Lesson media import completed successfully."
            )
        )

        self.stdout.write(
            f"Media created: {created}"
        )

        self.stdout.write(
            f"Media updated: {updated}"
        )

        self.stdout.write(
            f"Total processed: {created + updated}"
        )

    def clean_row(self, raw_row):
        cleaned = {}

        for key, value in raw_row.items():

            if key is None:
                continue

            key = key.strip()

            if isinstance(value, str):
                value = value.strip()

            cleaned[key] = value

        return cleaned

    def required_value(self, row, field):
        value = row.get(field, "")

        if value is None:
            value = ""

        value = str(value).strip()

        if not value:
            raise ValueError(
                f"'{field}' cannot be empty."
            )

        return value

    def optional_value(self, row, field):
        value = row.get(field, "")

        if value is None:
            return ""

        return str(value).strip()

    def integer_value(self, row, field):
        value = self.required_value(
            row,
            field,
        )

        try:
            number = int(value)
        except ValueError as exc:
            raise ValueError(
                f"'{field}' must be a whole number."
            ) from exc

        if number < 0:
            raise ValueError(
                f"'{field}' cannot be negative."
            )

        return number

    def boolean_value(self, value):
        if value is None:
            return False

        return str(value).strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "published",
        }

    def find_lesson(self, row):

        education_level_name = self.required_value(
            row,
            "education_level",
        )

        class_name = self.required_value(
            row,
            "class_name",
        )

        subject_name = self.required_value(
            row,
            "subject",
        )

        term_type = self.required_value(
            row,
            "term_type",
        ).lower()

        week_number = self.integer_value(
            row,
            "week_number",
        )

        lesson_order = self.integer_value(
            row,
            "lesson_order",
        )

        lesson_title = self.required_value(
            row,
            "lesson_title",
        )

        # ---------------------------------------------------------
        # Find education level
        # ---------------------------------------------------------

        education_level = (
            EducationLevel.objects
            .filter(name__iexact=education_level_name)
            .first()
        )

        if education_level is None:
            raise ValueError(
                f"Education level not found: "
                f"{education_level_name}"
            )

        # ---------------------------------------------------------
        # Find class
        # ---------------------------------------------------------

        school_class = (
            SchoolClass.objects
            .filter(
                education_level=education_level,
                name__iexact=class_name,
            )
            .first()
        )

        if school_class is None:
            raise ValueError(
                f"School class not found: "
                f"{class_name}"
            )

        # ---------------------------------------------------------
        # Find subject
        # ---------------------------------------------------------

        subject = (
            Subject.objects
            .filter(
                school_class=school_class,
                name__iexact=subject_name,
            )
            .first()
        )

        if subject is None:
            raise ValueError(
                f"Subject not found: "
                f"{subject_name}"
            )

        # ---------------------------------------------------------
        # Find term
        # ---------------------------------------------------------

        term = (
            Term.objects
            .filter(
                subject=subject,
                term_type__iexact=term_type,
            )
            .first()
        )

        if term is None:
            raise ValueError(
                f"Term not found: "
                f"{term_type} for {subject.name}"
            )

        # ---------------------------------------------------------
        # Find week
        # ---------------------------------------------------------

        week = (
            Week.objects
            .filter(
                term=term,
                number=week_number,
            )
            .first()
        )

        if week is None:
            raise ValueError(
                f"Week {week_number} not found "
                f"for {term.name}"
            )

        # ---------------------------------------------------------
        # Find lesson
        # ---------------------------------------------------------

        lesson = (
            Lesson.objects
            .filter(
                week=week,
                order=lesson_order,
                title__iexact=lesson_title,
            )
            .first()
        )

        if lesson is None:

            # Give a useful debugging message.
            available_lessons = list(
                week.lessons
                .order_by("order", "id")
                .values_list(
                    "order",
                    "title",
                )
            )

            if available_lessons:
                available = "; ".join(
                    f"{order}: {title}"
                    for order, title
                    in available_lessons
                )

                raise ValueError(
                    f"Lesson not found: "
                    f"'{lesson_title}'. "
                    f"Available lessons in Week "
                    f"{week.number}: {available}"
                )

            raise ValueError(
                f"No lessons exist in Week "
                f"{week.number}."
            )

        return lesson

    def import_row(
        self,
        row,
        force_publish=False,
    ):
        lesson = self.find_lesson(row)

        media_type = self.required_value(
            row,
            "media_type",
        ).lower()

        if media_type not in self.VALID_MEDIA_TYPES:
            raise ValueError(
                "Invalid media_type. "
                "Use video, image, or resource."
            )

        title = self.required_value(
            row,
            "title",
        )

        description = self.optional_value(
            row,
            "description",
        )

        media_order = self.integer_value(
            row,
            "media_order",
        )

        published = self.boolean_value(
            row.get("published")
        )

        if force_publish:
            published = True

        if media_type == "video":
            return self.import_video(
                lesson=lesson,
                title=title,
                description=description,
                media_order=media_order,
                published=published,
                video_url=self.optional_value(
                    row,
                    "video_url",
                ),
            )

        if media_type == "image":
            return self.import_image(
                lesson=lesson,
                title=title,
                description=description,
                media_order=media_order,
                published=published,
                file_path=self.optional_value(
                    row,
                    "file_path",
                ),
                caption=self.optional_value(
                    row,
                    "caption",
                ),
            )

        return self.import_resource(
            lesson=lesson,
            title=title,
            description=description,
            media_order=media_order,
            published=published,
            file_path=self.optional_value(
                row,
                "file_path",
            ),
            resource_type=self.optional_value(
                row,
                "resource_type",
            ).lower(),
        )

    def import_video(
        self,
        lesson,
        title,
        description,
        media_order,
        published,
        video_url,
    ):
        if not video_url:
            raise ValueError(
                "video_url is required for video media."
            )

        video, created = (
            LessonVideo.objects.update_or_create(
                lesson=lesson,
                order=media_order,
                defaults={
                    "title": title,
                    "description": description,
                    "video_url": video_url,
                    "published": published,
                },
            )
        )

        return "created" if created else "updated"

    def import_image(
        self,
        lesson,
        title,
        description,
        media_order,
        published,
        file_path,
        caption,
    ):
        if not file_path:
            raise ValueError(
                "file_path is required for image media."
            )

        source_path = Path(file_path)

        if not source_path.exists():
            raise ValueError(
                f"Image file not found: {file_path}"
            )

        if not source_path.is_file():
            raise ValueError(
                f"Image path is not a file: {file_path}"
            )

        image = LessonImage.objects.filter(
            lesson=lesson,
            order=media_order,
        ).first()

        created = image is None

        if image is None:
            image = LessonImage(
                lesson=lesson,
                order=media_order,
            )

        image.title = title
        image.caption = caption
        image.published = published

        with source_path.open("rb") as file:
            image.image.save(
                source_path.name,
                File(file),
                save=False,
            )

        image.save()

        return "created" if created else "updated"

    def import_resource(
        self,
        lesson,
        title,
        description,
        media_order,
        published,
        file_path,
        resource_type,
    ):
        if not file_path:
            raise ValueError(
                "file_path is required for resource media."
            )

        if resource_type not in self.VALID_RESOURCE_TYPES:
            raise ValueError(
                "Invalid resource_type. "
                "Use one of: "
                + ", ".join(
                    sorted(self.VALID_RESOURCE_TYPES)
                )
            )

        source_path = Path(file_path)

        if not source_path.exists():
            raise ValueError(
                f"Resource file not found: {file_path}"
            )

        if not source_path.is_file():
            raise ValueError(
                f"Resource path is not a file: {file_path}"
            )

        resource = LessonResource.objects.filter(
            lesson=lesson,
            order=media_order,
        ).first()

        created = resource is None

        if resource is None:
            resource = LessonResource(
                lesson=lesson,
                order=media_order,
            )

        resource.title = title
        resource.description = description
        resource.resource_type = resource_type
        resource.published = published

        with source_path.open("rb") as file:
            resource.file.save(
                source_path.name,
                File(file),
                save=False,
            )

        resource.save()

        return "created" if created else "updated"