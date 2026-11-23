import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


TECH_MODULE_SYSTEM_PROMPT = """You are a digital-skills curriculum designer.
Produce a structured module with lessons in strict JSON. Never include
markdown or code fences."""


TECH_MODULE_PROMPT = """Design one module for a "{course_title}" course.

Module topic: {topic}
Lessons to include: {lesson_count}
Difficulty: {difficulty}

Return JSON with exactly this shape:

{{
  "title": "string — clear module title, max 120 chars",
  "description": "string — 2-3 sentence description, max 400 chars",
  "lessons": [
    {{
      "title": "string — lesson title, max 120 chars",
      "description": "string — 1-2 sentence summary, max 240 chars"
    }}
  ],
  "estimated_minutes": 60
}}

Requirements:
- Exactly {lesson_count} lessons, in progressive order.
- Each lesson teaches one distinct concept.
- No duplicate or near-duplicate lesson titles.
"""


def generate_tech_module(
    *,
    user,
    course_title: str,
    topic: str,
    lesson_count: int = 4,
    difficulty: str = "standard",
) -> dict[str, Any]:
    if lesson_count < 2 or lesson_count > 12:
        raise ValueError("Lesson count must be between 2 and 12.")

    client = AIClient()
    user_prompt = TECH_MODULE_PROMPT.format(
        course_title=course_title,
        topic=topic,
        lesson_count=lesson_count,
        difficulty=difficulty,
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=TECH_MODULE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_module",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_tech_module(payload)
    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_module",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_tech_module(payload: dict[str, Any]) -> dict[str, Any]:
    lessons = payload.get("lessons")
    if not isinstance(lessons, list) or not lessons:
        raise AIClientError("AI returned no lessons.")

    cleaned_lessons = []
    for i, lesson in enumerate(lessons, start=1):
        title = str(lesson.get("title") or "").strip()
        if not title:
            raise AIClientError(f"Lesson {i}: empty title.")
        cleaned_lessons.append({
            "title": title[:200],
            "description": str(lesson.get("description") or "").strip()[:500],
        })

    return {
        "title": str(payload.get("title") or "").strip()[:200],
        "description": str(payload.get("description") or "").strip()[:1000],
        "lessons": cleaned_lessons,
        "estimated_minutes": int(payload.get("estimated_minutes") or 60),
    }