import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


TECH_COURSE_SYSTEM_PROMPT = """You are a curriculum designer for
digital-skills courses (web development, Python, JavaScript, cybersecurity,
data science, etc.). You produce structured course outlines in strict JSON.
Never include markdown or code fences."""


TECH_COURSE_PROMPT = """Design a tech course outline.

Category: {category}
Primary topic: {topic}
Target audience: {audience}
Difficulty: {difficulty}
Approximate course length: {length} modules

Return JSON with exactly this shape:

{{
  "title": "string — clear course title, max 120 chars",
  "description": "string — 2-3 sentence course description, max 500 chars",
  "module_titles": [
    "Module 1: string",
    "Module 2: string",
    "..."
  ],
  "learning_outcomes": "string — 3-5 bullets, each on its own line starting with '- '",
  "estimated_hours": 10
}}

Requirements:
- {length} modules total, each a clear progressive step.
- Each module title starts with "Module N:".
- Learning outcomes should be concrete and testable.
"""


def generate_tech_course(
    *,
    user,
    category: str,
    topic: str,
    audience: str = "beginners",
    difficulty: str = "standard",
    length: int = 6,
) -> dict[str, Any]:
    if length < 3 or length > 20:
        raise ValueError("Module count must be between 3 and 20.")

    client = AIClient()
    user_prompt = TECH_COURSE_PROMPT.format(
        category=category,
        topic=topic,
        audience=audience,
        difficulty=difficulty,
        length=length,
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=TECH_COURSE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_course",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_tech_course(payload, expected_modules=length)
    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="tech_course",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_tech_course(payload: dict[str, Any], expected_modules: int) -> dict:
    modules = payload.get("module_titles")
    if not isinstance(modules, list) or len(modules) < 1:
        raise AIClientError("AI returned no module titles.")

    return {
        "title": str(payload.get("title") or "").strip()[:200],
        "description": str(payload.get("description") or "").strip()[:1000],
        "module_titles": [str(m).strip()[:200] for m in modules],
        "learning_outcomes": str(payload.get("learning_outcomes") or "").strip(),
        "estimated_hours": int(payload.get("estimated_hours") or 10),
    }