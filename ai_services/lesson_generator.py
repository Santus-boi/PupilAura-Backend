import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


LESSON_SYSTEM_PROMPT = """You are an expert curriculum designer for Nigerian
schools (WAEC, NECO, JAMB aligned). You produce complete, accurate lesson
plans in strict JSON. Never include markdown, code fences, or commentary.
Always return exactly the fields requested, nothing more, nothing less."""


LESSON_USER_PROMPT_TEMPLATE = """Write a complete lesson plan in JSON with
exactly these keys:

{{
  "title": "string — clear lesson title, max 120 chars",
  "description": "string — one-sentence summary, max 200 chars",
  "objectives": "string — 3-5 bullet learning objectives, each on its own line starting with '- '",
  "content": "string — the main lesson content, 3-6 paragraphs, plain text, no headings",
  "examples": "string — 2-3 worked examples with clear reasoning, plain text",
  "key_points": "string — 4-6 bullet takeaways, each on its own line starting with '- '",
  "activity": "string — 1 hands-on classroom activity students can complete, plain text",
  "practical": "string — 1 practical/lab exercise, or empty string if not applicable",
  "estimated_minutes": 40
}}

Context:
- Subject: {subject}
- Class: {school_class}
- Education Level: {education_level}
- Term: {term}
- Week: {week}
- Lesson Topic: {topic}
- Curriculum Level: {level_description}

Return ONLY the JSON object."""


def generate_lesson_content(
    *,
    user,
    topic: str,
    subject: str,
    school_class: str,
    education_level: str,
    term: str = "",
    week: str = "",
    level_description: str = "standard secondary school",
) -> dict[str, Any]:
    """
    Returns a dict with keys: title, description, objectives, content,
    examples, key_points, activity, practical, estimated_minutes.

    Raises AIClientError on failure.
    """
    client = AIClient()

    user_prompt = LESSON_USER_PROMPT_TEMPLATE.format(
        topic=topic.strip(),
        subject=subject.strip(),
        school_class=school_class.strip(),
        education_level=education_level.strip(),
        term=term.strip() or "Not specified",
        week=week.strip() or "Not specified",
        level_description=level_description,
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=LESSON_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        record_ai_call(
            user=user,
            feature="lesson",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_lesson_payload(payload)

    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="lesson",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_lesson_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "title", "description", "objectives", "content",
        "examples", "key_points", "activity", "practical",
    }
    missing = required - set(payload)
    if missing:
        raise AIClientError(
            f"AI lesson response missing fields: {sorted(missing)}"
        )

    cleaned = {
        "title": str(payload["title"]).strip()[:200],
        "description": str(payload["description"]).strip()[:500],
        "objectives": str(payload["objectives"]).strip(),
        "content": str(payload["content"]).strip(),
        "examples": str(payload["examples"]).strip(),
        "key_points": str(payload["key_points"]).strip(),
        "activity": str(payload["activity"]).strip(),
        "practical": str(payload.get("practical") or "").strip(),
        "estimated_minutes": int(payload.get("estimated_minutes") or 40),
    }

    if not cleaned["title"]:
        raise AIClientError("AI returned an empty lesson title.")
    if not cleaned["content"]:
        raise AIClientError("AI returned empty lesson content.")

    return cleaned
    