from django.contrib import admin

from .models import (
    Category,
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    CurriculumMaterial,
    Course,
    Lesson,
    LessonVideo,
    LessonImage,
    LessonResource,
)


# ==============================================================
# INLINES
# ==============================================================

class LessonVideoInline(admin.TabularInline):
    """Video clips attached to a lesson."""
    model = LessonVideo
    extra = 0
    fields = ("order", "title", "video_url", "published")
    ordering = ("order", "id")
    show_change_link = True


class LessonImageInline(admin.TabularInline):
    """Images / diagrams attached to a lesson."""
    model = LessonImage
    extra = 0
    fields = ("order", "title", "image", "published")
    ordering = ("order", "id")
    show_change_link = True


class LessonResourceInline(admin.TabularInline):
    """Downloadable files attached to a lesson."""
    model = LessonResource
    extra = 0
    fields = ("order", "title", "file", "published")
    ordering = ("order", "id")
    show_change_link = True


class LessonInline(admin.TabularInline):
    """Compact view of a week's lessons — reorder and glance."""
    model = Lesson
    extra = 0
    fields = ("order", "title", "published")
    ordering = ("order", "id")
    show_change_link = True

class WeekCurriculumMaterialInline(admin.StackedInline):
    model = CurriculumMaterial
    fk_name = "week"
    extra = 1
    max_num = 1
    fields = ("title", "file", "description", "published")
    verbose_name = "Week Study Material"
    verbose_name_plural = "Week Study Material"


class TermCurriculumMaterialInline(admin.StackedInline):
    model = CurriculumMaterial
    fk_name = "term"
    extra = 1
    max_num = 1
    fields = ("title", "file", "description", "published")
    verbose_name = "Term Study Material"
    verbose_name_plural = "Term Study Material"

#=======================================================
# CATEGORY
# ==============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
    )

    search_fields = (
        "name",
        "description",
    )


# ==============================================================
# EDUCATION LEVEL
# ==============================================================

@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "level_type",
        "order",
    )

    list_filter = (
        "level_type",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "order",
    )


# ==============================================================
# SCHOOL CLASS
# ==============================================================

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "education_level",
        "order",
    )

    list_filter = (
        "education_level",
    )

    search_fields = (
        "name",
        "education_level__name",
    )

    ordering = (
        "education_level",
        "order",
    )


# ==============================================================
# SUBJECT
# ==============================================================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school_class",
        "education_level",
    )

    list_filter = (
        "school_class__education_level",
        "school_class",
    )

    search_fields = (
        "name",
        "school_class__name",
        "school_class__education_level__name",
    )

    ordering = (
        "school_class",
        "name",
    )

    @admin.display(
        description="Education Level"
    )
    def education_level(self, obj):
        return obj.school_class.education_level


# ==============================================================
# TERM
# ==============================================================

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "term_type",
        "subject",
        "school_class",
        "order",
    )

    list_filter = (
        "term_type",
        "subject__school_class",
        "subject__school_class__education_level",
    )

    search_fields = (
        "name",
        "subject__name",
        "subject__school_class__name",
    )

    ordering = (
        "subject",
        "order",
    )

    inlines = [
        TermCurriculumMaterialInline,
    ]

    @admin.display(
        description="School Class"
    )
    def school_class(self, obj):
        return obj.subject.school_class



# ==============================================================
# WEEK  (lessons inline)
# ==============================================================

@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "title",
        "term",
        "subject",
        "school_class",
    )

    list_filter = (
        "term__term_type",
        "term__subject",
        "term__subject__school_class",
    )

    search_fields = (
        "title",
        "term__name",
        "term__subject__name",
        "term__subject__school_class__name",
    )

    ordering = (
        "term",
        "number",
    )

    inlines = [
        LessonInline,
        WeekCurriculumMaterialInline,
    ]

    @admin.display(
        description="Subject"
    )
    def subject(self, obj):
        return obj.term.subject

    @admin.display(
        description="School Class"
    )
    def school_class(self, obj):
        return obj.term.subject.school_class



# ==============================================================
# CURRICULUM MATERIAL
# ==============================================================

@admin.register(CurriculumMaterial)
class CurriculumMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "material_level",
        "parent_name",
        "published",
        "updated_at",
    )

    list_filter = (
        "published",
    )

    search_fields = (
        "title",
        "description",
        "week__title",
        "term__name",
        "term__subject__name",
    )

    ordering = (
        "-updated_at",
    )

    fields = (
        "title",
        "week",
        "term",
        "file",
        "description",
        "published",
    )

    @admin.display(description="Level")
    def material_level(self, obj):
        return "Week" if obj.week_id else "Term"

    @admin.display(description="Attached To")
    def parent_name(self, obj):
        if obj.week_id:
            return (
                f"{obj.week.term.subject.name} - "
                f"Week {obj.week.number}"
            )

        return (
            f"{obj.term.subject.name} - "
            f"{obj.term.name}"
        )

# ==============================================================
# COURSE (independent)
# ==============================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "education_level",
        "subject",
        "price",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "category",
        "education_level",
        "subject",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "-created_at",
    )


# ==============================================================
# LESSON  (videos + images + resources inline)
# ==============================================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "school_class",
        "subject",
        "term",
        "week",
        "order",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "week__term__subject__school_class",
        "week__term__subject",
        "week__term__term_type",
        "week",
    )

    search_fields = (
        "title",
        "description",
        "content",
        "practical",
        "week__title",
        "week__term__name",
        "week__term__subject__name",
        "week__term__subject__school_class__name",
    )

    ordering = (
        "week",
        "order",
    )

    inlines = [
        LessonVideoInline,
        LessonImageInline,
        LessonResourceInline,
    ]

    @admin.display(
        description="School Class"
    )
    def school_class(self, obj):
        return obj.school_class

    @admin.display(
        description="Subject"
    )
    def subject(self, obj):
        return obj.subject

    @admin.display(
        description="Term"
    )
    def term(self, obj):
        return obj.term


# ==============================================================
# LESSON VIDEO
# ==============================================================

@admin.register(LessonVideo)
class LessonVideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "lesson__week__term__subject",
    )

    search_fields = (
        "title",
        "description",
        "lesson__title",
    )

    ordering = (
        "lesson",
        "order",
    )


# ==============================================================
# LESSON IMAGE
# ==============================================================

@admin.register(LessonImage)
class LessonImageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "lesson__week__term__subject",
    )

    search_fields = (
        "title",
        "caption",
        "lesson__title",
    )

    ordering = (
        "lesson",
        "order",
    )


# ==============================================================
# LESSON RESOURCE
# ==============================================================

@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "lesson__week__term__subject",
    )

    search_fields = (
        "title",
        "description",
        "lesson__title",
    )

    ordering = (
        "lesson",
        "order",
    )
