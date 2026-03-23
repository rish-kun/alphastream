from contextlib import contextmanager
from unittest.mock import MagicMock, patch
import time

from pipeline.tasks.reddit_scraper import scrape_subreddit

def _make_db_ctx(mock_db):
    def _factory():
        @contextmanager
        def _ctx():
            yield mock_db
        return _ctx()
    return _factory

@patch("pipeline.tasks.reddit_scraper.get_db")
@patch("pipeline.tasks.reddit_scraper.RedditClient")
def test_reddit_scraper_performance(MockClient, mock_get_db):
    # Set up mock reddit client
    mock_client = MagicMock()
    # 100 posts
    mock_client.get_hot_posts.return_value = [
        {
            "url": f"http://reddit.com/post/{i}",
            "title": f"Post {i}",
            "text": "This is a long text " * 20,
            "score": 10,
            "num_comments": 5,
            "created_utc": 1600000000 + i
        } for i in range(100)
    ]
    MockClient.return_value = mock_client

    # Set up mock DB
    mock_db = MagicMock()

    # We need to simulate the db execution
    # To count executions:
    executions = []
    def db_execute_side_effect(query, params=None):
        executions.append((query, params))

        result = MagicMock()
        query_str = str(query)
        if "SELECT id FROM social_sentiments" in query_str:
            result.fetchone.return_value = None
        elif "INSERT INTO news_articles" in query_str and "RETURNING id" in query_str:
            result.fetchone.return_value = (42,)
        return result

    mock_db.execute.side_effect = db_execute_side_effect
    mock_get_db.side_effect = _make_db_ctx(mock_db)

    with patch("pipeline.tasks.reddit_scraper.analyze_article.delay"):
        start_time = time.time()
        result = scrape_subreddit("IndianStreetBets", limit=100)
        end_time = time.time()

        print(f"Scraped {result['posts_scraped']} posts")
        print(f"Total DB execute calls: {len(executions)}")
        print(f"Time taken: {end_time - start_time:.4f}s")
