"""Text cleaning utilities for financial news content."""

import html
import re


def clean_html(html_content: str) -> str:
    """Strip HTML tags and decode HTML entities.

    Args:
        html_content: Raw HTML string.

    Returns:
        Plain text with tags removed and entities decoded.
    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html_content)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_article_text(text: str) -> str:
    """Clean and normalize article text for NLP processing.

    Removes boilerplate, normalizes whitespace, and strips common
    noise patterns from Indian financial news articles.

    Args:
        text: Raw article text.

    Returns:
        Cleaned and normalized text.
    """
    # Normalize unicode whitespace
    text = re.sub(r"[\u00a0\u200b\u200c\u200d\ufeff]", " ", text)
    # Normalize regular whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r"(?i)also\s+read\s*:.*?(?:\n|$)",
        r"(?i)recommended\s+stories.*?(?:\n|$)",
        r"(?i)subscribe\s+to\s+our\s+newsletter.*?(?:\n|$)",
        r"(?i)click\s+here\s+to\s+(?:read|know).*?(?:\n|$)",
        r"(?i)follow\s+us\s+on\s+(?:twitter|facebook|instagram).*?(?:\n|$)",
        r"(?i)download\s+the\s+(?:app|moneycontrol).*?(?:\n|$)",
        r"(?i)disclaimer\s*:.*?(?:\n|$)",
        r"(?i)for\s+more\s+(?:details|information)\s*,?\s*(?:visit|click).*?(?:\n|$)",
        r"(?i)\(with\s+inputs\s+from\s+(?:PTI|IANS|Reuters|ANI)\)",
        r"(?i)first\s+published\s+on.*?(?:\n|$)",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text)
    # Final whitespace cleanup
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text: str, max_length: int) -> str:
    """Truncate text to a maximum length, preserving word boundaries.

    Args:
        text: Text to truncate.
        max_length: Maximum character length.

    Returns:
        Truncated text, with "..." appended if truncated.
    """
    if len(text) <= max_length:
        return text
    # Find the last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated.rstrip() + "..."
