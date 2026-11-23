
import time
from typing import Any

from .client import AIClient, AIClientError
from .logging import record_ai_call


# =========================================================
# EXAM RESOURCE GENERATION
# =========================================================

RESOURCE_SYSTEM_PROMPT = """
You are an expert examination preparation content developer
specializing in WAEC, NECO and JAMB curricula.

You create accurate, educationally sound and age-appropriate
examination preparation materials.

Follow the requested resource type exactly.

Return only a valid JSON object.
Do not include Markdown, code fences or text outside the JSON.

IMPORTANT:
Never claim that an AI-generated question is an authentic
historical WAEC, NECO or JAMB examination question.

When generating questions, create original examination-style
practice questions unless verified source material is explicitly
provided in the prompt.
"""


RESOURCE_TYPES = {
    "past_questions",
    "solutions",
    "lesson",
    "practical",
    "mock_exam",
    "revision",
}


RESOURCE_PROMPTS = {

    # -----------------------------------------------------
    # LESSON
    # -----------------------------------------------------

    "lesson": """
Create a comprehensive examination lesson.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Clear lesson title",
    "description": "One-sentence lesson summary",
    "content": "Detailed teaching content explaining the topic",
    "structured_content": {{
        "objectives": "Learning objectives, one per line",
        "definitions": "Important definitions",
        "content": "Detailed lesson explanation",
        "examples": "Relevant worked examples",
        "key_points": "Important examination points, one per line",
        "activity": "A learning activity for the student"
    }}
}}

Requirements:
- Explain concepts clearly and progressively.
- Include accurate subject-specific information.
- Include relevant formulas and examples where appropriate.
- Make the lesson useful for examination preparation.
""",

    # -----------------------------------------------------
    # PRACTICAL
    # -----------------------------------------------------

    "practical": """
Create a practical examination preparation resource.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Clear practical title",
    "description": "One-sentence summary",
    "content": "Overview of the practical exercise",
    "structured_content": {{
        "objectives": "Practical learning objectives",
        "materials": "Required materials and equipment",
        "procedures": "Step-by-step practical procedures",
        "activities": "Practical activities for students",
        "expected_results": "Expected observations or results",
        "safety_notes": "Relevant safety precautions"
    }}
}}

Requirements:
- Use realistic and subject-appropriate procedures.
- Number the procedures clearly.
- Explain expected observations.
- Include safety precautions where applicable.
""",

    # -----------------------------------------------------
    # REVISION
    # -----------------------------------------------------

    "revision": """
Create an examination revision resource.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Clear revision title",
    "description": "One-sentence revision summary",
    "content": "A concise but useful revision overview",
    "structured_content": {{
        "topic": "Main topic",
        "summary": "Concise topic summary",
        "key_points": "Important facts and points, one per line",
        "formulas": "Relevant formulas and explanations, if applicable",
        "revision_exercises": "Revision questions and exercises"
    }}
}}

Requirements:
- Focus on high-value examination knowledge.
- Highlight important facts and concepts.
- Include formulas only where relevant.
- Provide useful revision exercises.
""",

    # -----------------------------------------------------
    # PAST QUESTIONS
    # -----------------------------------------------------

    "past_questions": """
Create an original examination-style practice question set.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Practice question set title",
    "description": "Description identifying this as AI-generated practice material",
    "content": "Short introduction and instructions",
    "questions": [
        {{
            "question_number": 1,
            "question_type": "mcq",
            "question_text": "Question text",
            "choices": [
                {{"text": "Option A", "is_correct": false}},
                {{"text": "Option B", "is_correct": true}},
                {{"text": "Option C", "is_correct": false}},
                {{"text": "Option D", "is_correct": false}}
            ],
            "correct_answer": "Option B",
            "solution": "Detailed explanation of the correct answer",
            "explanation": "Additional explanation if necessary",
            "marks": 1
        }}
    ]
}}

Requirements:
- Generate 10 original practice questions.
- Use a mixture of appropriate examination question formats.
- MCQ questions must have at least four answer choices.
- Exactly one MCQ choice must be correct.
- Theory and practical questions must have an appropriate written answer.
- Include correct answers and useful explanations.
- Do not claim these are authentic historical examination questions.
- Do not fabricate examination years, paper references or source citations.
- The questions should test the selected topic and difficulty.
""",

    # -----------------------------------------------------
    # SOLUTIONS
    # -----------------------------------------------------

    "solutions": """
Create an examination question-and-solution resource.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Question and solution resource title",
    "description": "One-sentence description",
    "content": "Short introduction to the questions and solutions",
    "questions": [
        {{
            "question_number": 1,
            "question_type": "mcq",
            "question_text": "Question text",
            "choices": [
                {{"text": "Option A", "is_correct": false}},
                {{"text": "Option B", "is_correct": true}},
                {{"text": "Option C", "is_correct": false}},
                {{"text": "Option D", "is_correct": false}}
            ],
            "correct_answer": "Option B",
            "solution": "Detailed step-by-step solution",
            "explanation": "Additional explanation",
            "marks": 1
        }}
    ]
}}

Requirements:
- Generate 5 original examination-style questions with solutions.
- Include the complete question before its answer.
- Include detailed workings for calculation-based questions.
- MCQ questions must have at least four choices and exactly one correct choice.
- Theory and practical questions must include appropriate written answers.
- Never invent historical examination sources.
- These questions may be created independently without an existing Past Questions resource.
""",

    # -----------------------------------------------------
    # MOCK EXAM
    # -----------------------------------------------------

    "mock_exam": """
Create a complete examination mock test.

Examination: {exam_name}
Subject: {subject_name}
Year reference: {year}
Topic: {topic}
Difficulty: {difficulty}

Return JSON with exactly these keys:

{{
    "title": "Mock examination title",
    "description": "One-sentence mock examination description",
    "content": "General examination overview",
    "structured_content": {{
        "instructions": "Instructions for candidates",
        "duration_minutes": 60,
        "total_marks": 20
    }},
    "questions": [
        {{
            "question_number": 1,
            "question_type": "mcq",
            "question_text": "Question text",
            "choices": [
                {{"text": "Option A", "is_correct": false}},
                {{"text": "Option B", "is_correct": true}},
                {{"text": "Option C", "is_correct": false}},
                {{"text": "Option D", "is_correct": false}}
            ],
            "correct_answer": "Option B",
            "solution": "Detailed answer and explanation",
            "explanation": "Additional explanation",
            "marks": 1
        }}
    ]
}}

Requirements:
- Generate 20 examination questions.
- Include appropriate examination instructions.
- Ensure the total marks equal the sum of question marks.
- Include an answer key and explanations.
- MCQ questions must have at least four choices and exactly one correct choice.
- Use theory or practical questions where appropriate.
- Questions must test the selected topic.
- This is an AI-generated mock examination, not an official examination paper.
""",
}


