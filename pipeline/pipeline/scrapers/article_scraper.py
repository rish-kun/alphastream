"""Full-text article scraper using newspaper4k."""

import logging
import re

logger = logging.getLogger(__name__)


class ArticleScraper:
    """Extracts full-text content from article URLs using newspaper4k."""

    def scrape(self, url: str) -> str | None:
        """Scrape full article text from a URL.

        Args:
            url: URL of the article to scrape.

        Returns:
            Cleaned article text, or None if extraction fails.
        """
        logger.info("Scraping article: %s", url)
        try:
            from newspaper import Article

            article = Article(url)
            article.download()
            article.parse()
            text = article.text
            if text:
                return self.clean_text(text)
            return None
        except Exception as e:
            logger.warning("Failed to scrape article %s: %s", url, e)
            return None

    def clean_text(self, text: str) -> str:
        """Clean extracted article text.

        Removes extra whitespace, ads boilerplate, and normalizes
        the text for downstream NLP processing.

        Args:
            text: Raw extracted article text.

        Returns:
            Cleaned text string.
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r"(?i)also\s+read\s*:",
            r"(?i)recommended\s+stories",
            r"(?i)subscribe\s+to\s+our\s+newsletter",
            r"(?i)click\s+here\s+to\s+read",
            r"(?i)follow\s+us\s+on\s+twitter",
            r"(?i)download\s+the\s+app",
        ]
        for pattern in boilerplate_patterns:
            text = re.sub(pattern + r".*?(?:\.|$)", "", text)
        return text.strip()
