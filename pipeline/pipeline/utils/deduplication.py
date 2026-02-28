"""Content deduplication utilities."""

import hashlib
from difflib import SequenceMatcher


def compute_content_hash(text: str) -> str:
    """Compute an MD5 hash of text content for deduplication.

    Args:
        text: Text content to hash.

    Returns:
        Hex-encoded MD5 hash string.
    """
    normalized = text.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def is_duplicate(content_hash: str, existing_hashes: set[str]) -> bool:
    """Check if a content hash already exists in the known set.

    Args:
        content_hash: MD5 hash of the content to check.
        existing_hashes: Set of known content hashes.

    Returns:
        True if the hash is a duplicate, False otherwise.
    """
    return content_hash in existing_hashes


def fuzzy_deduplicate(
    title: str, existing_titles: list[str], threshold: float = 0.85
) -> bool:
    """Check if a title is a fuzzy duplicate of any existing title.

    Uses SequenceMatcher to compute similarity ratios. Useful for
    catching near-duplicate articles with slightly different headlines
    (e.g., "Sensex rises 200 pts" vs "Sensex surges 200 points").

    Args:
        title: Title to check for duplicates.
        existing_titles: List of existing title strings to compare against.
        threshold: Similarity threshold (0.0-1.0). Default 0.85.

    Returns:
        True if the title is a fuzzy duplicate, False otherwise.
    """
    title_lower = title.strip().lower()
    for existing in existing_titles:
        existing_lower = existing.strip().lower()
        ratio = SequenceMatcher(None, title_lower, existing_lower).ratio()
        if ratio >= threshold:
            return True
    return False