# =========================================================
# RESOURCE GENERATION
# =========================================================

def generate_exam_resource(
    *,
    user,
    exam_name: str,
    subject_name: str,
    year: int | str,
    resource_type: str,
    topic: str,
    difficulty: str = "standard",
) -> dict[str, Any]:

    resource_type = (resource_type or "").strip().lower()

    if resource_type not in RESOURCE_TYPES:
        raise AIClientError(
            f"Unsupported exam resource type: {resource_type}"
        )

    difficulty = (difficulty or "standard").strip().lower()

    if difficulty not in {
        "easy",
        "medium",
        "hard",
        "standard",
    }:
        raise AIClientError(
            "Invalid difficulty level selected."
        )

    client = AIClient()

    user_prompt = RESOURCE_PROMPTS[resource_type].format(
        exam_name=exam_name,
        subject_name=subject_name,
        year=year,
        topic=topic,
        difficulty=difficulty,
    )

    start = time.monotonic()

    try:
        payload = client.complete_json(
            system_prompt=RESOURCE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema={
                "type": "object",
            },
        )

        validated_payload = _validate_exam_resource(
            payload,
            resource_type=resource_type,
        )

        duration_ms = int(
            (time.monotonic() - start) * 1000
        )

        record_ai_call(
            user=user,
            feature="exam_resource",
            provider=client.provider,
            model=client.model,
            success=True,
            duration_ms=duration_ms,
        )

        return validated_payload

    except AIClientError as exc:
        duration_ms = int(
            (time.monotonic() - start) * 1000
        )

        record_ai_call(
            user=user,
            feature="exam_resource",
            provider=client.provider,
            model=client.model,
            success=False,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
        )

        raise


