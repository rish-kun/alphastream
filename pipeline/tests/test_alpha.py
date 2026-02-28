"""Tests for alpha signal computation modules."""

from pipeline.alpha.composite_signal import compute_composite
from pipeline.alpha.expectation_gap import compute_expectation_gap
from pipeline.alpha.narrative_velocity import compute_narrative_velocity
from pipeline.alpha.divergence import compute_divergence


class TestExpectationGap:
    def test_positive_gap(self):
        gap = compute_expectation_gap(0.8, 0.3)
        assert gap > 0

    def test_negative_gap(self):
        gap = compute_expectation_gap(-0.5, 0.2)
        assert gap < 0

    def test_zero_gap(self):
        gap = compute_expectation_gap(0.5, 0.5)
        assert gap == 0.0


class TestNarrativeVelocity:
    def test_high_share_high_sentiment(self):
        nv = compute_narrative_velocity(0.8, 0.9)
        assert nv > 0

    def test_zero_share(self):
        nv = compute_narrative_velocity(0.0, 0.9)
        assert nv == 0.0

    def test_formula_correctness(self):
        # news_share * 5 * (1 + abs(sentiment))
        nv = compute_narrative_velocity(0.5, 0.5)
        expected = 0.5 * 5 * (1 + 0.5)
        assert abs(nv - expected) < 1e-6


class TestDivergence:
    def test_bullish_sentiment_falling_price(self):
        div = compute_divergence(0.8, -0.05)
        assert div > 0  # Positive divergence

    def test_bearish_sentiment_rising_price(self):
        div = compute_divergence(-0.8, 0.05)
        assert div < 0  # Negative divergence

    def test_aligned_signals(self):
        div = compute_divergence(0.5, 0.5)
        assert abs(div) < 1e-6


class TestCompositeSignal:
    def test_strong_buy_signal(self):
        result = compute_composite(0.8, 0.7, 0.6)
        assert result["signal"] == "strong_buy"
        assert result["composite_score"] > 0.5

    def test_strong_sell_signal(self):
        result = compute_composite(-0.8, -0.7, -0.6)
        assert result["signal"] == "strong_sell"
        assert result["composite_score"] < -0.5

    def test_hold_signal(self):
        result = compute_composite(0.1, -0.1, 0.05)
        assert result["signal"] == "hold"

    def test_conviction_ranges(self):
        result = compute_composite(0.8, 0.7, 0.6)
        assert 0.0 <= result["conviction"] <= 1.0

    def test_weights_sum_to_one(self):
        # Verify weights: 0.45 + 0.30 + 0.25 = 1.0
        result = compute_composite(1.0, 1.0, 1.0)
        assert abs(result["composite_score"] - 1.0) < 1e-6

    def test_all_zero_is_hold(self):
        result = compute_composite(0.0, 0.0, 0.0)
        assert result["signal"] == "hold"
        assert result["composite_score"] == 0.0
        assert result["conviction"] == 0.0

    def test_buy_threshold(self):
        # Composite > 0.2 but <= 0.5 should be "buy"
        result = compute_composite(0.4, 0.3, 0.2)
        assert result["signal"] == "buy"

    def test_sell_threshold(self):
        # Composite < -0.2 but >= -0.5 should be "sell"
        result = compute_composite(-0.4, -0.3, -0.2)
        assert result["signal"] == "sell"
