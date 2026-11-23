
import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


CARTOON_STORY_SYSTEM_PROMPT = """You are an expert children's storyteller,
early childhood educator and educational content designer.

Create original, entertaining, age-appropriate interactive cartoon stories.

Your stories must:
- Use simple language suitable for the specified age group.
- Have interesting characters with distinct personalities.
- Include engaging dialogue and descriptive narration.
- Develop a clear beginning, middle and ending.
- Teach a meaningful lesson naturally through the story.
- Encourage kindness, honesty, courage, curiosity and positive behaviour.
- Avoid graphic violence, frightening descriptions and inappropriate themes.
- Use culturally inclusive characters and settings.
- Create scenes that can be illustrated as colourful cartoon images.

Return strictly valid JSON. Never include markdown, code fences,
or commentary outside the JSON object."""


CARTOON_STORY_PROMPT = """Create a complete interactive children's cartoon story.

Story information:
- Preferred title: {title}
- Category: {category}
- Minimum reader age: {min_age}
- Maximum reader age: {max_age}
- Story idea: {story_idea}
- Preferred lesson: {lesson}
- Number of scenes: {scene_count}
- Number of comprehension questions: {question_count}
- Additional instructions: {instructions}

Return JSON with exactly these keys and structure:

{{
    "title": "string — engaging story title",
    "description": "string — short story description",
    "category": "{category}",
    "emoji": "string — suitable story emoji",
    "cover_emoji": "string — suitable cover emoji",
    "min_age": {min_age},
    "max_age": {max_age},
    "estimated_duration_minutes": 5,
    "lesson": "string — the moral or educational lesson",

    "scenes": [
        {{
            "scene_number": 1,
            "character_name": "string — speaking character or Narrator",
            "character_emoji": "string — character emoji",
            "title": "string — short scene title",
            "text": "string — dialogue or narration displayed to readers",
            "narration_text": "string — natural spoken narration",
            "illustration_prompt": "string — detailed visual description for a cartoon illustration"
        }}
    ],

    "questions": [
        {{
            "question_number": 1,
            "question_text": "string — comprehension question",
            "explanation": "string — simple explanation of the correct answer",
            "answers": [
                {{
                    "answer_text": "string — answer option",
                    "is_correct": true,
                    "order": 1
                }}
            ]
        }}
    ]
}}

Scene requirements:
- Return exactly {scene_count} scenes.
- Number scenes sequentially starting from 1.
- Every scene must move the story forward.
- Use character dialogue and narration naturally.
- Keep dialogue short and easy to understand.
- Make characters and their actions consistent across scenes.
- Each illustration prompt must describe the characters, setting,
  actions, expressions and visual composition.
- Keep character appearances visually consistent across scenes.
- Avoid putting multiple unrelated events into one scene.
- Narration must sound natural when read aloud.
- If narration_text is unnecessary, repeat the scene text.

Question requirements:
- Return exactly {question_count} questions.
- Number questions sequentially starting from 1.
- Each question must relate to events or lessons in the story.
- Provide between 2 and 4 answer options per question.
- Exactly ONE answer per question must have is_correct set to true.
- Make incorrect answers plausible but clearly distinguishable.
- Provide a simple explanation for every correct answer.

General requirements:
- Respect the specified age range.
- Keep the story entertaining rather than sounding like a textbook.
- Make the moral lesson clear without excessive preaching.
- Do not use scary or inappropriate content.
- Return all requested fields.
"""


def _record_cartoon_ai_call(
    *,
    user,
    client: AIClient,
    start: float,
    success: bool,
    error: Exception | None = None,
) -> None:
    duration_ms = int((time.monotonic() - start) * 1000)

    record_ai_call(
        user=user,
        feature="cartoon_story",
        provider=client.provider,
        model=client.model,
        success=success,
        error_message=str(error)[:1000] if error else "",
        duration_ms=duration_ms,
    )


