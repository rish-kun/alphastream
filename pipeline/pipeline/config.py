from pydantic_settings import BaseSettings


class PipelineSettings(BaseSettings):
    # Database (sync driver for Celery tasks)
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5433/alphastream"
    )
    REDIS_URL: str = "redis://localhost:6380/0"

    # API Keys
    GEMINI_API_KEYS: list[str] = []
    OPENROUTER_API_KEYS: list[str] = []

    # Reddit
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "AlphaStream/0.1"

    # Twitter
    TWITTER_BEARER_TOKEN: str = ""

    # Scraping
    SCRAPE_TIMEOUT: int = 30
    MAX_ARTICLES_PER_FEED: int = 50

    # ML
    FINBERT_MODEL: str = "ProsusAI/finbert"
    SPACY_MODEL: str = "en_core_web_sm"

    # Extensive Research API Keys
    FIRECRAWL_API_KEY: str = ""
    BROWSEAI_API_KEY: str = ""
    BROWSEAI_DEFAULT_ROBOT_ID: str = ""
    THUNDERBIT_API_KEY: str = ""

    # Rate limiting
    LLM_REQUESTS_PER_MINUTE: int = 15
    RSS_FETCH_TIMEOUT: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = PipelineSettings()
