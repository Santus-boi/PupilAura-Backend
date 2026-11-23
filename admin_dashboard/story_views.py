
import logging
from django.urls import reverse
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from ai_services.client import AIClientError
from ai_services.story_generator import (
    generate_story_library,
    generate_cartoon_story,
)

from play_learn.models import (
    Story,
    StoryChapter,
    CartoonStory,
    CartoonStoryScene,
    CartoonStoryQuestion,
    CartoonStoryAnswer,
)

from .views import admin_required


logger = logging.getLogger(__name__)


# =========================================================
# SHARED HELPERS
# =========================================================

def _choice_values(model, field_name):
    field = model._meta.get_field(field_name)
    return [value for value, label in field.choices]


def _unique_slug(model, title, instance=None):
    base_slug = slugify(title)[:200] or "generated-story"
    candidate = base_slug
    counter = 2

    queryset = model.objects.all()

    if instance:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(slug=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base_slug[:220 - len(suffix)]}{suffix}"
        counter += 1

    return candidate


def _get_int(post_data, field_name, default, minimum, maximum):
    raw_value = post_data.get(field_name, default)

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name.replace('_', ' ').capitalize()} must be a number."
        )

    if value < minimum or value > maximum:
        raise ValueError(
            f"{field_name.replace('_', ' ').capitalize()} must be between "
            f"{minimum} and {maximum}."
        )

    return value



def _delete_confirmation(request, obj, object_name, cancel_url, delete_url):
    return render(
        request,
        "admin_dashboard/confirm_delete.html",
        {
            "nav_active": "cartoon_stories" if isinstance(
                obj,
                (CartoonStory, CartoonStoryScene, CartoonStoryQuestion),
            ) else "stories",
            "object": obj,
            "object_name": object_name,
            "cancel_url": cancel_url,
            "delete_url": delete_url,
        },
    )


# =========================================================
# STORY LIBRARY FORMS
# =========================================================

class StoryForm(forms.ModelForm):

    class Meta:
        model = Story
        fields = [
            "title",
            "description",
            "genre",
            "audience",
            "content_rating",
            "author_name",
            "cover",
            "is_featured",
        ]


class StoryChapterForm(forms.ModelForm):

    class Meta:
        model = StoryChapter
        fields = [
            "chapter_number",
            "title",
            "content",
        ]


# =========================================================
# CARTOON STORY FORMS
# =========================================================

class CartoonStoryForm(forms.ModelForm):

    class Meta:
        model = CartoonStory
        fields = [
            "title",
            "description",
            "category",
            "cover",
            "emoji",
            "cover_emoji",
            "min_age",
            "max_age",
            "estimated_duration_minutes",
            "lesson",
            "is_featured",
            "order",
        ]

    def clean(self):
        cleaned_data = super().clean()

        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")

        if min_age is not None and max_age is not None:
            if min_age > max_age:
                raise ValidationError(
                    "Minimum age cannot be greater than maximum age."
                )

        return cleaned_data


class CartoonSceneForm(forms.ModelForm):

    class Meta:
        model = CartoonStoryScene
        fields = [
            "scene_number",
            "character_name",
            "character_emoji",
            "title",
            "text",
            "narration_text",
            "illustration",
            "audio_file",
        ]


class CartoonQuestionForm(forms.ModelForm):

    class Meta:
        model = CartoonStoryQuestion
        fields = [
            "question_number",
            "question_text",
            "explanation",
        ]


class CartoonAnswerForm(forms.ModelForm):

    class Meta:
        model = CartoonStoryAnswer
        fields = [
            "answer_text",
            "is_correct",
            "order",
        ]


class CartoonAnswerFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        active_answers = []

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            answer_text = form.cleaned_data.get("answer_text")

            if answer_text:
                active_answers.append(form.cleaned_data)

        if len(active_answers) < 2:
            raise ValidationError(
                "Each question must have at least two answer options."
            )

        correct_count = sum(
            1 for answer in active_answers
            if answer.get("is_correct")
        )

        if correct_count != 1:
            raise ValidationError(
                "Each question must have exactly one correct answer."
            )


