<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# i want to make a financial news analyser for the indian markets

the goal would of the project would be to go through the latest national, international and financial news
it should first aggregate news from multiple places and then find the analysis it would have on the indian market with an explanation for it
the main aim is  Institutional-grade news sentiment analysis for alpha generation

tech stack: FastAPI (backend)+ NextJS (frontend) + python piplelines and free AI APIs (such as gemini) for sentiment analysis

The user should be able to search for stocks and find news regarding those stocks and how those news might affect the stocks, they should also be able to add stocks in their portfolio and then perform a portfolio wide search. the website should have realtime feedback, websockets for data streaming, ML models for semantic identification and Gemini, OpenRouter support for finding the analysis of the news. Apart from this there should be a complete web scraping system which would search the news from rss feeds, scrape it from news sites, identify people sentiments/comments related to the news from twitter, reddit (scraping) again
it is okay to use custom ML models

[https://github.com/jaikaushik-prog/news-alpha-pipeline](https://github.com/jaikaushik-prog/news-alpha-pipeline)
[https://github.com/wsc-bitspilani/news-analyser](https://github.com/wsc-bitspilani/news-analyser)

here are 2 basic implementations

give me a final PRD of this

Here is a complete Product Requirements Document (PRD) for your institutional-grade financial news analyzer, combining your requested tech stack with the best architectural concepts from the reference implementations.

## Product Overview

**Name:** AlphaStream India (Placeholder)
**Vision:** An institutional-grade financial news and sentiment analysis platform tailored for the Indian stock market. It aggregates multi-channel news and social data, processes it through ML and LLM pipelines, and streams actionable alpha-generation insights to users in real time.
**Target Audience:** Retail investors, quantitative researchers, and finance students looking for real-time edge (alpha) in Indian equities.

## Tech Stack Architecture

- **Frontend:** NextJS for server-side rendering, React hooks for state management, and Tailwind CSS for styling.
- **Backend:** FastAPI for high-performance async API endpoints and WebSocket management.
- **Database \& Caching:** PostgreSQL for persistent user and portfolio data; Redis for task queuing, caching, and WebSocket Pub/Sub streams.
- **Data Pipelines:** Python (Celery/RQ) for async background scraping and processing tasks.
- **AI \& ML:** Gemini API and OpenRouter for core sentiment reasoning; HuggingFace/custom local ML models (e.g., FinBERT) for fast semantic identification and Named Entity Recognition (NER).


## Core Features

### 1. Multi-Source Data Aggregation

- **RSS Feed Ingestion:** Automatically poll feeds from top Indian financial outlets (MoneyControl, Economic Times, LiveMint, Business Standard, CNBC TV18) .
- **Web Scraping:** Extract full-text articles from targeted URLs to bypass RSS summary limits.
- **Social Sentiment Scraping:** Fetch retail sentiment and public commentary from targeted Reddit threads (e.g., r/IndianStreetBets) and Twitter/X queries.


### 2. Institutional-Grade Sentiment Analysis

- **LLM Reasoning:** Pass aggregated text to Gemini/OpenRouter to extract structured data: sentiment score (-1.0 to +1.0), confidence level, a 2-3 sentence market explanation, and the estimated impact timeline (immediate, short-term, long-term) .
- **Alpha Generation Metrics:** Implement institutional concepts like *Expectation Gap* (sentiment surprise versus baseline), *Narrative Velocity* (speed of information spread), and *Sentiment-Price Divergence* .
- **Semantic Ticker Identification:** Use custom local ML models to identify and tag Indian stock tickers (e.g., RELIANCE, TCS) mentioned in unstructured text, even when slang or abbreviations are used.


### 3. Portfolio \& Watchlist Management

- **Stock Tracking:** Allow users to search for specific stocks and view a dedicated dashboard of localized news and impact analysis.
- **Portfolio-Wide Search:** Enable users to build custom watchlists and execute aggregate searches that filter the global news stream exclusively for their held assets.


### 4. Real-Time Streaming \& UI

- **WebSocket Integration:** Stream newly analyzed news items directly to the NextJS frontend via FastAPI WebSockets and Redis, providing a live-updating feed without page refreshes.
- **Interactive Dashboards:** Display sentiment trends, recent articles, and Alpha metrics using frontend charting libraries.


## Data Pipeline Flow

1. **Ingestion:** Cron jobs and background workers continuously scrape RSS feeds, news sites, and social APIs.
2. **Preprocessing:** Clean text, remove HTML boilerplate, and run the custom ML semantic model to identify relevant stock tickers.
3. **Inference:** Send cleaned text to Gemini/OpenRouter with a strict prompt template to return structured JSON sentiment data.
4. **Storage \& Broadcast:** Save the structured analysis to PostgreSQL. Simultaneously publish the payload to a Redis channel, which the FastAPI WebSocket manager reads to push live updates to connected NextJS clients.

## System Requirements

- **Concurrency:** FastAPI and Redis must support at least concurrent WebSocket connections for real-time client updates.
- **API Rate Limiting:** Implement API key rotation or exponential backoff in the Celery/background workers to handle rate limits from free tiers of Gemini and OpenRouter .
- **Error Handling:** Gracefully handle temporary scraper blocks, broken RSS XML structures, and LLM hallucinations by falling back to neutral sentiment scores.

