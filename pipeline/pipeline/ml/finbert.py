"""FinBERT sentiment analysis for financial text."""

import logging

from pipeline.config import settings

logger = logging.getLogger(__name__)


class FinBERTAnalyzer:
    """Financial sentiment analysis using the FinBERT model.

    Uses ProsusAI/finbert for domain-specific financial sentiment
    classification (positive, negative, neutral).
    """

    def __init__(self) -> None:
        """Initialize FinBERT analyzer with lazy model loading."""
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._available = False

    def _load_model(self) -> None:
        """Lazily load the FinBERT model and tokenizer."""
        if self._pipeline is not None:
            return
        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
                pipeline as hf_pipeline,
            )

            logger.info("Loading FinBERT model: %s", settings.FINBERT_MODEL)
            self._tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                settings.FINBERT_MODEL
            )
            self._pipeline = hf_pipeline(
                "sentiment-analysis",
                model=self._model,
                tokenizer=self._tokenizer,
                return_all_scores=True,
            )
            self._available = True
            logger.info("FinBERT model loaded successfully")
        except ImportError:
            logger.warning("transformers not installed, FinBERT unavailable")
            self._available = False

    def analyze(self, text: str) -> dict:
        """Analyze sentiment of a single text.

        Args:
            text: Financial text to analyze.

        Returns:
            Dict with keys: score (-1.0 to 1.0), label, confidence.
        """
        self._load_model()
        if not self._available:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}
        logger.info("Analyzing sentiment for text (length=%d)", len(text))
        results = self._pipeline(text[:512])[0]
        best = max(results, key=lambda x: x["score"])
        label_map = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}
        return {
            "score": label_map.get(best["label"], 0.0),
            "label": best["label"],
            "confidence": best["score"],
        }

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Analyze sentiment for a batch of texts.

        Args:
            texts: List of financial texts to analyze.

        Returns:
            List of sentiment result dicts.
        """
        self._load_model()
        logger.info("Batch analyzing %d texts", len(texts))
        return [self.analyze(text) for text in texts]