CartoonAnswerFormSet = inlineformset_factory(
    CartoonStoryQuestion,
    CartoonStoryAnswer,
    form=CartoonAnswerForm,
    formset=CartoonAnswerFormSet,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


# =========================================================
# AI STORY GENERATOR
# =========================================================

def _get_story_generator_context(
    request,
    form_data=None,
    generated_story=None,):
    return {
        "nav_active": "ai_story_generator",
        "form_data": form_data or {},
        "generated_story": generated_story,
        "story_genres": Story._meta.get_field("genre").choices,
        "story_audiences": Story._meta.get_field("audience").choices,
        "content_ratings": Story._meta.get_field("content_rating").choices,
        "cartoon_categories": CartoonStory._meta.get_field("category").choices,
    }


@admin_required
def ai_story_generator(request):
    """
    Generate and save either:
    1. A Story Library story with chapters.
    2. An Interactive Cartoon Story with scenes and quiz questions.

    All generated content is saved as a draft.
    """

    form_data = request.POST.dict() if request.method == "POST" else {}
    generated_story = None

    if request.method == "POST":

        story_type = request.POST.get("story_type", "library").strip()
        topic = request.POST.get("topic", "").strip()
        instructions = request.POST.get("instructions", "").strip()

        if not topic:
            messages.error(
                request,
                "Enter a topic or story idea before generating.",
            )

            return render(
                request,
                "admin_dashboard/ai_story_generator.html",
                _get_story_generator_context(request, form_data),
            )

        try:

            # -------------------------------------------------
            # STORY LIBRARY GENERATION
            # -------------------------------------------------

            if story_type == "library":

                genre = request.POST.get("genre", "").strip()
                audience = request.POST.get("audience", "").strip()
                content_rating = request.POST.get(
                    "content_rating", ""
                ).strip()

                chapter_count = _get_int(
                    request.POST,
                    "chapter_count",
                    5,
                    1,
                    20,
                )

                if genre not in _choice_values(Story, "genre"):
                    raise ValueError("Select a valid story genre.")

                if audience not in _choice_values(Story, "audience"):
                    raise ValueError("Select a valid target audience.")

                if content_rating not in _choice_values(
                    Story,
                    "content_rating",
                ):
                    raise ValueError("Select a valid content rating.")

                result = generate_story_library(
                    user=request.user,
                    topic=topic,
                    genre=genre,
                    audience=audience,
                    content_rating=content_rating,
                    chapter_count=chapter_count,
                    instructions=instructions,
                )

                with transaction.atomic():

                    story = Story.objects.create(
                        title=result["title"],
                        slug=_unique_slug(Story, result["title"]),
                        description=result["description"],
                        genre=genre,
                        audience=audience,
                        content_rating=content_rating,
                        author_name=(
                            request.user.get_full_name()
                            or getattr(request.user, "username", "")
                            or "PupilAura"
                        ),
                        status="draft",
                        is_featured=False,
                    )

                    for index, chapter in enumerate(
                        result["chapters"],
                        start=1,
                    ):
                        StoryChapter.objects.create(
                            story=story,
                            chapter_number=index,
                            title=chapter["title"],
                            content=chapter["content"],
                            is_published=False,
                        )

                generated_story = {
                    "type": "library",
                    "title": story.title,
                    "description": story.description,
                    "chapter_count": story.chapters.count(),
                    "status": story.status,
                    "admin_url": "",
                }

                messages.success(
                    request,
                    "Story Library story generated and saved as a draft.",
                )

            # -------------------------------------------------
            # INTERACTIVE CARTOON STORY GENERATION
            # -------------------------------------------------

            elif story_type == "cartoon":

                category = request.POST.get("category", "").strip()
                lesson = request.POST.get("lesson", "").strip()

                min_age = _get_int(
                    request.POST, "min_age", 5, 1, 18
                )

                max_age = _get_int(
                    request.POST, "max_age", 10, 1, 18
                )

                scene_count = _get_int(
                    request.POST, "scene_count", 5, 3, 20
                )

                question_count = _get_int(
                    request.POST, "question_count", 3, 1, 15
                )

                if min_age > max_age:
                    raise ValueError(
                        "Minimum age cannot be greater than maximum age."
                    )

                if category not in _choice_values(
                    CartoonStory,
                    "category",
                ):
                    raise ValueError(
                        "Select a valid cartoon story category."
                    )

                result = generate_cartoon_story(
                    user=request.user,
                    topic=topic,
                    category=category,
                    min_age=min_age,
                    max_age=max_age,
                    scene_count=scene_count,
                    question_count=question_count,
                    lesson=lesson,
                    instructions=instructions,
                )

                with transaction.atomic():

                    cartoon_story = CartoonStory.objects.create(
                        title=result["title"],
                        slug=_unique_slug(
                            CartoonStory,
                            result["title"],
                        ),
                        description=result["description"],
                        category=category,
                        emoji=result.get("emoji", "📖"),
                        cover_emoji=result.get("cover_emoji", "🌟"),
                        min_age=min_age,
                        max_age=max_age,
                        estimated_duration_minutes=result.get(
                            "estimated_duration_minutes",
                            5,
                        ),
                        lesson=result.get("lesson") or lesson,
                        status="draft",
                        is_featured=False,
                    )

                    for index, scene in enumerate(
                        result["scenes"],
                        start=1,
                    ):
                        CartoonStoryScene.objects.create(
                            story=cartoon_story,
                            scene_number=index,
                            character_name=scene.get(
                                "character_name",
                                "Narrator",
                            ),
                            character_emoji=scene.get(
                                "character_emoji",
                                "📖",
                            ),
                            title=scene.get("title", ""),
                            text=scene["text"],
                            narration_text=scene.get(
                                "narration_text",
                                "",
                            ),
                            is_published=False,
                        )

                    for question_index, question_data in enumerate(
                        result["questions"],
                        start=1,
                    ):

                        question = CartoonStoryQuestion.objects.create(
                            story=cartoon_story,
                            question_number=question_index,
                            question_text=question_data["question_text"],
                            explanation=question_data.get(
                                "explanation",
                                "",
                            ),
                            is_published=False,
                        )

                        for answer_index, answer_data in enumerate(
                            question_data["answers"],
                            start=1,
                        ):
                            CartoonStoryAnswer.objects.create(
                                question=question,
                                answer_text=answer_data["answer_text"],
                                is_correct=answer_data["is_correct"],
                                order=answer_index,
                            )

                generated_story = {
                    "type": "cartoon",
                    "title": cartoon_story.title,
                    "description": cartoon_story.description,
                    "scene_count": cartoon_story.scenes.count(),
                    "question_count": cartoon_story.questions.count(),
                    "status": cartoon_story.status,
                    "admin_url": "",
                }

                messages.success(
                    request,
                    "Interactive Cartoon Story generated and saved as a draft.",
                )

            else:
                raise ValueError("Select a valid story type.")

        except (AIClientError, ValueError) as exc:
            messages.error(request, str(exc))

        except Exception:
            logger.exception(
                "Unexpected error while generating an AI story."
            )

            messages.error(
                request,
                "The story could not be saved because of an unexpected "
                "error. Check the server terminal for details.",
            )

    return render(
        request,
        "admin_dashboard/ai_story_generator.html",
        _get_story_generator_context(
            request,
            form_data,
            generated_story,
        ),
    )


# =========================================================
# STORY LIBRARY: LIST
# =========================================================

@admin_required
def stories(request):

    queryset = Story.objects.all()

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    genre = request.GET.get("genre", "").strip()

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(author_name__icontains=search)
        )

    if status in _choice_values(Story, "status"):
        queryset = queryset.filter(status=status)

    if genre in _choice_values(Story, "genre"):
        queryset = queryset.filter(genre=genre)

    return render(
        request,
        "admin_dashboard/stories.html",
        {
            "nav_active": "stories",
            "stories": queryset,
            "search_query": search,
            "selected_status": status,
            "selected_genre": genre,
            "story_statuses": Story._meta.get_field("status").choices,
            "story_genres": Story._meta.get_field("genre").choices,
            "total_stories": Story.objects.count(),
            "published_stories": Story.objects.filter(
                status="published"
            ).count(),
            "draft_stories": Story.objects.filter(
                status="draft"
            ).count(),
        },
    )


