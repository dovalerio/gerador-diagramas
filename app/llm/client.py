"""
OpenRouter LLM client with model fallback, retry and timeout.
Compatible with openai>=1.55.0 (OpenAI SDK v1 client interface).
"""
from __future__ import annotations
import time
import logging
from typing import Optional

from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError, NotFoundError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 2          # retries per model before moving to next
_RETRY_DELAY = 2.0        # seconds between retries (doubles each attempt)

# errors that mean "this model is unavailable, try the next one"
_FALLBACK_ERRORS = (RateLimitError, NotFoundError)


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "nvidia/nemotron-3-super-120b-a12b:free",
        fallback_models: list[str] | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.fallback_models = fallback_models or []
        self.max_retries = max_retries

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion, trying fallback models on rate limit or not-found."""
        candidates = [self.model] + self.fallback_models
        last_exc: Optional[Exception] = None

        for model in candidates:
            logger.info("Trying model: %s", model)
            result = self._try_model(model, system_prompt, user_prompt, temperature, max_tokens)
            if isinstance(result, str):
                return result
            last_exc = result  # an exception instance — try next model

        raise RuntimeError(
            f"All models exhausted after fallback attempts"
        ) from last_exc

    def _try_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str | Exception:
        """Try one model with retries. Returns content string on success, exception on failure."""
        delay = _RETRY_DELAY
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""

            except _FALLBACK_ERRORS as exc:
                logger.warning("Model %s unavailable (%s) — will try next", model, type(exc).__name__)
                return exc  # signal caller to move to next model

            except APIStatusError as exc:
                if exc.status_code == 402:
                    logger.warning("Model %s spend limit (402) — will try next", model)
                    return exc
                if exc.status_code and exc.status_code >= 500:
                    logger.warning("API %d on attempt %d/%d for %s", exc.status_code, attempt, self.max_retries, model)
                    last_exc = exc
                else:
                    raise  # 4xx other than 429/402/404 are permanent

            except APIConnectionError as exc:
                logger.warning("Connection error attempt %d/%d for %s: %s", attempt, self.max_retries, model, exc)
                last_exc = exc

            if attempt < self.max_retries:
                time.sleep(delay)
                delay *= 2

        return last_exc
