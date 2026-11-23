
"""
Thin wrapper around the LLM provider.

Swap the underlying provider (OpenAI, Anthropic, Google, local Ollama, etc.)
without touching the generator modules — they only talk to AIClient.
"""

import json
import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("ai_services")


class AIClientError(Exception):
    """Base class for AI provider errors."""


class AITimeoutError(AIClientError):
    """The provider took too long to respond."""


class AIConnectionError(AIClientError):
    """A network or SSL connection to the provider failed."""


class AIInvalidResponseError(AIClientError):
    """The provider returned a response that couldn't be parsed as valid JSON."""


class AIClient:
    """
    Wraps a single LLM call.

    Configure in settings:

        AI_PROVIDER = "openai"
        AI_API_KEY = "..."
        AI_MODEL = "gpt-4o-mini"
        AI_TIMEOUT_SECONDS = 45
        AI_MAX_RETRIES = 2
    """

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        self.provider = provider or getattr(settings, "AI_PROVIDER", "openai")
        self.api_key = api_key or getattr(settings, "AI_API_KEY", "")
        self.model = model or getattr(settings, "AI_MODEL", "gpt-4o-mini")
        self.timeout = timeout or getattr(settings, "AI_TIMEOUT_SECONDS", 45)

        if not self.api_key and self.provider != "ollama":
            raise AIClientError(
                "AI_API_KEY is not configured. Set AI_API_KEY in settings."
            )

    # ---- public API ---------------------------------------------

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        max_retries: int | None = None,
    ) -> dict[str, Any]:

        retries = (
            max_retries
            if max_retries is not None
            else getattr(settings, "AI_MAX_RETRIES", 2)
        )
        retries = max(1, int(retries))

        last_error = None

        for attempt in range(1, retries + 1):
            try:
                raw = self._call_provider(
                    system_prompt,
                    user_prompt,
                    schema,
                )
                return self._parse_json(raw)

            except (
                AITimeoutError,
                AIConnectionError,
                AIInvalidResponseError,
            ) as exc:

                last_error = exc

                logger.warning(
                    "AI call failed (attempt %s/%s): %s",
                    attempt,
                    retries,
                    exc,
                )

                if attempt < retries:
                    time.sleep(1.5 * attempt)

        raise last_error or AIClientError(
            "AI call failed after retries."
        )

    def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Free-form text completion."""
        return self._call_provider(system_prompt, user_prompt, None)

    # ---- provider abstraction -----------------------------------

    def _call_provider(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any] | None,
    ) -> str:

        if self.provider == "openai":
            return self._call_openai(
                system_prompt,
                user_prompt,
                schema,
            )

        if self.provider == "anthropic":
            return self._call_anthropic(
                system_prompt,
                user_prompt,
                schema,
            )

        if self.provider == "ollama":
            return self._call_ollama(
                system_prompt,
                user_prompt,
                schema,
            )

        raise AIClientError(
            f"Unknown AI provider: {self.provider}"
        )

    # ---- OpenAI --------------------------------------------------

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any] | None,
    ) -> str:

        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.4,
        }

        if schema:
            payload["response_format"] = {
                "type": "json_object"
            }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=(10, self.timeout),
            )

        except requests.exceptions.Timeout as exc:
            raise AITimeoutError(
                f"OpenAI request timed out: {exc}"
            ) from exc

        except requests.exceptions.SSLError as exc:
            raise AIConnectionError(
                "OpenAI SSL/TLS connection failed. "
                "Check your internet connection, certificates, "
                "VPN, proxy or firewall."
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise AIConnectionError(
                f"Could not establish a connection to OpenAI: {exc}"
            ) from exc

        except requests.RequestException as exc:
            raise AIClientError(
                f"OpenAI request error: {exc}"
            ) from exc

        # Handle unsuccessful HTTP responses.
        if response.status_code != 200:

            error_message = response.text[:500]

            if response.status_code in (408, 429) or response.status_code >= 500:
                raise AIConnectionError(
                    f"OpenAI temporarily unavailable "
                    f"({response.status_code}): {error_message}"
                )

            raise AIClientError(
                f"OpenAI {response.status_code}: {error_message}"
            )

        # Parse the provider response.
        try:
            data = response.json()

            content = data["choices"][0]["message"]["content"]

            if not isinstance(content, str) or not content.strip():
                raise ValueError("OpenAI returned empty content.")

            return content

        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIInvalidResponseError(
                f"Could not read OpenAI response: {exc}"
            ) from exc

    # Add _call_anthropic / _call_ollama analogously.

    # ---- JSON parsing -------------------------------------------

    def _parse_json(self, raw: str) -> dict[str, Any]:

        raw = (raw or "").strip()

        if raw.startswith("```"):
            raw = raw.strip("`").strip()

            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        try:
            result = json.loads(raw)

        except json.JSONDecodeError as exc:
            raise AIInvalidResponseError(
                f"AI returned invalid JSON: {exc}. "
                f"Raw: {raw[:300]}"
            ) from exc

        if not isinstance(result, dict):
            raise AIInvalidResponseError(
                "AI response must be a JSON object."
            )

        return result