# =========================================================
# STORY LIBRARY: CREATE
# =========================================================

@admin_required
def story_create(request):

    if request.method == "POST":
        form = StoryForm(request.POST, request.FILES)

        if form.is_valid():

            story = form.save(commit=False)
            story.slug = _unique_slug(Story, story.title)
            story.status = "draft"

            story.save()

            messages.success(
                request,
                "Story Library story created as a draft.",
            )

            return redirect(
                "admin_dashboard:story_detail",
                story_id=story.pk,
            )

    else:
        form = StoryForm()

    return render(
        request,
        "admin_dashboard/story_form.html",
        {
            "nav_active": "stories",
            "form": form,
            "form_title": "Create Story Library Story",
            "submit_label": "Create Story",
        },
    )


# =========================================================
# STORY LIBRARY: DETAIL
# =========================================================

@admin_required
def story_detail(request, story_id):

    story = get_object_or_404(Story, pk=story_id)

    chapters = story.chapters.all()

    return render(
        request,
        "admin_dashboard/story_detail.html",
        {
            "nav_active": "stories",
            "story": story,
            "chapters": chapters,
            "chapter_count": chapters.count(),
        },
    )


# =========================================================
# STORY LIBRARY: EDIT
# =========================================================

@admin_required
def story_edit(request, story_id):

    story = get_object_or_404(Story, pk=story_id)

    if request.method == "POST":

        form = StoryForm(
            request.POST,
            request.FILES,
            instance=story,
        )

        if form.is_valid():

            updated_story = form.save(commit=False)

            if updated_story.title != story.title:
                updated_story.slug = _unique_slug(
                    Story,
                    updated_story.title,
                    instance=story,
                )

            updated_story.save()

            messages.success(
                request,
                "Story Library story updated successfully.",
            )

            return redirect(
                "admin_dashboard:story_detail",
                story_id=story.pk,
            )

    else:
        form = StoryForm(instance=story)

    return render(
        request,
        "admin_dashboard/story_form.html",
        {
            "nav_active": "stories",
            "form": form,
            "story": story,
            "form_title": "Edit Story Library Story",
            "submit_label": "Save Changes",
        },
    )


