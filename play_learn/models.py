
from django.conf import settings
from django.db import models
from django.utils import timezone


class PlayGame(models.Model):
    class Category(models.TextChoices):
        ARCADE = "arcade", "Arcade Games"
        LEARN = "learn", "Learn & Play"
        SPEAKING = "speaking", "Speaking Lab"
        CARTOON = "cartoon", "Cartoon World"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    class Route(models.TextChoices):
        ALPHABET_ADVENTURE = "alphabet_adventure", "Alphabet Adventure"
        MATH_CHALLENGE = "math_challenge", "Math Challenge"
        WORD_BUILDER = "word_builder", "Word Builder"
        PRONUNCIATION_LAB = "pronunciation_lab", "Pronunciation Lab"
        CARTOON_ADVENTURE = "cartoon_adventure", "Cartoon Adventure"
        MEMORY_MATCH = "memory_match", "Memory Match"
        BUBBLE_POP = "bubble_pop", "Bubble Pop"
        WHACK_A_MOLE = "whack_a_mole", "Whack-a-Mole"
        NUMBER_NINJA = "number_ninja", "Number Ninja"
        COLOR_RUSH = "color_rush", "Color Rush"
        SIMON_SAYS = "simon_says", "Simon Says"
        TREASURE_HUNT = "treasure_hunt", "Treasure Hunt"
        MAZE_RUNNER = "maze_runner", "Maze Runner"
        CHESS_MASTER = "chess_master", "Chess Master"
        SUDOKU_CHALLENGE = "sudoku_challenge", "Sudoku Challenge"
        DETECTIVE_CASE_FILES = "detective_case_files", "Detective Case Files"
        TOWER_DEFENSE = "tower_defense", "Tower Defense"
        WORD_MASTER = "word_master", "Word Master"
        BUSINESS_TYCOON = "business_tycoon", "Business Tycoon"
        STOCK_MARKET_SIMULATOR = "stock_market_simulator", "Stock Market Simulator"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)

    url_name = models.CharField(
        max_length=60,
        choices=Route.choices,
        blank=True,
        default="",
        help_text="The existing play_learn URL name for this game.",
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.LEARN,
    )

    min_age = models.PositiveSmallIntegerField(default=3)
    max_age = models.PositiveSmallIntegerField(default=5)

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
    )

    thumbnail = models.ImageField(
        upload_to="play_learn/games/",
        blank=True,
        null=True,
    )

    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Play & Learn Game"
        verbose_name_plural = "Play & Learn Games"

    def __str__(self):
        return self.name


class GameAttempt(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="play_learn_attempts",
        null=True,
        blank=True,
    )

    game = models.ForeignKey(
        PlayGame,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STARTED,
    )

    extra_data = models.JSONField(default=dict, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "game"]),
            models.Index(fields=["game", "status"]),
        ]

    def __str__(self):
        player = self.user if self.user else "Guest"
        return f"{player} - {self.game.name} ({self.score})"

    @property
    def percentage(self):
        if self.max_score <= 0:
            return 0

        return round((self.score / self.max_score) * 100, 2)


class Story(models.Model):
    class Genre(models.TextChoices):
        MYSTERY = "mystery", "Mystery & Crime"
        ROMANCE = "romance", "Romance & Drama"
        THRILLER = "thriller", "Thriller & Suspense"
        FANTASY = "fantasy", "Fantasy & Supernatural"
        AFRICAN = "african", "African Fiction"
        SCIFI = "scifi", "Science Fiction"
        ADVENTURE = "adventure", "Adventure"
        LIFESTYLE = "lifestyle", "Life & Psychology"

    class Audience(models.TextChoices):
        KIDS = "kids", "Kids"
        TEENS = "teens", "Teenagers"
        ADULTS = "adults", "Adults"

    class ContentRating(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        AGE_13 = "13+", "13+"
        AGE_16 = "16+", "16+"
        AGE_18 = "18+", "18+"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()

    cover = models.ImageField(
        upload_to="play_learn/stories/",
        blank=True,
        null=True,
    )

    genre = models.CharField(
        max_length=20,
        choices=Genre.choices,
        default=Genre.ADVENTURE,
    )

    audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.TEENS,
    )

    content_rating = models.CharField(
        max_length=20,
        choices=ContentRating.choices,
        default=ContentRating.EVERYONE,
    )

    author_name = models.CharField(max_length=150, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "audience"]),
            models.Index(fields=["genre", "status"]),
        ]

    def __str__(self):
        return self.title

    @property
    def chapter_count(self):
        return self.chapters.count()


