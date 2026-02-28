"""Prompt templates for LLM-based financial analysis."""

SENTIMENT_ANALYSIS_PROMPT = """
You are an institutional-grade financial analyst specializing in the Indian stock market (NSE/BSE).

Analyze the following news article and provide a structured JSON response:

Article: {article_text}

Context (if any): {context}

Respond ONLY with valid JSON in this exact format:
{{
    "sentiment_score": <float between -1.0 and 1.0>,
    "confidence": <float between 0.0 and 1.0>,
    "explanation": "<2-3 sentence explanation of market impact>",
    "impact_timeline": "<one of: immediate, short_term, long_term>",
    "affected_sectors": [<list of affected sectors>],
    "mentioned_tickers": [<list of NSE ticker symbols>],
    "key_themes": [<list of key themes>]
}}
"""

PORTFOLIO_ANALYSIS_PROMPT = """
You are an institutional-grade portfolio analyst specializing in the Indian stock market (NSE/BSE).

Given the following portfolio holdings and recent news sentiment data, provide a structured risk assessment.

Portfolio Holdings:
{holdings}

Recent Sentiment Data:
{sentiment_data}

Respond ONLY with valid JSON in this exact format:
{{
    "overall_risk_score": <float between 0.0 and 1.0>,
    "risk_factors": [<list of identified risk factors>],
    "sector_exposure": {{<sector: exposure_percentage>}},
    "recommendations": [<list of actionable recommendations>],
    "outlook": "<one of: bullish, neutral, bearish>"
}}
"""