# =========================================================
# STORY LIBRARY: DELETE
# =========================================================


@admin_required
def story_delete(request, story_id):

    story = get_object_or_404(Story, pk=story_id)

    if request.method == "POST":

        story_title = story.title
        story.delete()

        messages.success(
            request,
            f'"{story_title}" and its chapters were deleted.',
        )

        return redirect("admin_dashboard:stories")

    return _delete_confirmation(
        request,
        story,
        "Story Library story",
        reverse(
            "admin_dashboard:story_detail",
            kwargs={"story_id": story.pk},
        ),
        reverse(
            "admin_dashboard:story_delete",
            kwargs={"story_id": story.pk},
        ),
    )


# =========================================================
# STORY LIBRARY: CHAPTER CREATE
# =========================================================

@admin_required
def story_chapter_create(request, story_id):

    story = get_object_or_404(Story, pk=story_id)

    if request.method == "POST":

        form = StoryChapterForm(request.POST)

        if form.is_valid():

            chapter = form.save(commit=False)
            chapter.story = story
            chapter.is_published = False

            try:
                chapter.save()

            except Exception:
                logger.exception("Unable to create story chapter.")

                messages.error(
                    request,
                    "Could not create this chapter. Check that its chapter "
                    "number is not already in use.",
                )

                return render(
                    request,
                    "admin_dashboard/story_chapter_form.html",
                    {
                        "nav_active": "stories",
                        "form": form,
                        "story": story,
                        "form_title": "Add Chapter",
                    },
                )

            messages.success(
                request,
                "Chapter added successfully. It is currently unpublished.",
            )

            return redirect(
                "admin_dashboard:story_detail",
                story_id=story.pk,
            )

    else:
        form = StoryChapterForm(
            initial={
                "chapter_number": (
                    story.chapters.order_by("-chapter_number")
                    .values_list("chapter_number", flat=True)
                    .first() or 0
                ) + 1
            }
        )

    return render(
        request,
        "admin_dashboard/story_chapter_form.html",
        {
            "nav_active": "stories",
            "form": form,
            "story": story,
            "form_title": "Add Chapter",
        },
    )