def generate_cartoon_story(
    *,
    user,
    category: str,
    min_age: int = 3,
    max_age: int = 8,
    title: str = "",
    story_idea: str = "",
    lesson: str = "",
    scene_count: int = 6,
    question_count: int = 3,
    instructions: str = "",
) -> dict[str, Any]:
    """
    Generate a complete interactive cartoon story.

    Returns:
        Story details
        Sequential scenes
        Illustration prompts
        Comprehension questions and answers

    Does not create or modify database records.
    """

    allowed_categories = {
        "friendship",
        "honesty",
        "kindness",
        "adventure",
        "courage",
        "animals",
        "family",
        "nature",
        "educational",
    }

    if category not in allowed_categories:
        raise ValueError(
            f"Invalid cartoon story category: {category}."
        )

    if not isinstance(min_age, int) or not isinstance(max_age, int):
        raise ValueError("Minimum and maximum ages must be integers.")

    if min_age < 1 or max_age > 17 or min_age > max_age:
        raise ValueError("Provide a valid age range between 1 and 17.")

    if not 3 <= scene_count <= 20:
        raise ValueError("Scene count must be between 3 and 20.")

    if not 1 <= question_count <= 10:
        raise ValueError("Question count must be between 1 and 10.")

    prompt = CARTOON_STORY_PROMPT.format(
        title=title.strip() or "Create an original title.",
        category=category,
        min_age=min_age,
        max_age=max_age,
        story_idea=story_idea.strip() or "Create an original story idea.",
        lesson=lesson.strip() or "Choose a suitable moral lesson.",
        scene_count=scene_count,
        question_count=question_count,
        instructions=instructions.strip() or "No additional instructions.",
    )

    def validate(payload: dict[str, Any]) -> dict[str, Any]:
        required = {
            "title",
            "description",
            "emoji",
            "cover_emoji",
            "estimated_duration_minutes",
            "lesson",
            "scenes",
            "questions",
        }

        missing = required - set(payload)

        if missing:
            raise AIClientError(
                f"Cartoon story response missing fields: {sorted(missing)}"
            )

        cleaned_title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        moral_lesson = str(payload.get("lesson") or "").strip()

        if not cleaned_title:
            raise AIClientError("AI returned an empty cartoon story title.")

        if not description:
            raise AIClientError("AI returned an empty story description.")

        if not moral_lesson:
            raise AIClientError("AI returned an empty moral lesson.")

        raw_scenes = payload.get("scenes")
        raw_questions = payload.get("questions")

        if not isinstance(raw_scenes, list):
            raise AIClientError("AI returned an invalid scenes collection.")

        if len(raw_scenes) != scene_count:
            raise AIClientError(
                f"Expected {scene_count} scenes, received {len(raw_scenes)}."
            )

        if not isinstance(raw_questions, list):
            raise AIClientError("AI returned an invalid questions collection.")

        if len(raw_questions) != question_count:
            raise AIClientError(
                f"Expected {question_count} questions, "
                f"received {len(raw_questions)}."
            )

        cleaned_scenes = []

        for index, scene in enumerate(raw_scenes, start=1):
            if not isinstance(scene, dict):
                raise AIClientError(
                    f"Scene {index} has an invalid format."
                )

            if scene.get("scene_number") != index:
                raise AIClientError(
                    f"Scene numbering is invalid at scene {index}."
                )

            character_name = str(
                scene.get("character_name") or "Narrator"
            ).strip()

            character_emoji = str(
                scene.get("character_emoji") or "📖"
            ).strip()

            scene_title = str(scene.get("title") or "").strip()
            scene_text = str(scene.get("text") or "").strip()

            narration = str(
                scene.get("narration_text") or scene_text
            ).strip()

            illustration_prompt = str(
                scene.get("illustration_prompt") or ""
            ).strip()

            if not scene_title:
                raise AIClientError(
                    f"Scene {index} has an empty title."
                )

            if not scene_text:
                raise AIClientError(
                    f"Scene {index} has empty dialogue or narration."
                )

            if not illustration_prompt:
                raise AIClientError(
                    f"Scene {index} has no illustration prompt."
                )

            cleaned_scenes.append({
                "scene_number": index,
                "character_name": character_name[:100],
                "character_emoji": character_emoji[:20],
                "title": scene_title[:200],
                "text": scene_text,
                "narration_text": narration,
                "illustration_prompt": illustration_prompt,
            })

        cleaned_questions = []

        for index, question in enumerate(raw_questions, start=1):
            if not isinstance(question, dict):
                raise AIClientError(
                    f"Question {index} has an invalid format."
                )

            if question.get("question_number") != index:
                raise AIClientError(
                    f"Question numbering is invalid at question {index}."
                )

            question_text = str(
                question.get("question_text") or ""
            ).strip()

            explanation = str(
                question.get("explanation") or ""
            ).strip()

            raw_answers = question.get("answers")

            if not question_text:
                raise AIClientError(
                    f"Question {index} has empty question text."
                )

            if not isinstance(raw_answers, list):
                raise AIClientError(
                    f"Question {index} has an invalid answers collection."
                )

            if not 2 <= len(raw_answers) <= 4:
                raise AIClientError(
                    f"Question {index} must have between 2 and 4 answers."
                )

            cleaned_answers = []

            for answer_index, answer in enumerate(raw_answers, start=1):
                if not isinstance(answer, dict):
                    raise AIClientError(
                        f"Question {index}, answer {answer_index} is invalid."
                    )

                answer_text = str(
                    answer.get("answer_text") or ""
                ).strip()

                if not answer_text:
                    raise AIClientError(
                        f"Question {index} has an empty answer option."
                    )

                cleaned_answers.append({
                    "answer_text": answer_text[:255],
                    "is_correct": bool(answer.get("is_correct", False)),
                    "order": answer_index,
                })

            correct_answers = sum(
                answer["is_correct"] for answer in cleaned_answers
            )

            if correct_answers != 1:
                raise AIClientError(
                    f"Question {index} must have exactly one correct answer."
                )

            cleaned_questions.append({
                "question_number": index,
                "question_text": question_text,
                "explanation": explanation,
                "answers": cleaned_answers,
            })

        try:
            duration = int(
                payload.get("estimated_duration_minutes") or 5
            )
        except (TypeError, ValueError):
            raise AIClientError(
                "AI returned an invalid estimated story duration."
            )

        if duration < 1 or duration > 120:
            raise AIClientError(
                "Story duration must be between 1 and 120 minutes."
            )

        return {
            "title": cleaned_title[:200],
            "description": description,
            "category": category,
            "emoji": str(payload.get("emoji") or "📖")[:20],
            "cover_emoji": str(payload.get("cover_emoji") or "📚")[:50],
            "min_age": min_age,
            "max_age": max_age,
            "estimated_duration_minutes": duration,
            "lesson": moral_lesson[:255],
            "scenes": cleaned_scenes,
            "questions": cleaned_questions,
        }

    client = AIClient()
    start = time.monotonic()

    try:
        payload = client.complete_json(
            system_prompt=CARTOON_STORY_SYSTEM_PROMPT,
            user_prompt=prompt,
            schema={"type": "object"},
        )

        cleaned = validate(payload)

        _record_cartoon_ai_call(
            user=user,
            client=client,
            start=start,
            success=True,
        )

        return cleaned

    except AIClientError as exc:
        _record_cartoon_ai_call(
            user=user,
            client=client,
            start=start,
            success=False,
            error=exc,
        )
        raise
