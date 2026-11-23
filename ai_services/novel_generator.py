
import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


NOVEL_SYSTEM_PROMPT = """You are a professional novelist, literary editor,
and creative writing specialist.

Create original, engaging, coherent and well-structured fiction.
Respect the requested genre, audience and content rating.

Maintain consistent characters, settings, timelines and plot details.
Avoid plagiarism, copied stories and generic filler.
Never introduce content that violates the requested audience or rating.

Return strictly valid JSON. Never include markdown, code fences,
or commentary outside the JSON object."""


NOVEL_CONCEPT_PROMPT = """Develop an original novel concept.

Return JSON with exactly these keys:

{{
    "title": "string — compelling novel title, maximum 200 characters",
    "description": "string — engaging novel description or synopsis",
    "genre": "{genre}",
    "audience": "{audience}",
    "content_rating": "{content_rating}"
}}

Creative direction:
- Genre: {genre}
- Intended audience: {audience}
- Content rating: {content_rating}
- Initial premise: {premise}
- Preferred title, if provided: {preferred_title}

Requirements:
- Create an original and interesting concept.
- Give the story a clear central conflict.
- Make the description engaging without revealing the entire ending.
- Respect the requested audience and content rating.
- Return exactly the requested fields."""


CHAPTER_OUTLINE_PROMPT = """Create a detailed chapter outline for this novel.

Novel title: {title}
Novel description: {description}
Genre: {genre}
Audience: {audience}
Content rating: {content_rating}

Number of chapters: {chapter_count}
Additional direction: {instructions}

Return JSON with exactly this structure:

{{
    "chapters": [
        {{
            "chapter_number": 1,
            "title": "string — chapter title",
            "summary": "string — detailed summary of what happens"
        }}
    ]
}}

Requirements:
- Return exactly {chapter_count} chapters.
- Number chapters sequentially, starting from 1.
- Give every chapter a distinct and meaningful title.
- Develop the plot progressively.
- Maintain continuity between chapters.
- Establish characters and conflicts naturally.
- Avoid repetitive chapter summaries.
- Give the novel a satisfying narrative progression.
- Respect the requested audience and content rating."""


CHAPTER_CONTENT_PROMPT = """Write the complete content of one novel chapter.

Novel title: {novel_title}
Novel description: {novel_description}
Genre: {genre}
Audience: {audience}
Content rating: {content_rating}

Chapter number: {chapter_number}
Chapter title: {chapter_title}
Chapter outline: {chapter_summary}

Previous chapter context:
{previous_context}

Additional writing instructions:
{instructions}

Target word count: {target_word_count}

Return JSON with exactly these keys:

{{
    "chapter_number": {chapter_number},
    "title": "string — chapter title",
    "content": "string — complete chapter content"
}}

Writing requirements:
- Write polished, engaging literary prose.
- Use natural dialogue where appropriate.
- Develop characters through actions, dialogue and decisions.
- Maintain consistency with the novel description and previous events.
- Follow the supplied chapter outline.
- Do not summarize the chapter instead of writing it.
- Do not add chapter headings inside the content.
- Respect the audience and content rating.
- Aim for approximately the requested word count.
- Do not prematurely resolve conflicts intended for later chapters."""


def _record_generation(
    *,
    user,
    feature: str,
    client: AIClient,
    start: float,
    success: bool,
    error: Exception | None = None,
) -> None:
    duration_ms = int((time.monotonic() - start) * 1000)

    record_ai_call(
        user=user,
        feature=feature,
        provider=client.provider,
        model=client.model,
        success=success,
        error_message=str(error)[:1000] if error else "",
        duration_ms=duration_ms,
    )


def _generate_payload(
    *,
    user,
    feature: str,
    system_prompt: str,
    user_prompt: str,
    validator,
) -> dict[str, Any]:
    client = AIClient()
    start = time.monotonic()

    try:
        payload = client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )

        cleaned = validator(payload)

        _record_generation(
            user=user,
            feature=feature,
            client=client,
            start=start,
            success=True,
        )

        return cleaned

    except AIClientError as exc:
        _record_generation(
            user=user,
            feature=feature,
            client=client,
            start=start,
            success=False,
            error=exc,
        )
        raise


# ==========================================================
# 1. GENERATE NOVEL CONCEPT
# ==========================================================

def generate_novel_concept(
    *,
    user,
    genre: str,
    audience: str,
    content_rating: str,
    premise: str = "",
    preferred_title: str = "",
) -> dict[str, Any]:
    """
    Generate an original adult/teen novel concept.

    Returns:
        title, description, genre, audience, content_rating

    Does not save anything to the database.
    """

    required_inputs = {
        "genre": genre,
        "audience": audience,
        "content_rating": content_rating,
    }

    for field, value in required_inputs.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field.replace('_', ' ').title()} is required.")

    prompt = NOVEL_CONCEPT_PROMPT.format(
        genre=genre.strip(),
        audience=audience.strip(),
        content_rating=content_rating.strip(),
        premise=premise.strip() or "Create an original story concept.",
        preferred_title=preferred_title.strip() or "Choose an appropriate title.",
    )

    def validate(payload):
        required = {
            "title",
            "description",
            "genre",
            "audience",
            "content_rating",
        }

        missing = required - set(payload)

        if missing:
            raise AIClientError(
                f"Novel concept response missing fields: {sorted(missing)}"
            )

        cleaned = {
            "title": str(payload.get("title") or "").strip()[:200],
            "description": str(payload.get("description") or "").strip(),
            "genre": genre.strip(),
            "audience": audience.strip(),
            "content_rating": content_rating.strip(),
        }

        if not cleaned["title"]:
            raise AIClientError("AI returned an empty novel title.")

        if not cleaned["description"]:
            raise AIClientError("AI returned an empty novel description.")

        return cleaned

    return _generate_payload(
        user=user,
        feature="novel_concept",
        system_prompt=NOVEL_SYSTEM_PROMPT,
        user_prompt=prompt,
        validator=validate,
    )


