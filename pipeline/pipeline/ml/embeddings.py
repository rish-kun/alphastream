"""Sentence embeddings for text similarity and clustering."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Generates sentence embeddings for text similarity computation.

    Uses a transformer-based sentence embedding model for encoding
    financial text into dense vector representations.
    """

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        """Initialize the embedding model with lazy loading.

        Args:
            model_name: HuggingFace model name for sentence embeddings.
        """
        self._model_name = model_name
        self._model = None
        self._available = False

    def _load_model(self) -> None:
        """Lazily load the sentence embedding model."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            self._available = True
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, embeddings unavailable"
            )
            self._available = False

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into dense vector embeddings.

        Args:
            texts: List of text strings to encode.

        Returns:
            NumPy array of shape (len(texts), embedding_dim).
        """
        self._load_model()
        if not self._available:
            logger.info("Encoding %d texts (returning zeros)", len(texts))
            return np.zeros((len(texts), 384))
        logger.info("Encoding %d texts", len(texts))
        return self._model.encode(texts, convert_to_numpy=True)

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts.

        Args:
            text1: First text string.
            text2: Second text string.

        Returns:
            Cosine similarity score between 0.0 and 1.0.
        """
        embeddings = self.encode([text1, text2])
        # Cosine similarity
        norm1 = np.linalg.norm(embeddings[0])
        norm2 = np.linalg.norm(embeddings[1])
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(embeddings[0], embeddings[1]) / (norm1 * norm2))
