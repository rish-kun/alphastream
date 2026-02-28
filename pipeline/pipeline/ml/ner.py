"""Named Entity Recognition for financial text."""

import logging

from pipeline.config import settings

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts named entities from financial text using spaCy.

    Focuses on organization entities (ORG) which can be resolved
    to stock tickers for Indian market analysis.
    """

    def __init__(self) -> None:
        """Initialize entity extractor with lazy spaCy model loading."""
        self._nlp = None
        self._available = False

    def _load_model(self) -> None:
        """Lazily load the spaCy NLP model."""
        if self._nlp is not None:
            return
        try:
            import spacy

            logger.info("Loading spaCy model: %s", settings.SPACY_MODEL)
            self._nlp = spacy.load(settings.SPACY_MODEL)
            self._available = True
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning(
                "spaCy model %s not downloaded, NER unavailable", settings.SPACY_MODEL
            )
            self._available = False
        except ImportError:
            logger.warning("spaCy not installed, NER unavailable")
            self._available = False

    def extract_entities(self, text: str) -> list[dict]:
        """Extract all named entities from text.

        Args:
            text: Text to process for named entities.

        Returns:
            List of entity dicts with keys: text, label, start, end.
        """
        self._load_model()
        if not self._available:
            return []
        logger.info("Extracting entities from text (length=%d)", len(text))
        doc = self._nlp(text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]

    def extract_organizations(self, text: str) -> list[str]:
        """Extract organization names from text.

        Filters NER results to only return ORG entities, which are
        the most relevant for ticker resolution.

        Args:
            text: Text to process.

        Returns:
            List of organization name strings.
        """
        entities = self.extract_entities(text)
        return [e["text"] for e in entities if e.get("label") == "ORG"]
