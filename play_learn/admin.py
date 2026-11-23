
from django.contrib import admin
from .models import (
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


# =========================================================
# PLAY & LEARN GAMES
# =========================================================

@admin.register(PlayGame)
class PlayGameAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "min_age",
        "max_age",
        "difficulty",
        "is_published",
        "order",
    )

    list_filter = (
        "category",
        "difficulty",
        "is_published",
    )

    search_fields = (
        "name",
        "description",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    list_editable = (
        "is_published",
        "order",
    )

    ordering = ("order", "name")


@admin.register(GameAttempt)
class GameAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "game",
        "score",
        "max_score",
        "status",
        "started_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "game",
        "started_at",
    )

    search_fields = (
        "user__email",
        "game__name",
    )

    readonly_fields = (
        "started_at",
        "completed_at",
    )

    ordering = ("-started_at",)


# =========================================================
# STORIES & NOVELS
# =========================================================

class StoryChapterInline(admin.TabularInline):
    model = StoryChapter
    extra = 1

    fields = (
        "chapter_number",
        "title",
        "is_published",
    )

    ordering = ("chapter_number",)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "genre",
        "audience",
        "content_rating",
        "status",
        "is_featured",
        "chapter_count",
        "created_at",
    )

    list_filter = (
        "genre",
        "audience",
        "content_rating",
        "status",
        "is_featured",
    )

    search_fields = (
        "title",
        "description",
        "author_name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    list_editable = (
        "status",
        "is_featured",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [StoryChapterInline]

    ordering = ("-created_at",)


@admin.register(StoryChapter)
class StoryChapterAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "story",
        "chapter_number",
        "is_published",
        "created_at",
    )

    list_filter = (
        "is_published",
        "story",
    )

    search_fields = (
        "title",
        "content",
        "story__title",
    )

    ordering = (
        "story",
        "chapter_number",
    )


@admin.register(StoryBookmark)
class StoryBookmarkAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "story",
        "chapter",
        "last_position",
        "updated_at",
    )

    list_filter = (
        "updated_at",
        "story",
    )

    search_fields = (
        "user__email",
        "story__title",
    )

    readonly_fields = (
        "updated_at",
    )

    ordering = ("-updated_at",)


# =========================================================
# CARTOON STORIES - SCENES
# =========================================================

class CartoonStorySceneInline(admin.StackedInline):
    model = CartoonStoryScene
    extra = 1

    fields = (
        "scene_number",
        "title",
        "character_name",
        "character_emoji",
        "text",
        "narration_text",
        "illustration",
        "audio_file",
        "is_published",
    )

    ordering = ("scene_number",)


# =========================================================
# CARTOON STORIES - QUIZ ANSWERS
# =========================================================

class CartoonStoryAnswerInline(admin.TabularInline):
    model = CartoonStoryAnswer
    extra = 2

    fields = (
        "answer_text",
        "is_correct",
        "order",
    )

    ordering = ("order",)


# =========================================================
# CARTOON STORIES - QUIZ QUESTIONS
# =========================================================

class CartoonStoryQuestionInline(admin.StackedInline):
    model = CartoonStoryQuestion
    extra = 1

    fields = (
        "question_number",
        "question_text",
        "explanation",
        "is_published",
    )

    ordering = ("question_number",)


@admin.register(CartoonStory)
class CartoonStoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "min_age",
        "max_age",
        "estimated_duration_minutes",
        "status",
        "is_featured",
        "order",
        "scene_count",
        "question_count",
    )

    list_filter = (
        "category",
        "status",
        "is_featured",
    )

    search_fields = (
        "title",
        "description",
        "lesson",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    list_editable = (
        "status",
        "is_featured",
        "order",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Story Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "category",
                    "lesson",
                ),
            },
        ),
        (
            "Appearance",
            {
                "fields": (
                    "cover",
                    "emoji",
                    "cover_emoji",
                ),
            },
        ),
        (
            "Age & Duration",
            {
                "fields": (
                    "min_age",
                    "max_age",
                    "estimated_duration_minutes",
                ),
            },
        ),
        (
            "Publishing",
            {
                "fields": (
                    "status",
                    "is_featured",
                    "order",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [
        CartoonStorySceneInline,
        CartoonStoryQuestionInline,
    ]

    ordering = ("order", "-created_at")


@admin.register(CartoonStoryScene)
class CartoonStorySceneAdmin(admin.ModelAdmin):
    list_display = (
        "story",
        "scene_number",
        "title",
        "character_name",
        "is_published",
    )

    list_filter = (
        "is_published",
        "story",
    )

    search_fields = (
        "story__title",
        "title",
        "character_name",
        "text",
    )

    ordering = (
        "story",
        "scene_number",
    )


@admin.register(CartoonStoryQuestion)
class CartoonStoryQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "story",
        "question_number",
        "question_text",
        "is_published",
    )

    list_filter = (
        "is_published",
        "story",
    )

    search_fields = (
        "story__title",
        "question_text",
    )

    ordering = (
        "story",
        "question_number",
    )

    inlines = [CartoonStoryAnswerInline]


@admin.register(CartoonStoryAnswer)
class CartoonStoryAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "answer_text",
        "is_correct",
        "order",
    )

    list_filter = (
        "is_correct",
    )

    search_fields = (
        "answer_text",
        "question__question_text",
        "question__story__title",
    )

    ordering = (
        "question",
        "order",
    )
