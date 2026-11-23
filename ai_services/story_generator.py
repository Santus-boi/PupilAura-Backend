
import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


# =========================================================
# SYSTEM PROMPTS
# =========================================================

STORY_SYSTEM_PROMPT = """
You are a professional creative writer and educational storyteller.

Create original, engaging, age-appropriate stories.
Follow the requested genre, audience, content rating and story structure.

Return valid JSON only.
Do not include Markdown, explanations or code fences.
Never invent existing copyrighted characters or reproduce copyrighted stories.
"""


CARTOON_STORY_SYSTEM_PROMPT = """
You are an expert children's storyteller and educational content designer.

Create engaging, age-appropriate interactive cartoon stories for children.
Use memorable characters, expressive dialogue, simple language and positive
educational lessons.

Every comprehension question must have exactly one correct answer.
All answers must be relevant to the question.

Return valid JSON only.
Do not include Markdown, explanations or code fences.
"""


# =========================================================
# STORY LIBRARY PROMPT
# =========================================================

STORY_LIBRARY_PROMPT = """
Create a complete original story for the PupilAura Story Library.

Story title/topic: {topic}
Genre: {genre}
Target audience: {audience}
Content rating: {content_rating}
Number of chapters: {chapter_count}
Additional instructions: {instructions}

Return JSON with exactly this structure:

{{
    "title": "Story title",
    "description": "An engaging story description",
    "chapters": [
        {{
            "title": "Chapter title",
            "content": "Complete chapter content"
        }}
    ]
}}

Requirements:
- Generate exactly {chapter_count} chapters.
- Each chapter must contain substantial, readable story content.
- Chapters must follow a continuous storyline.
- Give the story a compelling beginning, progressive development
  and satisfying conclusion.
- Avoid repeating the same events or dialogue.
- Respect the selected audience and content rating.
- Do not include chapter numbers in chapter titles.
- Do not include Markdown formatting.
- Do not leave chapter content empty.
"""


# =========================================================
# INTERACTIVE CARTOON STORY PROMPT
# =========================================================

CARTOON_STORY_PROMPT = """
Create an interactive educational cartoon story for PupilAura Play & Learn.

Story topic: {topic}
Category: {category}
Target age: {min_age} to {max_age} years
Number of scenes: {scene_count}
Number of comprehension questions: {question_count}
Educational lesson: {lesson}
Additional instructions: {instructions}

Return JSON with exactly this structure:

{{
    "title": "Story title",
    "description": "Short story description",
    "lesson": "The moral or educational lesson",
    "emoji": "One suitable emoji",
    "cover_emoji": "One suitable cover emoji",
    "estimated_duration_minutes": 5,
    "scenes": [
        {{
            "character_name": "Character name",
            "character_emoji": "Suitable emoji",
            "title": "Scene title",
            "text": "Dialogue or narration for this scene",
            "narration_text": "Narration text"
        }}
    ],
    "questions": [
        {{
            "question_text": "Comprehension question",
            "explanation": "Explanation of the correct answer",
            "answers": [
                {{
                    "answer_text": "Answer option",
                    "is_correct": true
                }},
                {{
                    "answer_text": "Answer option",
                    "is_correct": false
                }},
                {{
                    "answer_text": "Answer option",
                    "is_correct": false
                }},
                {{
                    "answer_text": "Answer option",
                    "is_correct": false
                }}
            ]
        }}
    ]
}}

Requirements:
- Generate exactly {scene_count} scenes.
- Generate exactly {question_count} questions.
- Every scene must advance the storyline.
- Use consistent character names and personalities.
- Make dialogue natural and understandable for the target age.
- Use short, engaging scenes.
- Every scene must have meaningful text.
- Narration text may be similar to the dialogue but should be
  suitable for reading aloud.
- Every question must have exactly four answer options.
- Exactly one answer per question must have is_correct set to true.
- Questions must test understanding of events and the lesson.
- The ending must communicate the requested educational lesson.
- Keep the content appropriate for children.
"""


# =========================================================
# STORY LIBRARY GENERATOR
# =========================================================

def generate_story_library(
    *,
    user,
    topic: str,
    genre: str = "adventure",
    audience: str = "teens",
    content_rating: str = "everyone",
    chapter_count: int = 5,
    instructions: str = "",
) -> dict[str, Any]:

    if not 1 <= chapter_count <= 20:
        raise ValueError("Chapter count must be between 1 and 20.")

    if not topic.strip():
        raise ValueError("A story topic is required.")

    client = AIClient()

    user_prompt = STORY_LIBRARY_PROMPT.format(
        topic=topic.strip(),
        genre=genre,
        audience=audience,
        content_rating=content_rating,
        chapter_count=chapter_count,
        instructions=instructions.strip() or "None",
    )

    start = time.monotonic()

    try:
        payload = client.complete_json(
            system_prompt=STORY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )

        result = _validate_story_library(
            payload,
            expected_chapters=chapter_count,
        )

        record_ai_call(
            user=user,
            feature="story_library",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=int((time.monotonic() - start) * 1000),
        )

        return result

    except AIClientError as exc:
        record_ai_call(
            user=user,
            feature="story_library",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=int((time.monotonic() - start) * 1000),
        )
        raise


