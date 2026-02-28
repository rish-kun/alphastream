"""Tests for ML modules — FinBERT, NER, Ticker Resolver."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FinBERT Analyzer
# ---------------------------------------------------------------------------


class TestFinBERTAnalyzer:
    """Tests for pipeline.ml.finbert.FinBERTAnalyzer."""

    @patch("pipeline.ml.finbert.settings")
    def test_analyze_returns_result_with_mocked_pipeline(self, mock_settings):
        """analyze() should return score/label/confidence when model is loaded."""
        mock_settings.FINBERT_MODEL = "ProsusAI/finbert"

        from pipeline.ml.finbert import FinBERTAnalyzer

        analyzer = FinBERTAnalyzer()

        # Simulate a loaded pipeline — bypass _load_model
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [
            [
                {"label": "positive", "score": 0.85},
                {"label": "negative", "score": 0.10},
                {"label": "neutral", "score": 0.05},
            ]
        ]
        analyzer._pipeline = mock_pipeline
        analyzer._available = True

        result = analyzer.analyze(
            "Reliance Industries reported strong quarterly profits."
        )

        assert result["label"] == "positive"
        assert result["score"] == 1.0  # positive maps to 1.0
        assert result["confidence"] == pytest.approx(0.85)

    @patch("pipeline.ml.finbert.settings")
    def test_analyze_returns_neutral_when_unavailable(self, mock_settings):
        """analyze() returns neutral defaults when the model is not available."""
        mock_settings.FINBERT_MODEL = "ProsusAI/finbert"

        from pipeline.ml.finbert import FinBERTAnalyzer

        analyzer = FinBERTAnalyzer()
        # Force unavailable state — skip _load_model by setting _pipeline to a
        # non-None sentinel so _load_model short-circuits, but _available=False.
        analyzer._pipeline = MagicMock()
        analyzer._available = False

        result = analyzer.analyze("anything")

        assert result["score"] == 0.0
        assert result["label"] == "neutral"
        assert result["confidence"] == 0.0

    @patch("pipeline.ml.finbert.settings")
    def test_analyze_batch_returns_list(self, mock_settings):
        """analyze_batch() should return a list of results."""
        mock_settings.FINBERT_MODEL = "ProsusAI/finbert"

        from pipeline.ml.finbert import FinBERTAnalyzer

        analyzer = FinBERTAnalyzer()

        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [
            [
                {"label": "negative", "score": 0.7},
                {"label": "positive", "score": 0.2},
                {"label": "neutral", "score": 0.1},
            ]
        ]
        analyzer._pipeline = mock_pipeline
        analyzer._available = True

        results = analyzer.analyze_batch(["text 1", "text 2", "text 3"])

        assert isinstance(results, list)
        assert len(results) == 3
        for r in results:
            assert "score" in r
            assert "label" in r
            assert "confidence" in r

    @patch("pipeline.ml.finbert.settings")
    def test_analyze_negative_sentiment(self, mock_settings):
        """analyze() should return negative score for bearish text."""
        mock_settings.FINBERT_MODEL = "ProsusAI/finbert"

        from pipeline.ml.finbert import FinBERTAnalyzer

        analyzer = FinBERTAnalyzer()
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [
            [
                {"label": "negative", "score": 0.9},
                {"label": "positive", "score": 0.05},
                {"label": "neutral", "score": 0.05},
            ]
        ]
        analyzer._pipeline = mock_pipeline
        analyzer._available = True

        result = analyzer.analyze("Market crashed 500 points")

        assert result["label"] == "negative"
        assert result["score"] == -1.0


# ---------------------------------------------------------------------------
# Entity Extractor (NER)
# ---------------------------------------------------------------------------


class TestEntityExtractor:
    """Tests for pipeline.ml.ner.EntityExtractor."""

    @patch("pipeline.ml.ner.settings")
    def test_extract_entities_returns_entities(self, mock_settings):
        """extract_entities() should return a list of entity dicts."""
        mock_settings.SPACY_MODEL = "en_core_web_sm"

        from pipeline.ml.ner import EntityExtractor

        extractor = EntityExtractor()

        # Build a mock spaCy doc with entities
        mock_ent = SimpleNamespace(
            text="Reliance Industries",
            label_="ORG",
            start_char=0,
            end_char=20,
        )
        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent]

        mock_nlp = MagicMock(return_value=mock_doc)
        extractor._nlp = mock_nlp
        extractor._available = True

        entities = extractor.extract_entities("Reliance Industries reported profits")

        assert len(entities) == 1
        assert entities[0]["text"] == "Reliance Industries"
        assert entities[0]["label"] == "ORG"

    @patch("pipeline.ml.ner.settings")
    def test_extract_entities_returns_empty_when_unavailable(self, mock_settings):
        """extract_entities() returns [] when spaCy model is not loaded."""
        mock_settings.SPACY_MODEL = "en_core_web_sm"

        from pipeline.ml.ner import EntityExtractor

        extractor = EntityExtractor()
        extractor._nlp = MagicMock()  # set to skip _load_model
        extractor._available = False

        entities = extractor.extract_entities("anything")
        assert entities == []

    @patch("pipeline.ml.ner.settings")
    def test_extract_organizations_filters_org_only(self, mock_settings):
        """extract_organizations() should only return ORG entities."""
        mock_settings.SPACY_MODEL = "en_core_web_sm"

        from pipeline.ml.ner import EntityExtractor

        extractor = EntityExtractor()

        ent_org = SimpleNamespace(text="TCS", label_="ORG", start_char=0, end_char=3)
        ent_person = SimpleNamespace(
            text="Mukesh Ambani", label_="PERSON", start_char=10, end_char=23
        )
        ent_gpe = SimpleNamespace(
            text="India", label_="GPE", start_char=30, end_char=35
        )
        mock_doc = MagicMock()
        mock_doc.ents = [ent_org, ent_person, ent_gpe]

        extractor._nlp = MagicMock(return_value=mock_doc)
        extractor._available = True

        orgs = extractor.extract_organizations("TCS and Mukesh Ambani in India")

        assert orgs == ["TCS"]


# ---------------------------------------------------------------------------
# Ticker Resolver
# ---------------------------------------------------------------------------


class TestTickerResolver:
    """Tests for pipeline.ml.ticker_resolver.TickerResolver."""

    def test_resolve_exact_match(self):
        """resolve() should match exact alias (case-insensitive)."""
        from pipeline.ml.ticker_resolver import TickerResolver

        resolver = TickerResolver()

        assert resolver.resolve("Reliance Industries") == "RELIANCE"
        assert resolver.resolve("reliance industries") == "RELIANCE"
        assert resolver.resolve("TCS") == "TCS"
        assert resolver.resolve("Infosys") == "INFY"

    def test_resolve_partial_match(self):
        """resolve() should handle partial/substring matches."""
        from pipeline.ml.ticker_resolver import TickerResolver

        resolver = TickerResolver()

        # "Reliance" is a known alias
        assert resolver.resolve("Reliance") == "RELIANCE"

    def test_resolve_unknown_entity(self):
        """resolve() should return None for unknown companies."""
        from pipeline.ml.ticker_resolver import TickerResolver

        resolver = TickerResolver()

        assert resolver.resolve("FooBar Corp") is None
        assert resolver.resolve("Completely Unknown Inc") is None

    def test_resolve_all_returns_list_of_dicts(self):
        """resolve_all() should return entity/ticker pairs."""
        from pipeline.ml.ticker_resolver import TickerResolver

        resolver = TickerResolver()

        results = resolver.resolve_all(
            ["Reliance Industries", "Unknown Co", "HDFC Bank"]
        )

        assert len(results) == 3
        assert results[0]["entity"] == "Reliance Industries"
        assert results[0]["ticker"] == "RELIANCE"
        assert results[1]["entity"] == "Unknown Co"
        assert results[1]["ticker"] is None
        assert results[2]["entity"] == "HDFC Bank"
        assert results[2]["ticker"] == "HDFCBANK"