# =========================================================
# STORY LIBRARY: CHAPTER EDIT
# =========================================================

@admin_required
def story_chapter_edit(request, chapter_id):

    chapter = get_object_or_404(
        StoryChapter.objects.select_related("story"),
        pk=chapter_id,
    )

    if request.method == "POST":

        form = StoryChapterForm(
            request.POST,
            instance=chapter,
        )

        if form.is_valid():

            try:
                form.save()

            except Exception:
                logger.exception("Unable to update story chapter.")

                messages.error(
                    request,
                    "Could not update this chapter. Check its chapter number.",
                )

            else:
                messages.success(
                    request,
                    "Chapter updated successfully.",
                )

                return redirect(
                    "admin_dashboard:story_detail",
                    story_id=chapter.story_id,
                )

    else:
        form = StoryChapterForm(instance=chapter)

    return render(
        request,
        "admin_dashboard/story_chapter_form.html",
        {
            "nav_active": "stories",
            "form": form,
            "story": chapter.story,
            "chapter": chapter,
            "form_title": "Edit Chapter",
        },
    )


# =========================================================
# STORY LIBRARY: CHAPTER DELETE
# =========================================================


@admin_required
def story_chapter_delete(request, chapter_id):

    chapter = get_object_or_404(
        StoryChapter.objects.select_related("story"),
        pk=chapter_id,
    )

    story_id = chapter.story_id

    if request.method == "POST":

        chapter.delete()

        messages.success(
            request,
            "Chapter deleted successfully.",
        )

        return redirect(
            "admin_dashboard:story_detail",
            story_id=story_id,
        )

    return _delete_confirmation(
        request,
        chapter,
        "Story chapter",
        reverse(
            "admin_dashboard:story_detail",
            kwargs={"story_id": story_id},
        ),
        reverse(
            "admin_dashboard:story_chapter_delete",
            kwargs={"chapter_id": chapter.pk},
        ),
    )


# =========================================================
# STORY LIBRARY: PUBLISH / UNPUBLISH
# =========================================================

