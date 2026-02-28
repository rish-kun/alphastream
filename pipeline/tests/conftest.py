"""Shared test fixtures for the AlphaStream pipeline test suite."""

import pytest


@pytest.fixture
def sample_article_text() -> str:
    """Sample Indian financial news article text."""
    return (
        "Reliance Industries Ltd reported a 12% rise in quarterly net profit, "
        "beating analyst estimates. The company's retail and digital services "
        "segments showed strong growth. Analysts at HDFC Securities maintained "
        "a buy rating with a target price of Rs 2,800. The stock rose 2.5% "
        "on the NSE following the earnings announcement."
    )


@pytest.fixture
def sample_html_content() -> str:
    """Sample HTML content from a financial news page."""
    return (
        '<div class="article">'
        "<h1>Sensex Rises 500 Points</h1>"
        "<p>The BSE Sensex surged 500 points on Monday, driven by &amp; "
        "strong buying in banking &amp; IT stocks.</p>"
        '<p class="disclaimer">Disclaimer: This is not investment advice.</p>'
        "</div>"
    )


@pytest.fixture
def sample_titles() -> list[str]:
    """Sample article titles for deduplication testing."""
    return [
        "Sensex rises 200 points on banking rally",
        "Nifty crosses 22,000 mark for the first time",
        "RBI keeps repo rate unchanged at 6.5%",
        "Tata Motors Q3 results beat estimates",
        "HDFC Bank reports strong loan growth",
    ]
