import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


EXAM_QUESTION_SYSTEM_PROMPT = """You are an experienced WAEC/NECO/JAMB
examinations setter. You produce accurate, curriculum-aligned multiple-choice
exam questions in strict JSON. Never include markdown or code fences."""


EXAM_QUESTION_PROMPT = """Create {count} {exam_name} exam questions for
{subject_name} ({year}).

Return JSON with exactly this shape:

{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "string — exam-style question, max 300 chars",
      "option_a": "string",
      "option_b": "string",
      "option_c": "string",
      "option_d": "string",
      "correct": "A|B|C|D",
      "explanation": "string — why this answer is correct, max 200 chars",
      "marks": 1
    }}
  ]
}}

Requirements:
- Number from 1 to {count}, sequentially.
- Style: {exam_name}. Difficulty: {difficulty}.
- Exactly 4 options per question.
- Vary the position of the correct option across the set.
- Do NOT reuse the same question twice.
- Keep facts accurate — if unsure, prefer a simpler well-known fact.
"""


def generate_exam_questions(
    *,
    user,
    exam_name: str,
    subject_name: str,
    year: int | str,
    count: int = 10,
    difficulty: str = "standard",
) -> dict[str, Any]:
    """
    Returns {"questions": [{question_number, question_text, option_a..d,
    correct, explanation, marks}, ...]}.
    """
    if count < 1 or count > 60:
        raise ValueError("Question count must be between 1 and 60.")

    client = AIClient()
    user_prompt = EXAM_QUESTION_PROMPT.format(
        count=count,
        exam_name=exam_name,
        subject_name=subject_name,
        year=year,
        difficulty=difficulty,
    )

    start = time.monotonic()
    try:
        payload = client.complete_json(
            system_prompt=EXAM_QUESTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={"type": "object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="exam_questions",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )
        return _validate_exam_questions(payload)
    except AIClientError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        record_ai_call(
            user=user,
            feature="exam_questions",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )
        raise


def _validate_exam_questions(payload: dict[str, Any]) -> dict[str, Any]:
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise AIClientError("AI returned no exam questions.")

    cleaned = []
    for i, q in enumerate(questions, start=1):
        correct = str(q.get("correct") or "").strip().upper()
        if correct not in ("A", "B", "C", "D"):
            raise AIClientError(
                f"Question {i}: 'correct' must be A/B/C/D (got '{correct}')."
            )

        cleaned.append({
            "question_number": int(q.get("question_number") or i),
            "question_text": str(q.get("question_text") or "").strip()[:600],
            "option_a": str(q.get("option_a") or "").strip()[:300],
            "option_b": str(q.get("option_b") or "").strip()[:300],
            "option_c": str(q.get("option_c") or "").strip()[:300],
            "option_d": str(q.get("option_d") or "").strip()[:300],
            "correct": correct,
            "explanation": str(q.get("explanation") or "").strip()[:500],
            "marks": int(q.get("marks") or 1),
        })

    return {"questions": cleaned}