@admin_required
@require_POST
def story_publish_toggle(request, story_id):

    story = get_object_or_404(Story, pk=story_id)

    if story.status == "published":

        story.status = "draft"
        story.chapters.update(is_published=False)
        story.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            "Story unpublished successfully.",
        )

    else:

        chapters = story.chapters.all()

        if not chapters.exists():
            messages.error(
                request,
                "This story cannot be published without at least one chapter.",
            )

            return redirect(
                "admin_dashboard:story_detail",
                story_id=story.pk,
            )

        incomplete = chapters.filter(
            Q(title__isnull=True)
            | Q(title="")
            | Q(content__isnull=True)
            | Q(content="")
        ).exists()

        if incomplete:
            messages.error(
                request,
                "Complete all chapter titles and content before publishing.",
            )

            return redirect(
                "admin_dashboard:story_detail",
                story_id=story.pk,
            )

        with transaction.atomic():

            chapters.update(is_published=True)

            story.status = "published"
            story.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            "Story Library story and all its chapters are now published.",
        )

    return redirect(
        "admin_dashboard:story_detail",
        story_id=story.pk,
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: LIST
# =========================================================

@admin_required
def cartoon_stories(request):

    queryset = CartoonStory.objects.all()

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(lesson__icontains=search)
        )

    if status in _choice_values(CartoonStory, "status"):
        queryset = queryset.filter(status=status)

    if category in _choice_values(CartoonStory, "category"):
        queryset = queryset.filter(category=category)

    return render(
        request,
        "admin_dashboard/cartoon_stories.html",
        {
            "nav_active": "cartoon_stories",
            "cartoon_stories": queryset,
            "search_query": search,
            "selected_status": status,
            "selected_category": category,
            "cartoon_statuses": CartoonStory._meta.get_field(
                "status"
            ).choices,
            "cartoon_categories": CartoonStory._meta.get_field(
                "category"
            ).choices,
            "total_stories": CartoonStory.objects.count(),
            "published_stories": CartoonStory.objects.filter(
                status="published"
            ).count(),
            "draft_stories": CartoonStory.objects.filter(
                status="draft"
            ).count(),
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: CREATE
# =========================================================

@admin_required
def cartoon_story_create(request):

    if request.method == "POST":

        form = CartoonStoryForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            story = form.save(commit=False)
            story.slug = _unique_slug(
                CartoonStory,
                story.title,
            )
            story.status = "draft"

            story.save()

            messages.success(
                request,
                "Interactive Cartoon Story created as a draft.",
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

    else:
        form = CartoonStoryForm()

    return render(
        request,
        "admin_dashboard/cartoon_story_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "form_title": "Create Interactive Cartoon Story",
            "submit_label": "Create Story",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: DETAIL
# =========================================================

@admin_required
def cartoon_story_detail(request, story_id):

    story = get_object_or_404(CartoonStory, pk=story_id)

    scenes = story.scenes.all()

    questions = (
        story.questions
        .prefetch_related("answers")
        .all()
    )

    return render(
        request,
        "admin_dashboard/cartoon_story_detail.html",
        {
            "nav_active": "cartoon_stories",
            "cartoon_story": story,
            "scenes": scenes,
            "questions": questions,
            "scene_count": scenes.count(),
            "question_count": questions.count(),
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: EDIT
# =========================================================

@admin_required
def cartoon_story_edit(request, story_id):

    story = get_object_or_404(
        CartoonStory,
        pk=story_id,
    )

    if request.method == "POST":

        form = CartoonStoryForm(
            request.POST,
            request.FILES,
            instance=story,
        )

        if form.is_valid():

            updated_story = form.save(commit=False)

            if updated_story.title != story.title:
                updated_story.slug = _unique_slug(
                    CartoonStory,
                    updated_story.title,
                    instance=story,
                )

            updated_story.save()

            messages.success(
                request,
                "Interactive Cartoon Story updated successfully.",
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

    else:
        form = CartoonStoryForm(instance=story)

    return render(
        request,
        "admin_dashboard/cartoon_story_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "cartoon_story": story,
            "form_title": "Edit Interactive Cartoon Story",
            "submit_label": "Save Changes",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: DELETE
# =========================================================


@admin_required
def cartoon_story_delete(request, story_id):

    story = get_object_or_404(
        CartoonStory,
        pk=story_id,
    )

    if request.method == "POST":

        title = story.title
        story.delete()

        messages.success(
            request,
            f'"{title}" and its scenes and questions were deleted.',
        )

        return redirect(
            "admin_dashboard:cartoon_stories"
        )

    return _delete_confirmation(
        request,
        story,
        "Interactive Cartoon Story",
        reverse(
            "admin_dashboard:cartoon_story_detail",
            kwargs={"story_id": story.pk},
        ),
        reverse(
            "admin_dashboard:cartoon_story_delete",
            kwargs={"story_id": story.pk},
        ),
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: SCENE CREATE
# =========================================================

@admin_required
def cartoon_scene_create(request, story_id):

    story = get_object_or_404(
        CartoonStory,
        pk=story_id,
    )

    if request.method == "POST":

        form = CartoonSceneForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            scene = form.save(commit=False)
            scene.story = story
            scene.is_published = False

            try:
                scene.save()

            except Exception:
                logger.exception("Unable to create cartoon scene.")

                messages.error(
                    request,
                    "Could not create this scene. Check that its scene "
                    "number is not already in use.",
                )

            else:
                messages.success(
                    request,
                    "Scene added successfully.",
                )

                return redirect(
                    "admin_dashboard:cartoon_story_detail",
                    story_id=story.pk,
                )

    else:

        next_number = (
            story.scenes.order_by("-scene_number")
            .values_list("scene_number", flat=True)
            .first() or 0
        ) + 1

        form = CartoonSceneForm(
            initial={"scene_number": next_number}
        )

    return render(
        request,
        "admin_dashboard/cartoon_scene_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "cartoon_story": story,
            "form_title": "Add Cartoon Scene",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: SCENE EDIT
# =========================================================

@admin_required
def cartoon_scene_edit(request, scene_id):

    scene = get_object_or_404(
        CartoonStoryScene.objects.select_related("story"),
        pk=scene_id,
    )

    if request.method == "POST":

        form = CartoonSceneForm(
            request.POST,
            request.FILES,
            instance=scene,
        )

        if form.is_valid():

            try:
                form.save()

            except Exception:
                logger.exception("Unable to update cartoon scene.")

                messages.error(
                    request,
                    "Could not update this scene. Check its scene number.",
                )

            else:
                messages.success(
                    request,
                    "Cartoon scene updated successfully.",
                )

                return redirect(
                    "admin_dashboard:cartoon_story_detail",
                    story_id=scene.story_id,
                )

    else:
        form = CartoonSceneForm(instance=scene)

    return render(
        request,
        "admin_dashboard/cartoon_scene_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "scene": scene,
            "cartoon_story": scene.story,
            "form_title": "Edit Cartoon Scene",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: SCENE DELETE
# =========================================================


@admin_required
def cartoon_scene_delete(request, scene_id):

    scene = get_object_or_404(
        CartoonStoryScene.objects.select_related("story"),
        pk=scene_id,
    )

    story_id = scene.story_id

    if request.method == "POST":

        scene.delete()

        messages.success(
            request,
            "Cartoon scene deleted successfully.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story_id,
        )

    return _delete_confirmation(
        request,
        scene,
        "Cartoon story scene",
        reverse(
            "admin_dashboard:cartoon_story_detail",
            kwargs={"story_id": story_id},
        ),
        reverse(
            "admin_dashboard:cartoon_scene_delete",
            kwargs={"scene_id": scene.pk},
        ),
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: QUESTION CREATE
# =========================================================

@admin_required
def cartoon_question_create(request, story_id):

    story = get_object_or_404(
        CartoonStory,
        pk=story_id,
    )

    question_instance = CartoonStoryQuestion(
        story=story,
    )

    if request.method == "POST":

        form = CartoonQuestionForm(request.POST)

        answer_formset = CartoonAnswerFormSet(
            request.POST,
            instance=question_instance,
            prefix="answers",
        )

        if form.is_valid() and answer_formset.is_valid():

            with transaction.atomic():

                question = form.save(commit=False)
                question.story = story
                question.is_published = False
                question.save()

                answer_formset.instance = question
                answer_formset.save()

            messages.success(
                request,
                "Question and answer options added successfully.",
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

    else:

        next_number = (
            story.questions.order_by("-question_number")
            .values_list("question_number", flat=True)
            .first() or 0
        ) + 1

        form = CartoonQuestionForm(
            initial={"question_number": next_number}
        )

        answer_formset = CartoonAnswerFormSet(
            instance=question_instance,
            prefix="answers",
        )

    return render(
        request,
        "admin_dashboard/cartoon_question_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "answer_formset": answer_formset,
            "cartoon_story": story,
            "form_title": "Add Interactive Question",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: QUESTION EDIT
# =========================================================

@admin_required
def cartoon_question_edit(request, question_id):

    question = get_object_or_404(
        CartoonStoryQuestion.objects.select_related("story"),
        pk=question_id,
    )

    if request.method == "POST":

        form = CartoonQuestionForm(
            request.POST,
            instance=question,
        )

        answer_formset = CartoonAnswerFormSet(
            request.POST,
            instance=question,
            prefix="answers",
        )

        if form.is_valid() and answer_formset.is_valid():

            with transaction.atomic():

                form.save()
                answer_formset.save()

            messages.success(
                request,
                "Question and answers updated successfully.",
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=question.story_id,
            )

    else:

        form = CartoonQuestionForm(instance=question)

        answer_formset = CartoonAnswerFormSet(
            instance=question,
            prefix="answers",
        )

    return render(
        request,
        "admin_dashboard/cartoon_question_form.html",
        {
            "nav_active": "cartoon_stories",
            "form": form,
            "answer_formset": answer_formset,
            "question": question,
            "cartoon_story": question.story,
            "form_title": "Edit Interactive Question",
        },
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: QUESTION DELETE
# =========================================================


@admin_required
def cartoon_question_delete(request, question_id):

    question = get_object_or_404(
        CartoonStoryQuestion.objects.select_related("story"),
        pk=question_id,
    )

    story_id = question.story_id

    if request.method == "POST":

        question.delete()

        messages.success(
            request,
            "Question and its answer options deleted successfully.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story_id,
        )

    return _delete_confirmation(
        request,
        question,
        "Cartoon story question",
        reverse(
            "admin_dashboard:cartoon_story_detail",
            kwargs={"story_id": story_id},
        ),
        reverse(
            "admin_dashboard:cartoon_question_delete",
            kwargs={"question_id": question.pk},
        ),
    )


# =========================================================
# INTERACTIVE CARTOON STORIES: PUBLISH / UNPUBLISH
# =========================================================

@admin_required
@require_POST
def cartoon_story_publish_toggle(request, story_id):

    story = get_object_or_404(
        CartoonStory,
        pk=story_id,
    )

    if story.status == "published":

        with transaction.atomic():

            story.scenes.update(is_published=False)
            story.questions.update(is_published=False)

            story.status = "draft"
            story.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            "Interactive Cartoon Story unpublished successfully.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story.pk,
        )

    # -----------------------------------------------------
    # CHECK SCENES
    # -----------------------------------------------------

    scenes = story.scenes.all()

    if not scenes.exists():

        messages.error(
            request,
            "Add at least one scene before publishing this cartoon story.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story.pk,
        )

    incomplete_scene = scenes.filter(
        Q(text__isnull=True) | Q(text="")
    ).exists()

    if incomplete_scene:

        messages.error(
            request,
            "Every scene must contain story text before publishing.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story.pk,
        )

    # -----------------------------------------------------
    # CHECK QUESTIONS
    # -----------------------------------------------------

    questions = story.questions.all()

    if not questions.exists():

        messages.error(
            request,
            "Add at least one interactive question before publishing.",
        )

        return redirect(
            "admin_dashboard:cartoon_story_detail",
            story_id=story.pk,
        )

    for question in questions:

        answers = question.answers.all()

        if answers.count() < 2:

            messages.error(
                request,
                (
                    f"Question {question.question_number} must have "
                    "at least two answer options."
                ),
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

        if answers.filter(is_correct=True).count() != 1:

            messages.error(
                request,
                (
                    f"Question {question.question_number} must have "
                    "exactly one correct answer."
                ),
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

        if answers.filter(answer_text="").exists():

            messages.error(
                request,
                (
                    f"Question {question.question_number} contains "
                    "an empty answer option."
                ),
            )

            return redirect(
                "admin_dashboard:cartoon_story_detail",
                story_id=story.pk,
            )

    # -----------------------------------------------------
    # PUBLISH COMPLETE CARTOON STORY
    # -----------------------------------------------------

    with transaction.atomic():

        story.scenes.update(is_published=True)
        story.questions.update(is_published=True)

        story.status = "published"
        story.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        (
            "Interactive Cartoon Story, scenes and questions "
            "are now published."
        ),
    )

    return redirect(
        "admin_dashboard:cartoon_story_detail",
        story_id=story.pk,
    )
