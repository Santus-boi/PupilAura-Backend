import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


QUIZ_SYSTEM_PROMPT = """You are an expert assessment designer creating
WAEC/NECO/JAMB-style multiple-choice questions. Return strict JSON only.
Never include markdown or code fences."""


QUIZ_USER_PROMPT_TEMPLATE = """Create {count} multiple-choice quiz questions
based on the lesson below. Return JSON with exactly this shape:

{{
  "title": "string — short quiz title, max 100 chars",
  "pass_mark": {pass_mark},
  "questions": [
    {{
      "question_text": "string — the question, max 250 chars",
      "explanation": "string — why the correct answer is correct, max 200 chars",
      "marks": 1,
      "choices": [
        {{"text": "string", "is_correct": true}},
        {{"text": "string", "is_correct": false}},
        {{"text": "string", "is_correct": false}},
        {{"text": "string", "is_correct": false}}
      ]
    }}
  ]
}}

Requirements:
- Exactly 4 choices per question.
- Exactly 1 choice per question has is_correct = true.
- Difficulty: {difficulty}
- Do NOT reuse the same answer letter position for every question.

Lesson title: {lesson_title}
Lesson content:
{lesson_content}
"""


def generate_quiz_questions(
    *,
    user,
    lesson_title: str,
    lesson_content: str,
    count: int = 5,
    pass_mark: int = 50,
    difficulty: str = "standard",
) -> dict[str, Any]:
    """
    Returns a dict with: title, pass_mark, questions[]
    Each question has: question_text, explanation, marks, choices[]
    Each choice has: text, is_correct

    Raises AIClientError on failure.
    """
    if count < 1 or count > 30:
        raise ValueError("Question count must be between 1 and 30.")

    client = AIClient()

    user_prompt = QUIZ_USER_PROMPT_TEMPLATE.format(
        count=count,
        pass_mark=pass_mark,
        difficulty=difficulty,
        lesson_title=lesson_title.strip(),
        lesson_content=lesson_content.strip()[:8000],  # guard against huge lessons
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=QUIZ_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="quiz",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_quiz_payload(payload, expected_count=count)

    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="quiz",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_quiz_payload(payload: dict[str, Any], expected_count: int) -> dict:
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise AIClientError("AI returned no quiz questions.")

    cleaned_questions = []
    for i, q in enumerate(questions, start=1):
        text = str(q.get("question_text") or "").strip()
        if not text:
            raise AIClientError(f"Question {i} has empty text.")

        choices = q.get("choices") or []
        if len(choices) != 4:
            raise AIClientError(
                f"Question {i} must have exactly 4 choices (got {len(choices)})."
            )

        correct_count = sum(1 for c in choices if c.get("is_correct"))
        if correct_count != 1:
            raise AIClientError(
                f"Question {i} must have exactly 1 correct choice "
                f"(got {correct_count})."
            )

        cleaned_questions.append({
            "question_text": text[:500],
            "explanation": str(q.get("explanation") or "").strip()[:500],
            "marks": int(q.get("marks") or 1),
            "choices": [
                {
                    "text": str(c.get("text") or "").strip()[:500],
                    "is_correct": bool(c.get("is_correct")),
                }
                for c in choices
            ],
        })

    if len(cleaned_questions) < expected_count:
        # AI under-produced; not a hard failure — caller can retry or accept fewer.
        pass

    return {
        "title": str(payload.get("title") or "Generated Quiz").strip()[:200],
        "pass_mark": int(payload.get("pass_mark") or 50),
        "questions": cleaned_questions,
    }