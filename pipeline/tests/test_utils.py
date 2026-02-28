"""Tests for pipeline utility modules."""

from pipeline.utils.text_cleaner import clean_html, clean_article_text, truncate
from pipeline.utils.deduplication import (
    compute_content_hash,
    is_duplicate,
    fuzzy_deduplicate,
)
from pipeline.utils.indian_market import (
    get_yahoo_ticker,
    NIFTY50_TICKERS,
    SECTORS,
    SECTOR_KEYWORDS,
)


class TestCleanHtml:
    def test_strips_tags(self):
        assert "Hello world" in clean_html("<p>Hello <b>world</b></p>")

    def test_decodes_entities(self):
        assert "&" in clean_html("foo &amp; bar")

    def test_handles_empty_string(self):
        assert clean_html("") == ""

    def test_normalizes_whitespace(self):
        result = clean_html("<p>  lots   of   spaces  </p>")
        assert "  " not in result


class TestCleanArticleText:
    def test_removes_boilerplate(self):
        text = "Some news content. Also Read: More articles here."
        result = clean_article_text(text)
        assert "Also Read" not in result

    def test_removes_disclaimer(self):
        text = "Market update. Disclaimer: This is not investment advice."
        result = clean_article_text(text)
        assert "Disclaimer" not in result

    def test_normalizes_whitespace(self):
        text = "Some   text\n\nwith   weird   spacing"
        result = clean_article_text(text)
        assert "  " not in result

    def test_removes_pti_attribution(self):
        text = "Market news here. (With inputs from PTI)"
        result = clean_article_text(text)
        assert "PTI" not in result


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", 100) == "hello"

    def test_truncates_at_word_boundary(self):
        result = truncate("hello world this is a test", 15)
        assert result.endswith("...")
        assert len(result) <= 18  # 15 + "..."

    def test_preserves_word_boundaries(self):
        result = truncate("The quick brown fox jumps over the lazy dog", 20)
        assert not result[:-3].endswith(" ")  # No trailing space before ...


class TestContentHash:
    def test_same_content_same_hash(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("goodbye world")
        assert h1 != h2

    def test_case_insensitive(self):
        h1 = compute_content_hash("Hello World")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_whitespace_normalized(self):
        h1 = compute_content_hash("  hello world  ")
        h2 = compute_content_hash("hello world")
        assert h1 == h2


class TestIsDuplicate:
    def test_detects_duplicate(self):
        hashes = {"abc123", "def456"}
        assert is_duplicate("abc123", hashes)

    def test_allows_new_content(self):
        hashes = {"abc123", "def456"}
        assert not is_duplicate("ghi789", hashes)

    def test_empty_set(self):
        assert not is_duplicate("abc123", set())


class TestFuzzyDeduplicate:
    def test_detects_near_duplicate(self):
        existing = ["Sensex rises 200 points on banking rally"]
        assert fuzzy_deduplicate("Sensex rises 200 pts on banking rally", existing)

    def test_allows_different_title(self):
        existing = ["Sensex rises 200 points on banking rally"]
        assert not fuzzy_deduplicate("RBI keeps repo rate unchanged", existing)

    def test_empty_list(self):
        assert not fuzzy_deduplicate("Any title", [])

    def test_custom_threshold(self):
        existing = ["Sensex rises 200 points"]
        # With a very high threshold, even similar titles won't match
        assert not fuzzy_deduplicate("Sensex rises 200 pts", existing, threshold=0.99)


class TestIndianMarket:
    def test_get_yahoo_ticker(self):
        assert get_yahoo_ticker("RELIANCE") == "RELIANCE.NS"
        assert get_yahoo_ticker("TCS") == "TCS.NS"
        assert get_yahoo_ticker("HDFCBANK") == "HDFCBANK.NS"

    def test_nifty50_has_50_tickers(self):
        assert len(NIFTY50_TICKERS) == 50

    def test_major_tickers_present(self):
        for ticker in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]:
            assert ticker in NIFTY50_TICKERS

    def test_sectors_dict_populated(self):
        assert len(SECTORS) > 0
        assert "Banking & Finance" in SECTORS
        assert "Information Technology" in SECTORS

    def test_sector_keywords_populated(self):
        assert len(SECTOR_KEYWORDS) > 0
        assert "bank" in SECTOR_KEYWORDS["Banking & Finance"]
        assert "IT" in SECTOR_KEYWORDS["Information Technology"]
