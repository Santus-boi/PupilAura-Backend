from django.contrib import admin

from .models import (
    TechCategory,
    TechCourse,
    TechModule,
    TechLesson,
    TechLessonVideo,
    TechLessonImage,
    TechLessonResource,
    TechEnrollment,
    TechLessonProgress,
    TechQuiz,
    TechQuestion,
    TechChoice,
    TechQuizAttempt,
)


# ==============================================================
# INLINES
# ==============================================================

class TechModuleInline(admin.TabularInline):
    """Modules of a TechCourse — reorder / glance."""
    model = TechModule
    extra = 0
    fields = ("order", "title", "published")
    ordering = ("order", "id")
    show_change_link = True


class TechLessonInline(admin.TabularInline):
    """Lessons of a TechModule — reorder / glance."""
    model = TechLesson
    extra = 0
    fields = ("order", "title", "published")
    ordering = ("order", "id")
    show_change_link = True


class TechLessonVideoInline(admin.TabularInline):
    """Video clips attached to a TechLesson."""
    model = TechLessonVideo
    extra = 0
    fields = ("order", "title", "video_url", "published")
    ordering = ("order", "id")
    show_change_link = True


class TechLessonImageInline(admin.TabularInline):
    """Images / diagrams attached to a TechLesson."""
    model = TechLessonImage
    extra = 0
    fields = ("order", "title", "image", "published")
    ordering = ("order", "id")
    show_change_link = True


class TechLessonResourceInline(admin.TabularInline):
    """Downloadable files attached to a TechLesson."""
    model = TechLessonResource
    extra = 0
    fields = ("order", "title", "file", "published")
    ordering = ("order", "id")
    show_change_link = True


class TechQuestionInline(admin.TabularInline):
    """Questions of a TechQuiz."""
    model = TechQuestion
    extra = 0
    fields = ("order", "question", "points")
    ordering = ("order", "id")
    show_change_link = True


class TechChoiceInline(admin.TabularInline):
    """Answer choices for a TechQuestion."""
    model = TechChoice
    extra = 4
    fields = ("order", "text", "is_correct")
    ordering = ("order", "id")
    show_change_link = True


# ==============================================================
# TECH CATEGORY
# ==============================================================

@admin.register(TechCategory)
class TechCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "order",
        "published",
        "created_at",
    )
    list_filter = ("published",)
    search_fields = ("name", "description")
    ordering = ("order", "name")


# ==============================================================
# TECH COURSE  (modules inline)
# ==============================================================

@admin.register(TechCourse)
class TechCourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "published",
        "created_at",
    )
    list_filter = ("published", "category")
    search_fields = (
        "title",
        "description",
        "category__name",
    )
    ordering = ("-created_at",)

    inlines = [
        TechModuleInline,
    ]


# ==============================================================
# TECH MODULE  (lessons inline)
# ==============================================================

@admin.register(TechModule)
class TechModuleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "order",
        "published",
        "created_at",
    )
    list_filter = ("published", "course")
    search_fields = (
        "title",
        "description",
        "course__title",
    )
    ordering = ("course", "order")

    inlines = [
        TechLessonInline,
    ]


# ==============================================================
# TECH LESSON  (videos / images / resources inline)
# ==============================================================

@admin.register(TechLesson)
class TechLessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "module",
        "course",
        "order",
        "published",
        "created_at",
    )
    list_filter = (
        "published",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "description",
        "content",
        "practical",
        "project",
        "module__title",
        "module__course__title",
    )
    ordering = ("module", "order")

    inlines = [
        TechLessonVideoInline,
        TechLessonImageInline,
        TechLessonResourceInline,
    ]

    @admin.display(description="Course")
    def course(self, obj):
        return obj.module.course


# ==============================================================
# TECH LESSON VIDEO
# ==============================================================

@admin.register(TechLessonVideo)
class TechLessonVideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )
    list_filter = (
        "published",
        "lesson__module__course",
    )
    search_fields = (
        "title",
        "description",
        "lesson__title",
    )
    ordering = ("lesson", "order")


# ==============================================================
# TECH LESSON IMAGE
# ==============================================================

@admin.register(TechLessonImage)
class TechLessonImageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )
    list_filter = (
        "published",
        "lesson__module__course",
    )
    search_fields = (
        "title",
        "caption",
        "lesson__title",
    )
    ordering = ("lesson", "order")


# ==============================================================
# TECH LESSON RESOURCE
# ==============================================================

@admin.register(TechLessonResource)
class TechLessonResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "order",
        "published",
        "created_at",
    )
    list_filter = (
        "published",
        "lesson__module__course",
    )
    search_fields = (
        "title",
        "description",
        "lesson__title",
    )
    ordering = ("lesson", "order")


# ==============================================================
# TECH ENROLLMENT
# ==============================================================

@admin.register(TechEnrollment)
class TechEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "enrolled_at",
        "completed",
    )
    list_filter = (
        "completed",
        "course",
    )
    search_fields = (
        "student__email",
        "course__title",
    )
    ordering = ("-enrolled_at",)


# ==============================================================
# TECH LESSON PROGRESS
# ==============================================================

@admin.register(TechLessonProgress)
class TechLessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "lesson",
        "completed",
        "completed_at",
    )
    list_filter = (
        "completed",
        "lesson__module__course",
    )
    search_fields = (
        "enrollment__student__email",
        "lesson__title",
        "lesson__module__course__title",
    )
    ordering = ("-completed_at",)

    @admin.display(description="Student")
    def student(self, obj):
        return obj.enrollment.student

    @admin.display(description="Course")
    def course(self, obj):
        return obj.lesson.module.course


# ==============================================================
# TECH QUIZ  (questions inline)
# ==============================================================

@admin.register(TechQuiz)
class TechQuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "pass_mark",
        "published",
        "created_at",
    )
    list_filter = (
        "published",
        "pass_mark",
        "lesson__module__course",
    )
    search_fields = (
        "title",
        "description",
        "lesson__title",
        "lesson__module__title",
        "lesson__module__course__title",
    )
    ordering = ("-created_at",)

    inlines = [
        TechQuestionInline,
    ]


# ==============================================================
# TECH QUESTION  (choices inline)
# ==============================================================

@admin.register(TechQuestion)
class TechQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "quiz",
        "points",
        "order",
    )
    list_filter = (
        "quiz",
        "quiz__lesson__module__course",
    )
    search_fields = (
        "question",
        "quiz__title",
        "quiz__lesson__title",
    )
    ordering = (
        "quiz",
        "order",
    )

    inlines = [
        TechChoiceInline,
    ]


# ==============================================================
# TECH CHOICE
# ==============================================================

@admin.register(TechChoice)
class TechChoiceAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "question",
        "is_correct",
        "order",
    )
    list_filter = (
        "is_correct",
        "question__quiz",
    )
    search_fields = (
        "text",
        "question__question",
        "question__quiz__title",
    )
    ordering = (
        "question",
        "order",
    )


# ==============================================================
# TECH QUIZ ATTEMPT
# ==============================================================

@admin.register(TechQuizAttempt)
class TechQuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "quiz",
        "score",
        "total_points",
        "percentage",
        "passed",
        "completed_at",
    )
    list_filter = (
        "passed",
        "quiz",
        "quiz__lesson__module__course",
    )
    search_fields = (
        "student__email",
        "quiz__title",
        "quiz__lesson__title",
    )
    ordering = ("-completed_at",)

    readonly_fields = (
        "student",
        "quiz",
        "score",
        "total_points",
        "percentage",
        "passed",
        "completed_at",
    )