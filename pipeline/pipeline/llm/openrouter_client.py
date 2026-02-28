"""OpenRouter API client for financial sentiment analysis."""

import json
import logging
import re

from pipeline.llm.rate_limiter import KeyRotator, RateLimiter

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API with key rotation and rate limiting.

    Uses OpenRouter to access various LLM models with a unified API,
    with multiple API keys for rotation.
    """

    def __init__(self, api_keys: list[str]) -> None:
        """Initialize the OpenRouter client.

        Args:
            api_keys: List of OpenRouter API keys for rotation.
        """
        self._key_rotator = KeyRotator(api_keys)
        self._rate_limiter = RateLimiter(max_requests_per_minute=15)
        self._api_keys = api_keys
        logger.info("OpenRouterClient initialized with %d API keys", len(api_keys))

    def _rotate_key(self) -> str:
        """Get the next available API key.

        Returns:
            An API key string from the rotation pool.
        """
        return self._key_rotator.get_next()

    def analyze_sentiment(self, text: str, context: str = "") -> dict:
        """Analyze financial sentiment using OpenRouter.

        Args:
            text: Article or post text to analyze.
            context: Additional context (e.g., sector, related news).

        Returns:
            Dict with sentiment_score, confidence, explanation, and metadata.
        """
        logger.info("Analyzing sentiment via OpenRouter (text length=%d)", len(text))

        if len(self._api_keys) == 0:
            logger.warning("No OpenRouter API keys configured, returning placeholder")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "explanation": "No OpenRouter API keys configured",
                "impact_timeline": "unknown",
                "affected_sectors": [],
                "mentioned_tickers": [],
                "key_themes": [],
            }

        self._rate_limiter.wait()
        api_key = self._rotate_key()

        try:
            from openai import OpenAI

            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            from pipeline.llm.prompts import SENTIMENT_ANALYSIS_PROMPT

            prompt = SENTIMENT_ANALYSIS_PROMPT.format(
                article_text=text[:3000], context=context
            )
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[{"role": "user", "content": prompt}],
            )

            result = self._parse_json_response(response.choices[0].message.content)
            logger.info("OpenRouter sentiment analysis completed successfully")
            return result
        except Exception as e:
            logger.error("OpenRouter API call failed: %s", str(e))
            return self._get_fallback_response(str(e))

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from the OpenRouter response.

        Args:
            response_text: Raw response text from OpenRouter.

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
        logger.warning("Returning fallback sentiment response due to: %s", error)
        return {
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "explanation": f"Analysis failed: {error[:100]}",
            "impact_timeline": "unknown",
            "affected_sectors": [],
            "mentioned_tickers": [],
            "key_themes": [],
        }
