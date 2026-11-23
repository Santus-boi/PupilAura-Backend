import logging
from decimal import Decimal

from .models import AICallLog

logger = logging.getLogger("ai_services")


def record_ai_call(
    *,
    user,
    feature: str,
    provider: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_estimate: Decimal | None = None,
    success: bool,
    error_message: str = "",
    duration_ms: int = 0,
):
    try:
        AICallLog.objects.create(
            user=user,
            feature=feature,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate=cost_estimate,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
        )
    except Exception:
        logger.exception("Failed to record AI call audit log")