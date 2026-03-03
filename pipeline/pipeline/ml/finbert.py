"""FinBERT sentiment analysis for financial text."""

import logging
import threading
from collections.abc import Sequence

from pipeline.config import settings

logger = logging.getLogger(__name__)


class FinBERTAnalyzer:
    """Financial sentiment analysis using the FinBERT model.

    Uses ProsusAI/finbert for domain-specific financial sentiment
    classification (positive, negative, neutral).
    """

    _shared_pipeline = None
    _shared_available = False
    _shared_model_name: str | None = None
    _load_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize FinBERT analyzer with lazy model loading."""
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._available = False

    def _load_model(self) -> None:
        """Lazily load the FinBERT model and tokenizer."""
        configured_model = self._get_model_name()
        if (
            self.__class__._shared_pipeline is not None
            and self.__class__._shared_model_name == configured_model
        ):
            self._pipeline = self.__class__._shared_pipeline
            self._available = self.__class__._shared_available
            return

        if self._pipeline is not None:
            return

        with self.__class__._load_lock:
            if (
                self.__class__._shared_pipeline is not None
                and self.__class__._shared_model_name == configured_model
            ):
                self._pipeline = self.__class__._shared_pipeline
                self._available = self.__class__._shared_available
                return
            try:
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                    pipeline as hf_pipeline,
                )

                logger.info("Loading FinBERT model: %s", configured_model)
                self._tokenizer = AutoTokenizer.from_pretrained(configured_model)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    configured_model
                )
                self._pipeline = hf_pipeline(
                    "sentiment-analysis",
                    model=self._model,
                    tokenizer=self._tokenizer,
                    return_all_scores=True,
                )
                self._available = True
                self.__class__._shared_pipeline = self._pipeline
                self.__class__._shared_available = True
                self.__class__._shared_model_name = configured_model
                logger.info("FinBERT model loaded successfully")
            except ImportError:
                logger.warning("transformers not installed, FinBERT unavailable")
                self._available = False
            except Exception:
                logger.exception("Failed to load FinBERT model: %s", configured_model)
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

        segments = self._segment_text(text)
        if not segments:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}

        logger.debug(
            "Analyzing sentiment for %d segment(s), total_length=%d",
            len(segments),
            len(text),
        )
        all_results = self._run_pipeline(segments)
        probabilities = self._aggregate_probabilities(all_results, segments)
        positive = probabilities.get("positive", 0.0)
        negative = probabilities.get("negative", 0.0)
        neutral = probabilities.get("neutral", 0.0)
        score = max(-1.0, min(1.0, positive - negative))
        label = max(probabilities, key=probabilities.get)
        confidence = max(positive, negative, neutral)

        return {
            "score": score,
            "label": label,
            "confidence": confidence,
            "probabilities": probabilities,
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

    def _segment_text(self, text: str) -> list[str]:
        normalized = " ".join((text or "").split())
        if not normalized:
            return []

        max_chars = max(400, self._get_int_setting("SENTIMENT_FINBERT_MAX_CHARS", 3000))
        max_chunks = max(1, self._get_int_setting("SENTIMENT_FINBERT_MAX_CHUNKS", 3))

        if len(normalized) <= max_chars:
            return [normalized]

        head_size = max_chars // 2
        tail_size = max_chars // 2
        segments = [normalized[:head_size], normalized[-tail_size:]]

        if max_chunks > 2 and len(normalized) > max_chars * 2:
            mid_start = max(0, (len(normalized) // 2) - (max_chars // 4))
            mid_end = min(len(normalized), mid_start + (max_chars // 2))
            segments.insert(1, normalized[mid_start:mid_end])

        return segments[:max_chunks]

    def _run_pipeline(self, segments: list[str]) -> list[Sequence[dict]]:
        raw = self._pipeline(segments if len(segments) > 1 else segments[0])
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            return [raw]
        return raw

    def _aggregate_probabilities(
        self, all_results: list[Sequence[dict]], segments: list[str]
    ) -> dict[str, float]:
        if not all_results:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

        totals = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        total_weight = 0.0

        for idx, result in enumerate(all_results):
            weight = float(len(segments[idx])) if idx < len(segments) else 1.0
            total_weight += weight
            for entry in result:
                label = str(entry.get("label", "")).lower()
                if label in totals:
                    totals[label] += float(entry.get("score", 0.0)) * weight

        if total_weight <= 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

        averaged = {label: value / total_weight for label, value in totals.items()}
        total = sum(averaged.values())
        if total <= 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

        return {label: value / total for label, value in averaged.items()}

    def _get_model_name(self) -> str:
        preferred = getattr(settings, "SENTIMENT_FINBERT_MODEL", None)
        fallback = getattr(settings, "FINBERT_MODEL", "ProsusAI/finbert")
        if isinstance(preferred, str) and preferred.strip():
            return preferred.strip()
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()
        return "ProsusAI/finbert"

    def _get_int_setting(self, key: str, default: int) -> int:
        value = getattr(settings, key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
