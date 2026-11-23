# ai_services/__init__.py
# Do NOT import models at module load time — Django apps.populate() would fail.

_LAZY_IMPORTS = {
    "AIClient": ("ai_services.client", "AIClient"),
    "AIClientError": ("ai_services.client", "AIClientError"),
    "AITimeoutError": ("ai_services.client", "AITimeoutError"),
    "AIInvalidResponseError": ("ai_services.client", "AIInvalidResponseError"),
    "record_ai_call": ("ai_services.logging", "record_ai_call"),
    "generate_lesson_content": ("ai_services.lesson_generator", "generate_lesson_content"),
    "generate_quiz_questions": ("ai_services.quiz_generator", "generate_quiz_questions"),
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        import importlib
        module_path, attr = _LAZY_IMPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module 'ai_services' has no attribute {name!r}")