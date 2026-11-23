import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


TECH_LESSON_SYSTEM_PROMPT = """You are a hands-on digital-skills instructor.
Produce practical, project-driven lessons in strict JSON. Never include
markdown or code fences."""


TECH_LESSON_PROMPT = """Write a tech lesson.

Course: {course_title}
Module: {module_title}
Lesson topic: {topic}
Level: {difficulty}

Return JSON with exactly these keys:

{{
  "title": "string — clear lesson title, max 120 chars",
  "description": "string — one-sentence summary, max 200 chars",
  "objectives": "string — 3-5 bullet learning objectives, each on its own line starting with '- '",
  "content": "string — main lesson content, 3-6 paragraphs, may include inline code samples",
  "practical": "string — a hands-on coding exercise or lab the student can complete",
  "project": "string — a small project that reinforces this lesson, or empty string",
  "key_points": "string — 4-6 bullets, each on its own line starting with '- '",
  "estimated_minutes": 45
}}

Requirements:
- Language: plain text. For code samples, use indented code blocks.
- Level: {difficulty}. Prefer hands-on learning over theory.
"""


def generate_tech_lesson(
    *,
    user,
    course_title: str,
    module_title: str,
    topic: str,
    difficulty: str = "standard",
) -> dict[str, Any]:
    client = AIClient()
    user_prompt = TECH_LESSON_PROMPT.format(
        course_title=course_title,
        module_title=module_title,
        topic=topic,
        difficulty=difficulty,
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=TECH_LESSON_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_lesson",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_tech_lesson(payload)
    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_lesson",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_tech_lesson(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"title", "description", "content", "practical", "project"}
    missing = required - set(payload)
    if missing:
        raise AIClientError(
            f"AI lesson response missing fields: {sorted(missing)}"
        )
    return {
        "title": str(payload["title"]).strip()[:200],
        "description": str(payload["description"]).strip()[:500],
        "objectives": str(payload.get("objectives") or "").strip(),
        "content": str(payload["content"]).strip(),
        "practical": str(payload["practical"]).strip(),
        "project": str(payload["project"]).strip(),
        "key_points": str(payload.get("key_points") or "").strip(),
        "estimated_minutes": int(payload.get("estimated_minutes") or 45),
    }