def _validate_story_library(
    payload: dict[str, Any],
    expected_chapters: int,
) -> dict[str, Any]:

    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    chapters = payload.get("chapters")

    if not title:
        raise AIClientError("AI returned a story without a title.")

    if not description:
        raise AIClientError("AI returned a story without a description.")

    if not isinstance(chapters, list):
        raise AIClientError("AI returned an invalid chapter structure.")

    if len(chapters) != expected_chapters:
        raise AIClientError(
            f"AI returned {len(chapters)} chapters instead of "
            f"{expected_chapters}."
        )

    validated_chapters = []

    for index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            raise AIClientError(
                f"Chapter {index} has an invalid structure."
            )

        chapter_title = str(chapter.get("title") or "").strip()
        chapter_content = str(chapter.get("content") or "").strip()

        if not chapter_title or not chapter_content:
            raise AIClientError(
                f"Chapter {index} is missing its title or content."
            )

        validated_chapters.append({
            "title": chapter_title[:200],
            "content": chapter_content,
        })

    return {
        "title": title[:200],
        "description": description,
        "chapters": validated_chapters,
    }


# =========================================================
# INTERACTIVE CARTOON STORY GENERATOR
# =========================================================

def generate_cartoon_story(
    *,
    user,
    topic: str,
    category: str = "adventure",
    min_age: int = 3,
    max_age: int = 8,
    scene_count: int = 6,
    question_count: int = 5,
    lesson: str = "",
    instructions: str = "",
) -> dict[str, Any]:

    if not topic.strip():
        raise ValueError("A cartoon story topic is required.")

    if not 1 <= min_age <= 18:
        raise ValueError("Minimum age must be between 1 and 18.")

    if not min_age <= max_age <= 18:
        raise ValueError(
            "Maximum age must be between minimum age and 18."
        )

    if not 3 <= scene_count <= 20:
        raise ValueError("Scene count must be between 3 and 20.")

    if not 1 <= question_count <= 15:
        raise ValueError("Question count must be between 1 and 15.")

    client = AIClient()

    user_prompt = CARTOON_STORY_PROMPT.format(
        topic=topic.strip(),
        category=category,
        min_age=min_age,
        max_age=max_age,
        scene_count=scene_count,
        question_count=question_count,
        lesson=lesson.strip() or "A positive educational lesson",
        instructions=instructions.strip() or "None",
    )

    start = time.monotonic()

    try:
        payload = client.complete_json(
            system_prompt=CARTOON_STORY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )

        result = _validate_cartoon_story(
            payload,
            expected_scenes=scene_count,
            expected_questions=question_count,
        )

        record_ai_call(
            user=user,
            feature="cartoon_story",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=int((time.monotonic() - start) * 1000),
        )

        return result

    except AIClientError as exc:
        record_ai_call(
            user=user,
            feature="cartoon_story",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=int((time.monotonic() - start) * 1000),
        )
        raise


def _validate_cartoon_story(
    payload: dict[str, Any],
    expected_scenes: int,
    expected_questions: int,
) -> dict[str, Any]:

    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    scenes = payload.get("scenes")
    questions = payload.get("questions")

    if not title:
        raise AIClientError("AI returned a cartoon story without a title.")

    if not description:
        raise AIClientError(
            "AI returned a cartoon story without a description."
        )

    if not isinstance(scenes, list) or len(scenes) != expected_scenes:
        raise AIClientError(
            f"AI must return exactly {expected_scenes} scenes."
        )

    if (
        not isinstance(questions, list)
        or len(questions) != expected_questions
    ):
        raise AIClientError(
            f"AI must return exactly {expected_questions} questions."
        )

    validated_scenes = []

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise AIClientError(
                f"Scene {index} has an invalid structure."
            )

        character_name = str(
            scene.get("character_name") or "Narrator"
        ).strip()

        text = str(scene.get("text") or "").strip()

        if not text:
            raise AIClientError(
                f"Scene {index} has no dialogue or narration."
            )

        validated_scenes.append({
            "character_name": character_name[:100],
            "character_emoji": str(
                scene.get("character_emoji") or "📖"
            )[:20],
            "title": str(scene.get("title") or "").strip()[:200],
            "text": text,
            "narration_text": str(
                scene.get("narration_text") or ""
            ).strip(),
        })

    validated_questions = []

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise AIClientError(
                f"Question {index} has an invalid structure."
            )

        question_text = str(
            question.get("question_text") or ""
        ).strip()

        answers = question.get("answers")

        if not question_text:
            raise AIClientError(
                f"Question {index} has no question text."
            )

        if not isinstance(answers, list) or len(answers) != 4:
            raise AIClientError(
                f"Question {index} must have exactly four answers."
            )

        validated_answers = []

        for answer in answers:
            if not isinstance(answer, dict):
                raise AIClientError(
                    f"Question {index} has an invalid answer."
                )

            answer_text = str(
                answer.get("answer_text") or ""
            ).strip()

            if not answer_text:
                raise AIClientError(
                    f"Question {index} contains an empty answer."
                )

            validated_answers.append({
                "answer_text": answer_text[:255],
                "is_correct": answer.get("is_correct") is True,
            })

        correct_count = sum(
            answer["is_correct"] for answer in validated_answers
        )

        if correct_count != 1:
            raise AIClientError(
                f"Question {index} must have exactly one correct answer."
            )

        validated_questions.append({
            "question_text": question_text,
            "explanation": str(
                question.get("explanation") or ""
            ).strip(),
            "answers": validated_answers,
        })

    try:
        duration = int(
            payload.get("estimated_duration_minutes") or 5
        )
    except (TypeError, ValueError):
        duration = 5

    return {
        "title": title[:200],
        "description": description,
        "lesson": str(payload.get("lesson") or "").strip()[:255],
        "emoji": str(payload.get("emoji") or "")[:20],
        "cover_emoji": str(payload.get("cover_emoji") or "")[:50],
        "estimated_duration_minutes": max(1, min(duration, 120)),
        "scenes": validated_scenes,
        "questions": validated_questions,
    }
