from pydantic import field_validator
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

    @field_validator("GEMINI_API_KEYS", "OPENROUTER_API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [k.strip() for k in v.split(",") if k.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Force a sync Postgres driver for Celery/SQLAlchemy sync engine."""
        if isinstance(v, str) and v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        return v

    @field_validator("SENTIMENT_LLM_PROVIDER_ORDER", mode="before")
    @classmethod
    def parse_provider_order(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return ["gemini", "openrouter"]
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [
                        str(item).strip().lower()
                        for item in parsed
                        if str(item).strip()
                    ]
            except json.JSONDecodeError:
                pass
            return [item.strip().lower() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip().lower() for item in v if str(item).strip()]
        return ["gemini", "openrouter"]

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
    SENTIMENT_FINBERT_MODEL: str = "ProsusAI/finbert"
    SENTIMENT_GEMINI_MODEL: str = "gemini-3-flash-preview"
    SENTIMENT_OPENROUTER_MODEL: str = "stepfun/step-3.5-flash:free"
    SENTIMENT_LLM_PROVIDER_ORDER: list[str] = ["gemini", "openrouter"]
    SENTIMENT_FINBERT_MAX_CHARS: int = 3000
    SENTIMENT_FINBERT_MAX_CHUNKS: int = 3
    SENTIMENT_LLM_MAX_CHARS: int = 2200
    SENTIMENT_LLM_TRIGGER_CONFIDENCE: float = 0.70
    SENTIMENT_LLM_TRIGGER_NEUTRAL_BAND: float = 0.20
    SENTIMENT_LOCAL_WEIGHT: float = 0.65
    SENTIMENT_LLM_WEIGHT: float = 0.35
    SENTIMENT_ENABLE_LLM: bool = True
    SENTIMENT_PENDING_BATCH_SIZE: int = 50
    SENTIMENT_REANALYZE_BATCH_LIMIT: int = 100

    # Extensive Research API Keys
    FIRECRAWL_API_KEY: str = ""
    BROWSEAI_API_KEY: str = ""
    BROWSEAI_TEAM_ID: str = ""
    BROWSEAI_DEFAULT_ROBOT_ID: str = ""
    THUNDERBIT_API_KEY: str = ""

    # Rate limiting
    LLM_REQUESTS_PER_MINUTE: int = 15
    RSS_FETCH_TIMEOUT: int = 30

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "enable_decoding": False,
    }


settings = PipelineSettings()