# ==========================================================
# 2. GENERATE CHAPTER OUTLINE
# ==========================================================

def generate_novel_chapter_outline(
    *,
    user,
    title: str,
    description: str,
    genre: str,
    audience: str,
    content_rating: str,
    chapter_count: int = 12,
    instructions: str = "",
) -> dict[str, Any]:
    """
    Generate a sequential chapter outline for a novel.

    Returns:
        {
            "chapters": [
                {
                    "chapter_number": 1,
                    "title": "...",
                    "summary": "..."
                }
            ]
        }

    Does not create StoryChapter records.
    """

    if chapter_count < 1 or chapter_count > 60:
        raise ValueError("Chapter count must be between 1 and 60.")

    if not title.strip() or not description.strip():
        raise ValueError("Novel title and description are required.")

    prompt = CHAPTER_OUTLINE_PROMPT.format(
        title=title.strip(),
        description=description.strip(),
        genre=genre.strip(),
        audience=audience.strip(),
        content_rating=content_rating.strip(),
        chapter_count=chapter_count,
        instructions=instructions.strip() or "No additional instructions.",
    )

    def validate(payload):
        chapters = payload.get("chapters")

        if not isinstance(chapters, list):
            raise AIClientError("AI returned an invalid chapter outline.")

        if len(chapters) != chapter_count:
            raise AIClientError(
                f"Expected {chapter_count} chapters, received {len(chapters)}."
            )

        cleaned_chapters = []

        for index, chapter in enumerate(chapters, start=1):
            if not isinstance(chapter, dict):
                raise AIClientError(f"Chapter {index} has an invalid format.")

            chapter_number = chapter.get("chapter_number", index)

            if chapter_number != index:
                raise AIClientError(
                    f"Chapter numbering is invalid at chapter {index}."
                )

            chapter_title = str(chapter.get("title") or "").strip()
            summary = str(chapter.get("summary") or "").strip()

            if not chapter_title:
                raise AIClientError(f"Chapter {index} has an empty title.")

            if not summary:
                raise AIClientError(f"Chapter {index} has an empty summary.")

            cleaned_chapters.append({
                "chapter_number": index,
                "title": chapter_title[:200],
                "summary": summary,
            })

        return {"chapters": cleaned_chapters}

    return _generate_payload(
        user=user,
        feature="novel_chapter_outline",
        system_prompt=NOVEL_SYSTEM_PROMPT,
        user_prompt=prompt,
        validator=validate,
    )


# ==========================================================
# 3. GENERATE COMPLETE CHAPTER CONTENT
# ==========================================================

def generate_novel_chapter(
    *,
    user,
    novel_title: str,
    novel_description: str,
    genre: str,
    audience: str,
    content_rating: str,
    chapter_number: int,
    chapter_title: str,
    chapter_summary: str,
    previous_context: str = "",
    instructions: str = "",
    target_word_count: int = 1500,
) -> dict[str, Any]:
    """
    Generate the complete content of one novel chapter.

    Returns:
        chapter_number, title, content

    Can also be used to regenerate an existing chapter.
    Does not save or overwrite StoryChapter records.
    """

    if chapter_number < 1:
        raise ValueError("Chapter number must be at least 1.")

    if target_word_count < 300 or target_word_count > 6000:
        raise ValueError(
            "Target word count must be between 300 and 6000."
        )

    required_inputs = {
        "novel_title": novel_title,
        "novel_description": novel_description,
        "chapter_title": chapter_title,
        "chapter_summary": chapter_summary,
    }

    for field, value in required_inputs.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field.replace('_', ' ').title()} is required."
            )

    prompt = CHAPTER_CONTENT_PROMPT.format(
        novel_title=novel_title.strip(),
        novel_description=novel_description.strip(),
        genre=genre.strip(),
        audience=audience.strip(),
        content_rating=content_rating.strip(),
        chapter_number=chapter_number,
        chapter_title=chapter_title.strip(),
        chapter_summary=chapter_summary.strip(),
        previous_context=previous_context.strip() or "This is the opening chapter.",
        instructions=instructions.strip() or "No additional instructions.",
        target_word_count=target_word_count,
    )

    def validate(payload):
        required = {"chapter_number", "title", "content"}
        missing = required - set(payload)

        if missing:
            raise AIClientError(
                f"Chapter response missing fields: {sorted(missing)}"
            )

        returned_number = payload.get("chapter_number")

        if returned_number != chapter_number:
            raise AIClientError("AI returned an incorrect chapter number.")

        cleaned = {
            "chapter_number": chapter_number,
            "title": str(payload.get("title") or "").strip()[:200],
            "content": str(payload.get("content") or "").strip(),
        }

        if not cleaned["title"]:
            raise AIClientError("AI returned an empty chapter title.")

        if not cleaned["content"]:
            raise AIClientError("AI returned empty chapter content.")

        return cleaned

    return _generate_payload(
        user=user,
        feature="novel_chapter",
        system_prompt=NOVEL_SYSTEM_PROMPT,
        user_prompt=prompt,
        validator=validate,
    )
