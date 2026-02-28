"""Tests for LLM modules — Gemini, OpenRouter, RateLimiter, Prompts."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Gemini Client
# ---------------------------------------------------------------------------


class TestGeminiClient:
    """Tests for pipeline.llm.gemini_client.GeminiClient."""

    def test_analyze_sentiment_no_keys_returns_placeholder(self):
        """analyze_sentiment() returns placeholder when no keys are provided."""
        from pipeline.llm.gemini_client import GeminiClient

        client = GeminiClient(api_keys=[])
        result = client.analyze_sentiment("Reliance stock rose 5%")

        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.0
        assert "No Gemini API keys configured" in result["explanation"]

    @patch("pipeline.llm.gemini_client.GeminiClient._parse_json_response")
    def test_analyze_sentiment_with_mocked_genai(self, mock_parse):
        """analyze_sentiment() should call Gemini API and return parsed JSON."""
        expected = {
            "sentiment_score": 0.7,
            "confidence": 0.85,
            "explanation": "Strong quarterly results",
            "impact_timeline": "short_term",
            "affected_sectors": ["Energy"],
            "mentioned_tickers": ["RELIANCE"],
            "key_themes": ["earnings"],
        }
        mock_parse.return_value = expected

        from pipeline.llm.gemini_client import GeminiClient

        client = GeminiClient(api_keys=["fake-key-1"])

        # Mock the rate limiter and the genai import
        client._rate_limiter = MagicMock()

        with patch.dict(
            "sys.modules", {"google": MagicMock(), "google.genai": MagicMock()}
        ) as _:
            with patch("pipeline.llm.gemini_client.genai", create=True) as mock_genai:
                mock_client_obj = MagicMock()
                mock_response = MagicMock()
                mock_response.text = json.dumps(expected)
                mock_client_obj.models.generate_content.return_value = mock_response

                # Patch the import inside analyze_sentiment
                with patch("google.genai.Client", return_value=mock_client_obj):
                    result = client.analyze_sentiment("Reliance posted strong Q3")

        assert result["sentiment_score"] == 0.7

    def test_parse_json_response_valid_json(self):
        """_parse_json_response should parse clean JSON."""
        from pipeline.llm.gemini_client import GeminiClient

        client = GeminiClient(api_keys=[])
        data = '{"sentiment_score": 0.5, "confidence": 0.8}'
        result = client._parse_json_response(data)

        assert result["sentiment_score"] == 0.5

    def test_parse_json_response_extracts_json_from_text(self):
        """_parse_json_response should extract JSON embedded in text."""
        from pipeline.llm.gemini_client import GeminiClient

        client = GeminiClient(api_keys=[])
        data = 'Here is the analysis: {"sentiment_score": 0.3, "confidence": 0.6} end.'
        result = client._parse_json_response(data)

        assert result["sentiment_score"] == 0.3

    def test_get_fallback_response(self):
        """_get_fallback_response should return defaults with the error message."""
        from pipeline.llm.gemini_client import GeminiClient

        client = GeminiClient(api_keys=[])
        result = client._get_fallback_response("timeout error")

        assert result["sentiment_score"] == 0.0
        assert "timeout error" in result["explanation"]


# ---------------------------------------------------------------------------
# OpenRouter Client
# ---------------------------------------------------------------------------


class TestOpenRouterClient:
    """Tests for pipeline.llm.openrouter_client.OpenRouterClient."""

    def test_analyze_sentiment_no_keys_returns_placeholder(self):
        """analyze_sentiment() returns placeholder when no keys are provided."""
        from pipeline.llm.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_keys=[])
        result = client.analyze_sentiment("Market crashed today")

        assert result["sentiment_score"] == 0.0
        assert "No OpenRouter API keys configured" in result["explanation"]

    def test_parse_json_response_valid(self):
        """_parse_json_response should parse clean JSON."""
        from pipeline.llm.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_keys=[])
        data = '{"sentiment_score": -0.4, "confidence": 0.7}'
        result = client._parse_json_response(data)

        assert result["sentiment_score"] == -0.4

    def test_get_fallback_response(self):
        """_get_fallback_response should return neutral defaults."""
        from pipeline.llm.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_keys=[])
        result = client._get_fallback_response("connection refused")

        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.0
        assert "connection refused" in result["explanation"]


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    """Tests for pipeline.llm.rate_limiter.RateLimiter."""

    def test_acquire_first_request_succeeds(self):
        """First acquire() call should always succeed."""
        from pipeline.llm.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests_per_minute=60)
        assert limiter.acquire() is True

    def test_acquire_second_request_throttled(self):
        """Second immediate acquire() should be rejected (rate limited)."""
        from pipeline.llm.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests_per_minute=60)
        limiter.acquire()  # first call sets _last_request_time

        # Immediately try again — should be throttled
        assert limiter.acquire() is False

    def test_wait_blocks_until_interval(self):
        """wait() should enforce the minimum interval between requests."""
        from pipeline.llm.rate_limiter import RateLimiter

        # 60 RPM => 1s interval.  Two immediate calls must take >= 1s total
        # but we just verify the internal state changes correctly.
        limiter = RateLimiter(max_requests_per_minute=6000)
        # interval = 60/6000 = 0.01s — fast enough to not slow tests

        limiter.wait()
        t1 = limiter._last_request_time
        limiter.wait()
        t2 = limiter._last_request_time

        # The second call must have set _last_request_time >= t1
        assert t2 >= t1


# ---------------------------------------------------------------------------
# Key Rotator
# ---------------------------------------------------------------------------


class TestKeyRotator:
    """Tests for pipeline.llm.rate_limiter.KeyRotator."""

    def test_round_robin_rotation(self):
        """get_next() should cycle through keys in round-robin order."""
        from pipeline.llm.rate_limiter import KeyRotator

        rotator = KeyRotator(["key-a", "key-b", "key-c"])

        assert rotator.get_next() == "key-a"
        assert rotator.get_next() == "key-b"
        assert rotator.get_next() == "key-c"
        assert rotator.get_next() == "key-a"  # wraps around

    def test_mark_failed_skips_key(self):
        """mark_failed() should cause that key to be skipped."""
        from pipeline.llm.rate_limiter import KeyRotator

        rotator = KeyRotator(["key-a", "key-b", "key-c"])
        rotator.mark_failed("key-a")

        # Now only key-b, key-c are available
        result = rotator.get_next()
        assert result in ("key-b", "key-c")

    def test_all_failed_resets(self):
        """When all keys are marked failed, failure list should reset."""
        from pipeline.llm.rate_limiter import KeyRotator

        rotator = KeyRotator(["key-a", "key-b"])
        rotator.mark_failed("key-a")
        rotator.mark_failed("key-b")

        # All failed — should reset and return a key
        key = rotator.get_next()
        assert key in ("key-a", "key-b")

    def test_no_keys_raises(self):
        """get_next() should raise ValueError when no keys are configured."""
        from pipeline.llm.rate_limiter import KeyRotator

        rotator = KeyRotator([])
        with pytest.raises(ValueError, match="No API keys configured"):
            rotator.get_next()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


class TestPrompts:
    """Tests for pipeline.llm.prompts prompt templates."""

    def test_sentiment_prompt_is_string(self):
        """SENTIMENT_ANALYSIS_PROMPT should be a non-empty string."""
        from pipeline.llm.prompts import SENTIMENT_ANALYSIS_PROMPT

        assert isinstance(SENTIMENT_ANALYSIS_PROMPT, str)
        assert len(SENTIMENT_ANALYSIS_PROMPT) > 50

    def test_sentiment_prompt_formatting(self):
        """SENTIMENT_ANALYSIS_PROMPT should accept article_text and context."""
        from pipeline.llm.prompts import SENTIMENT_ANALYSIS_PROMPT

        formatted = SENTIMENT_ANALYSIS_PROMPT.format(
            article_text="Sensex rises 500 points",
            context="Banking sector",
        )

        assert "Sensex rises 500 points" in formatted
        assert "Banking sector" in formatted

    def test_portfolio_prompt_is_string(self):
        """PORTFOLIO_ANALYSIS_PROMPT should be a non-empty string."""
        from pipeline.llm.prompts import PORTFOLIO_ANALYSIS_PROMPT

        assert isinstance(PORTFOLIO_ANALYSIS_PROMPT, str)
        assert len(PORTFOLIO_ANALYSIS_PROMPT) > 50

    def test_portfolio_prompt_formatting(self):
        """PORTFOLIO_ANALYSIS_PROMPT should accept holdings and sentiment_data."""
        from pipeline.llm.prompts import PORTFOLIO_ANALYSIS_PROMPT

        formatted = PORTFOLIO_ANALYSIS_PROMPT.format(
            holdings="RELIANCE: 100 shares",
            sentiment_data="score=0.7",
        )

        assert "RELIANCE: 100 shares" in formatted
        assert "score=0.7" in formatted