# =========================================================
# RESOURCE VALIDATION HELPERS
# =========================================================

def _resource_text(value, field_name, required=True, max_length=None):
    if value is None:
        value = ""

    if not isinstance(value, (str, int, float)):
        raise AIClientError(
            f"Invalid AI response for {field_name}."
        )

    value = str(value).strip()

    if required and not value:
        raise AIClientError(
            f"AI resource response is missing {field_name}."
        )

    if max_length:
        value = value[:max_length]

    return value


def _validate_resource_questions(questions):
    if not isinstance(questions, list) or not questions:
        raise AIClientError(
            "AI resource response must contain at least one question."
        )

    validated_questions = []

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise AIClientError(
                f"Invalid question data at question {index}."
            )

        question_text = _resource_text(
            question.get("question_text"),
            f"question {index} text",
        )

        question_type = question.get("question_type") or "mcq"

        if not isinstance(question_type, str):
            raise AIClientError(
                f"Invalid question type at question {index}."
            )

        question_type = question_type.strip().lower()

        if question_type not in {"mcq", "theory", "practical"}:
            raise AIClientError(
                f"Invalid question type at question {index}."
            )

        try:
            marks = int(question.get("marks") or 1)
        except (TypeError, ValueError):
            raise AIClientError(
                f"Invalid marks value at question {index}."
            )

        if marks < 1:
            raise AIClientError(
                f"Question {index} must have at least one mark."
            )

        choices = question.get("choices") or []

        if not isinstance(choices, list):
            raise AIClientError(
                f"Invalid answer choices at question {index}."
            )

        validated_choices = []

        for choice_index, choice in enumerate(choices, start=1):
            if not isinstance(choice, dict):
                raise AIClientError(
                    f"Invalid answer choice at question {index}."
                )

            choice_text = _resource_text(
                choice.get("text"),
                f"answer choice in question {index}",
            )

            is_correct = choice.get("is_correct", False)

            if not isinstance(is_correct, bool):
                raise AIClientError(
                    f"Invalid correct-answer flag in question "
                    f"{index}, choice {choice_index}."
                )

            validated_choices.append({
                "text": choice_text,
                "is_correct": is_correct,
            })

        if question_type == "mcq":
            if len(validated_choices) < 4:
                raise AIClientError(
                    f"Question {index} must have at least four choices."
                )

            correct_count = sum(
                1 for choice in validated_choices
                if choice["is_correct"]
            )

            if correct_count != 1:
                raise AIClientError(
                    f"Question {index} must have exactly one correct choice."
                )

        correct_answer = _resource_text(
            question.get("correct_answer"),
            f"correct answer for question {index}",
            required=False,
        )

        if question_type == "mcq" and not correct_answer:
            correct_answer = next(
                choice["text"]
                for choice in validated_choices
                if choice["is_correct"]
            )

        if question_type in {"theory", "practical"} and not correct_answer:
            raise AIClientError(
                f"Question {index} requires a written correct answer."
            )

        solution = _resource_text(
            question.get("solution"),
            f"solution for question {index}",
            required=False,
        )

        explanation = _resource_text(
            question.get("explanation"),
            f"explanation for question {index}",
            required=False,
        )

        try:
            question_number = int(
                question.get("question_number") or index
            )
        except (TypeError, ValueError):
            raise AIClientError(
                f"Invalid question number at question {index}."
            )

        if question_number < 1:
            raise AIClientError(
                f"Question {index} has an invalid question number."
            )

        validated_questions.append({
            "question_number": question_number,
            "question_type": question_type,
            "question_text": question_text,
            "choices": validated_choices,
            "correct_answer": correct_answer,
            "solution": solution,
            "explanation": explanation,
            "marks": marks,
        })

    question_numbers = [
        question["question_number"]
        for question in validated_questions
    ]

    if len(question_numbers) != len(set(question_numbers)):
        raise AIClientError(
            "Generated questions contain duplicate question numbers."
        )

    return validated_questions


