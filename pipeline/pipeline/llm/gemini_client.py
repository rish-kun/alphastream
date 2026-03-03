"""Google Gemini API client for financial sentiment analysis."""

import json
import logging
import re

from pipeline.config import settings
from pipeline.llm.rate_limiter import KeyRotator, RateLimiter

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API with key rotation and rate limiting.

    Uses multiple API keys with rotation to maximize throughput
    while respecting rate limits.
    """

    def __init__(
        self,
        api_keys: list[str],
        model_name: str | None = None,
        max_input_chars: int | None = None,
    ) -> None:
        """Initialize the Gemini client.

        Args:
            api_keys: List of Gemini API keys for rotation.
        """
        self._key_rotator = KeyRotator(api_keys)
        self._rate_limiter = RateLimiter(
            max_requests_per_minute=settings.LLM_REQUESTS_PER_MINUTE
        )
        self._api_keys = api_keys
        self._model_name = model_name or settings.SENTIMENT_GEMINI_MODEL
        self._max_input_chars = max_input_chars or settings.SENTIMENT_LLM_MAX_CHARS
        logger.info("GeminiClient initialized with %d API keys", len(api_keys))

    def _rotate_key(self) -> str:
        """Get the next available API key.

        Returns:
            An API key string from the rotation pool.
        """
        return self._key_rotator.get_next()

    def analyze_sentiment(
        self,
        text: str,
        context: str = "",
        fail_silently: bool = True,
    ) -> dict:
        """Analyze financial sentiment using Gemini.

        Args:
            text: Article or post text to analyze.
            context: Additional context (e.g., sector, related news).

        Returns:
            Dict with sentiment_score, confidence, explanation, and metadata.
        """
        logger.info(
            "Analyzing sentiment via Gemini (text length=%d)", len(text))

        if len(self._api_keys) == 0:
            if not fail_silently:
                raise ValueError("No Gemini API keys configured")
            logger.warning(
                "No Gemini API keys configured, returning placeholder")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "explanation": "No Gemini API keys configured",
                "impact_timeline": "unknown",
                "affected_sectors": [],
                "mentioned_tickers": [],
                "key_themes": [],
            }

        self._rate_limiter.wait()
        api_key = self._rotate_key()

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            from pipeline.llm.prompts import SENTIMENT_ANALYSIS_PROMPT

            prompt = SENTIMENT_ANALYSIS_PROMPT.format(
                article_text=text[: self._max_input_chars], context=context
            )
            response = client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )

            result = self._normalize_response(
                self._parse_json_response(response.text))
            logger.info("Gemini sentiment analysis completed successfully")
            return result
        except Exception as e:
            self._key_rotator.mark_failed(api_key)
            logger.error("Gemini API call failed: %s", str(e))
            if not fail_silently:
                raise
            return self._get_fallback_response(str(e))

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from the Gemini response.

        Args:
            response_text: Raw response text from Gemini.

        Returns:
            Parsed JSON dict.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise

    def _get_fallback_response(self, error: str) -> dict:
        """Return a fallback response on error.

        Args:
            error: Error message for logging.

        Returns:
            Fallback dict with default values.
        """
        logger.warning(
            "Returning fallback sentiment response due to: %s", error)
        return {
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "explanation": f"Analysis failed: {error[:100]}",
            "impact_timeline": "unknown",
            "affected_sectors": [],
            "mentioned_tickers": [],
            "key_themes": [],
        }

    def _normalize_response(self, result: dict) -> dict:
        score = self._clamp(self._to_float(
            result.get("sentiment_score")), -1.0, 1.0)
        confidence = self._clamp(
            self._to_float(result.get("confidence")),
            0.0,
            1.0,
        )
        timeline = str(result.get("impact_timeline")
                       or "unknown").strip().lower()
        if timeline not in {"immediate", "short_term", "long_term"}:
            timeline = "unknown"
        return {
            "sentiment_score": score,
            "confidence": confidence,
            "explanation": str(result.get("explanation") or "").strip()
            or "No explanation provided",
            "impact_timeline": timeline,
            "affected_sectors": self._normalize_list(result.get("affected_sectors")),
            "mentioned_tickers": self._normalize_list(result.get("mentioned_tickers")),
            "key_themes": self._normalize_list(result.get("key_themes")),
        }

    def _normalize_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _to_float(self, value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _clamp(self, value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))
