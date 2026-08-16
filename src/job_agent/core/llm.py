import os
import logging
import re
import time
from typing import Any, Type, TypeVar
from google import genai
from pydantic import BaseModel
from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMService:
    """
    Wrapper for Google GenAI API (Gemini).
    Provides structured JSON output capabilities.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will fail if called.")
            
        # We assume the user has the google-genai library installed
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        # Keep requests conservative and sequential: ~10 requests/minute.
        self.min_interval_seconds = 6.0
        self.max_retries = 3
        self._last_request_ts = 0.0

        # Run metrics counters consumed by the orchestrator logs.
        self.success_count = 0
        self.failure_count = 0
        self.retry_429_count = 0

    def _is_quota_error(self, err: Exception) -> bool:
        message = str(err).lower()
        status_code = getattr(err, "status_code", None)
        code = getattr(err, "code", None)
        return (
            status_code == 429
            or code == 429
            or "resource_exhausted" in message
            or "429" in message
            or "quota" in message
        )

    def _extract_retry_delay_seconds(self, err: Exception) -> float:
        # Example payload fragments:
        # retryDelay: "8s"
        # retryDelay":"1.5s"
        # retryDelay: 12
        message = str(err)
        match = re.search(r"retryDelay\s*[:=]\s*\"?([0-9]+(?:\.[0-9]+)?)\s*([sm]?)\"?", message)
        if not match:
            return 0.0
        value = float(match.group(1))
        unit = match.group(2) or "s"
        if unit == "m":
            return value * 60.0
        return value

    def _wait_for_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        
    def generate_structured_response(self, prompt: str, schema: Type[T]) -> T:
        """
        Sends a prompt to Gemini and enforces a structured JSON response matching the schema.
        """
        backoff_seconds = 2.0
        for attempt in range(self.max_retries + 1):
            self._wait_for_rate_limit()
            self._last_request_ts = time.monotonic()
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1 # Low temperature for analytical consistency
                    ),
                )

                self.success_count += 1
                # The google-genai SDK when using response_schema returns a JSON string in response.text
                # Or if it supports structured outputs directly, we parse it.
                # We will use Pydantic to validate and parse the JSON string.
                return schema.model_validate_json(response.text)

            except Exception as e:
                if self._is_quota_error(e) and attempt < self.max_retries:
                    retry_delay = self._extract_retry_delay_seconds(e)
                    sleep_for = retry_delay if retry_delay > 0 else backoff_seconds
                    self.retry_429_count += 1
                    logger.warning(
                        f"Gemini quota hit (attempt {attempt + 1}/{self.max_retries + 1}). "
                        f"Retrying in {sleep_for:.1f}s."
                    )
                    time.sleep(sleep_for)
                    backoff_seconds *= 2.0
                    continue

                self.failure_count += 1
                logger.error(f"Error generating structured response from LLM: {e}")
                raise