# =========================================================
# RESOURCE RESPONSE VALIDATION
# =========================================================

def _validate_exam_resource(
    payload: dict[str, Any],
    *,
    resource_type: str, ) -> dict[str, Any]:

    if not isinstance(payload, dict):
        raise AIClientError(
            "AI returned an invalid resource response."
        )

    title = _resource_text(
        payload.get("title"),
        "title",
        max_length=200,
    )

    description = _resource_text(
        payload.get("description"),
        "description",
        max_length=500,
    )

    content = _resource_text(
        payload.get("content"),
        "content",
        required=False,
    )

    structured_content = payload.get(
        "structured_content",
        {},
    )

    if not isinstance(structured_content, dict):
        raise AIClientError(
            "Invalid structured resource content."
        )

    questions = []

    if resource_type in {
        "past_questions",
        "solutions",
        "mock_exam",
    }:
        questions = _validate_resource_questions(
            payload.get("questions"),
        )

    # -----------------------------------------------------
    # Validate structured resource types
    # -----------------------------------------------------

    structured_fields = {
        "lesson": [
            "objectives",
            "definitions",
            "content",
            "examples",
            "key_points",
            "activity",
        ],
        "practical": [
            "objectives",
            "materials",
            "procedures",
            "activities",
            "expected_results",
            "safety_notes",
        ],
        "revision": [
            "topic",
            "summary",
            "key_points",
            "formulas",
            "revision_exercises",
        ],
        "mock_exam": [
            "instructions",
            "duration_minutes",
            "total_marks",
        ],
    }

    if resource_type in structured_fields:

        validated_structured_content = {}

        for field in structured_fields[resource_type]:

            value = structured_content.get(field)

            if resource_type == "mock_exam" and field in {
                "duration_minutes",
                "total_marks",
            }:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise AIClientError(
                        f"Invalid mock exam value: {field}."
                    )

                if value < 1:
                    raise AIClientError(
                        f"Mock exam {field} must be greater than zero."
                    )

            else:
                value = _resource_text(
                    value,
                    field,
                    required=(field not in {"formulas", "safety_notes"}),
                )

            validated_structured_content[field] = value

        structured_content = validated_structured_content

    # -----------------------------------------------------
    # Mock exam marks validation
    # -----------------------------------------------------

    if resource_type == "mock_exam":

        question_total = sum(
            question["marks"]
            for question in questions
        )

        if question_total != structured_content["total_marks"]:
            raise AIClientError(
                "Mock exam total marks do not match the sum "
                "of the generated question marks."
            )

    # -----------------------------------------------------
    # Past Questions provenance
    # -----------------------------------------------------

    if resource_type == "past_questions":
        description = (
            description
            + " AI-generated practice questions; "
            "not verified historical examination questions."
        )[:500]

    if resource_type == "mock_exam":
        description = (
            description
            + " AI-generated mock examination."
        )[:500]

    return {
        "title": title,
        "description": description,
        "content": content,
        "structured_content": structured_content,
        "questions": questions,
        "resource_type": resource_type,
        "generated_by_ai": True,
    }
