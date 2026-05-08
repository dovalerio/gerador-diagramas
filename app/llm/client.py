"""
OpenRouter LLM client with retry and timeout.
Compatible with openai>=1.55.0 (OpenAI SDK v1 client interface).
"""
from __future__ import annotations
import time
import logging
from typing import Optional

from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0   # seconds per request
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0        # seconds between retries (doubles each attempt)


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "meta-llama/llama-3.3-70b-instruct:free",
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.max_retries = max_retries

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request, retrying on transient errors."""
        delay = _RETRY_DELAY
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""

            except RateLimitError as exc:
                logger.warning("Rate limit on attempt %d/%d: %s", attempt, self.max_retries, exc)
                last_exc = exc

            except APIConnectionError as exc:
                logger.warning("Connection error on attempt %d/%d: %s", attempt, self.max_retries, exc)
                last_exc = exc

            except APIStatusError as exc:
                # 5xx are transient; 4xx (except 429) are permanent — don't retry
                if exc.status_code and exc.status_code < 500:
                    raise
                logger.warning("API %d error on attempt %d/%d: %s",
                               exc.status_code, attempt, self.max_retries, exc)
                last_exc = exc

            if attempt < self.max_retries:
                time.sleep(delay)
                delay *= 2

        raise RuntimeError(
            f"LLM request failed after {self.max_retries} attempts"
        ) from last_exc
