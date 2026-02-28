"""initial_schema

Revision ID: 001
Revises:
Create Date: 2025-02-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the initial schema."""

    # --- users ---
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("oauth_provider", sa.String(20), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("gemini_api_key", sa.String(255), nullable=True),
        sa.Column("openrouter_api_key", sa.String(255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # --- stocks ---
    op.create_table(
        "stocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("exchange", sa.String(10), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("market_cap", sa.BigInteger(), nullable=True),
        sa.Column(
            "aliases",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("last_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index(op.f("ix_stocks_ticker"), "stocks", ["ticker"], unique=True)
    op.create_index(op.f("ix_stocks_sector"), "stocks", ["sector"], unique=False)

    # --- news_articles ---
    op.create_table(
        "news_articles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(
        op.f("ix_news_articles_source"), "news_articles", ["source"], unique=False
    )
    op.create_index(
        op.f("ix_news_articles_published_at"),
        "news_articles",
        ["published_at"],
        unique=False,
    )

    # --- article_stock_mentions ---
    op.create_table(
        "article_stock_mentions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relevance_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("mentioned_as", sa.String(100), nullable=False),
        sa.Column("impact_direction", sa.String(10), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["news_articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"],
            ["stocks.id"],
            ondelete="CASCADE",
        ),
    )

    # --- sentiment_analyses ---
    op.create_table(
        "sentiment_analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("impact_timeline", sa.String(20), nullable=False),
        sa.Column("finbert_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("llm_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("llm_provider", sa.String(20), nullable=True),
        sa.Column(
            "raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["news_articles.id"],
            ondelete="CASCADE",
        ),
    )

    # --- alpha_metrics ---
    op.create_table(
        "alpha_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("expectation_gap", sa.Numeric(6, 4), nullable=False),
        sa.Column("narrative_velocity", sa.Numeric(6, 4), nullable=False),
        sa.Column("sentiment_divergence", sa.Numeric(6, 4), nullable=False),
        sa.Column("composite_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("signal", sa.String(20), nullable=False),
        sa.Column("conviction", sa.Numeric(4, 3), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("window_hours", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["stock_id"],
            ["stocks.id"],
            ondelete="CASCADE",
        ),
    )

    # --- social_sentiments ---
    op.create_table(
        "social_sentiments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("post_url", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(4, 3), nullable=False),
        sa.Column(
            "engagement",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["news_articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"],
            ["stocks.id"],
            ondelete="CASCADE",
        ),
    )

    # --- portfolios ---
    op.create_table(
        "portfolios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    # --- portfolio_stocks ---
    op.create_table(
        "portfolio_stocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), nullable=True),
        sa.Column("avg_buy_price", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"],
            ["stocks.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("portfolio_stocks")
    op.drop_table("portfolios")
    op.drop_table("social_sentiments")
    op.drop_table("alpha_metrics")
    op.drop_table("sentiment_analyses")
    op.drop_table("article_stock_mentions")
    op.drop_index(op.f("ix_news_articles_published_at"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_source"), table_name="news_articles")
    op.drop_table("news_articles")
    op.drop_index(op.f("ix_stocks_sector"), table_name="stocks")
    op.drop_index(op.f("ix_stocks_ticker"), table_name="stocks")
    op.drop_table("stocks")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
