"""Reddit client wrapper using PRAW."""

import logging

from pipeline.config import settings

logger = logging.getLogger(__name__)


class RedditClient:
    """Wrapper around PRAW for scraping Indian finance subreddits."""

    def __init__(self) -> None:
        """Initialize the Reddit client with PRAW.

        Lazily initializes PRAW using credentials from pipeline settings.
        """
        self._reddit = None

    def _get_reddit(self):
        """Lazily initialize PRAW Reddit instance."""
        if self._reddit is None:
            if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
                logger.warning(
                    "Reddit credentials not configured. Set REDDIT_CLIENT_ID and "
                    "REDDIT_CLIENT_SECRET in environment or .env file."
                )
                return None
            logger.info("Initializing PRAW Reddit client")
            import praw

            self._reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            logger.info("PRAW Reddit client initialized successfully")
        return self._reddit

    def get_hot_posts(self, subreddit: str, limit: int = 25) -> list[dict]:
        """Fetch hot posts from a subreddit.

        Args:
            subreddit: Subreddit name (without r/ prefix).
            limit: Maximum number of posts to fetch.

        Returns:
            List of post dicts with title, text, score, url, author, created.
        """
        logger.info("Fetching hot posts from r/%s (limit=%d)", subreddit, limit)
        try:
            reddit = self._get_reddit()
            if reddit is None:
                return []
            posts = []
            for post in reddit.subreddit(subreddit).hot(limit=limit):
                posts.append(
                    {
                        "id": post.id,
                        "title": post.title,
                        "text": post.selftext,
                        "score": post.score,
                        "url": post.url,
                        "author": str(post.author),
                        "created_utc": post.created_utc,
                        "num_comments": post.num_comments,
                        "subreddit": post.subreddit.display_name,
                    }
                )
            logger.info("Fetched %d posts from r/%s", len(posts), subreddit)
            return posts
        except Exception as e:
            logger.error("Error fetching hot posts from r/%s: %s", subreddit, str(e))
            return []

    def get_comments(self, post_id: str) -> list[dict]:
        """Fetch comments for a Reddit post.

        Args:
            post_id: Reddit post ID.

        Returns:
            List of comment dicts with text, score, author.
        """
        logger.info("Fetching comments for post: %s", post_id)
        try:
            reddit = self._get_reddit()
            if reddit is None:
                return []
            submission = reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            comments = []
            for comment in submission.comments.list()[:50]:
                comments.append(
                    {
                        "id": comment.id,
                        "text": comment.body,
                        "score": comment.score,
                        "author": str(comment.author),
                    }
                )
            logger.info("Fetched %d comments for post %s", len(comments), post_id)
            return comments
        except Exception as e:
            logger.error("Error fetching comments for post %s: %s", post_id, str(e))
            return []

    def search_posts(self, query: str, subreddit: str) -> list[dict]:
        """Search for posts matching a query in a subreddit.

        Args:
            query: Search query string.
            subreddit: Subreddit name (without r/ prefix).

        Returns:
            List of matching post dicts.
        """
        logger.info("Searching r/%s for: %s", subreddit, query)
        try:
            reddit = self._get_reddit()
            if reddit is None:
                return []
            posts = []
            for post in reddit.subreddit(subreddit).search(query, limit=25):
                posts.append(
                    {
                        "id": post.id,
                        "title": post.title,
                        "text": post.selftext,
                        "score": post.score,
                        "url": post.url,
                        "author": str(post.author),
                        "created_utc": post.created_utc,
                        "num_comments": post.num_comments,
                        "subreddit": post.subreddit.display_name,
                    }
                )
            logger.info(
                "Found %d posts matching '%s' in r/%s", len(posts), query, subreddit
            )
            return posts
        except Exception as e:
            logger.error("Error searching r/%s for '%s': %s", subreddit, query, str(e))
            return []