class StoryChapter(models.Model):
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="chapters",
    )

    chapter_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chapter_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["story", "chapter_number"],
                name="unique_story_chapter_number",
            )
        ]

    def __str__(self):
        return f"{self.story.title} - Chapter {self.chapter_number}"


class StoryBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_bookmarks",
    )

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )

    chapter = models.ForeignKey(
        StoryChapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reader_bookmarks",
    )

    last_position = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "story"],
                name="unique_user_story_bookmark",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.story.title}"


# ==========================================================
# INTERACTIVE CARTOON STORIES
# ==========================================================

class CartoonStory(models.Model):
    class Category(models.TextChoices):
        FRIENDSHIP = "friendship", "Friendship"
        HONESTY = "honesty", "Honesty"
        KINDNESS = "kindness", "Kindness"
        ADVENTURE = "adventure", "Adventure"
        COURAGE = "courage", "Courage"
        ANIMALS = "animals", "Animal Stories"
        FAMILY = "family", "Family"
        NATURE = "nature", "Nature"
        EDUCATIONAL = "educational", "Educational"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    description = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.ADVENTURE,
    )

    cover = models.ImageField(
        upload_to="play_learn/cartoon_stories/covers/",
        blank=True,
        null=True,
    )

    emoji = models.CharField(max_length=20, blank=True)
    cover_emoji = models.CharField(max_length=50, blank=True)

    min_age = models.PositiveSmallIntegerField(default=3)
    max_age = models.PositiveSmallIntegerField(default=8)

    estimated_duration_minutes = models.PositiveSmallIntegerField(
        default=5
    )

    lesson = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Cartoon Story"
        verbose_name_plural = "Cartoon Stories"
        indexes = [
            models.Index(fields=["status", "category"]),
        ]

    def __str__(self):
        return self.title

    @property
    def scene_count(self):
        return self.scenes.count()

    @property
    def question_count(self):
        return self.questions.count()


class CartoonStoryScene(models.Model):
    story = models.ForeignKey(
        CartoonStory,
        on_delete=models.CASCADE,
        related_name="scenes",
    )

    scene_number = models.PositiveIntegerField()

    character_name = models.CharField(
        max_length=100,
        default="Narrator",
    )

    character_emoji = models.CharField(
        max_length=20,
        blank=True,
        default="📖",
    )

    title = models.CharField(max_length=200, blank=True)

    text = models.TextField(
        help_text="The dialogue or narration displayed in this scene."
    )

    narration_text = models.TextField(
        blank=True,
        help_text="Optional alternative text for audio narration. "
                  "If empty, the scene text can be narrated."
    )

    illustration = models.ImageField(
        upload_to="play_learn/cartoon_stories/scenes/",
        blank=True,
        null=True,
    )

    audio_file = models.FileField(
        upload_to="play_learn/cartoon_stories/audio/",
        blank=True,
        null=True,
        help_text="Optional recorded narration for this scene."
    )

    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scene_number"]
        verbose_name = "Cartoon Story Scene"
        verbose_name_plural = "Cartoon Story Scenes"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "scene_number"],
                name="unique_cartoon_scene_number",
            )
        ]

    def __str__(self):
        return (
            f"{self.story.title} - Scene {self.scene_number}"
        )

    @property
    def narration(self):
        return self.narration_text or self.text


class CartoonStoryQuestion(models.Model):
    story = models.ForeignKey(
        CartoonStory,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    question_number = models.PositiveIntegerField(default=1)
    question_text = models.TextField()

    explanation = models.TextField(
        blank=True,
        help_text="Optional explanation shown after answering."
    )

    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["question_number"]
        verbose_name = "Cartoon Story Question"
        verbose_name_plural = "Cartoon Story Questions"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "question_number"],
                name="unique_cartoon_question_number",
            )
        ]

    def __str__(self):
        return (
            f"{self.story.title} - Question {self.question_number}"
        )

    @property
    def correct_answer(self):
        return self.answers.filter(is_correct=True).first()


class CartoonStoryAnswer(models.Model):
    question = models.ForeignKey(
        CartoonStoryQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Cartoon Story Answer"
        verbose_name_plural = "Cartoon Story Answers"

    def __str__(self):
        return self.answer_text
