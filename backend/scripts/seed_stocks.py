"""Seed the stocks table with Nifty 50 constituents.

Usage:
    cd /home/rishit/personal/as2/backend
    uv run python scripts/seed_stocks.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ── Nifty 50 stock data ──────────────────────────────────────────────────────
# Each entry: (nse_ticker, company_name, sector, industry, aliases)
NIFTY50_STOCKS: list[tuple[str, str, str, str, list[str]]] = [
    (
        "ADANIENT",
        "Adani Enterprises Ltd",
        "Infrastructure",
        "Diversified",
        ["Adani Enterprises", "Adani"],
    ),
    (
        "ADANIPORTS",
        "Adani Ports & SEZ Ltd",
        "Infrastructure",
        "Port Operations",
        ["Adani Ports", "APSEZ"],
    ),
    (
        "APOLLOHOSP",
        "Apollo Hospitals Enterprise Ltd",
        "Pharmaceuticals",
        "Healthcare Services",
        ["Apollo Hospitals", "Apollo"],
    ),
    ("ASIANPAINT", "Asian Paints Ltd", "FMCG", "Paints & Coatings", ["Asian Paints"]),
    (
        "AXISBANK",
        "Axis Bank Ltd",
        "Banking & Finance",
        "Private Banks",
        ["Axis Bank", "Axis"],
    ),
    (
        "BAJAJ-AUTO",
        "Bajaj Auto Ltd",
        "Automobiles",
        "Two-Wheelers",
        ["Bajaj Auto", "Bajaj"],
    ),
    (
        "BAJFINANCE",
        "Bajaj Finance Ltd",
        "Banking & Finance",
        "NBFCs",
        ["Bajaj Finance", "BajFin"],
    ),
    (
        "BAJAJFINSV",
        "Bajaj Finserv Ltd",
        "Banking & Finance",
        "Financial Services",
        ["Bajaj Finserv"],
    ),
    (
        "BPCL",
        "Bharat Petroleum Corporation Ltd",
        "Oil & Gas",
        "Oil Refining & Marketing",
        ["Bharat Petroleum", "BPCL"],
    ),
    (
        "BHARTIARTL",
        "Bharti Airtel Ltd",
        "Telecom",
        "Telecom Services",
        ["Bharti Airtel", "Airtel"],
    ),
    ("BRITANNIA", "Britannia Industries Ltd", "FMCG", "Food Products", ["Britannia"]),
    ("CIPLA", "Cipla Ltd", "Pharmaceuticals", "Pharmaceuticals", ["Cipla"]),
    ("COALINDIA", "Coal India Ltd", "Metals & Mining", "Mining", ["Coal India", "CIL"]),
    (
        "DIVISLAB",
        "Divi's Laboratories Ltd",
        "Pharmaceuticals",
        "Pharmaceuticals",
        ["Divi's Labs", "Divis Lab"],
    ),
    (
        "DRREDDY",
        "Dr. Reddy's Laboratories Ltd",
        "Pharmaceuticals",
        "Pharmaceuticals",
        ["Dr Reddy's", "Dr Reddy", "DRL"],
    ),
    (
        "EICHERMOT",
        "Eicher Motors Ltd",
        "Automobiles",
        "Automobiles",
        ["Eicher Motors", "Royal Enfield"],
    ),
    (
        "GRASIM",
        "Grasim Industries Ltd",
        "Cement",
        "Cement & Diversified",
        ["Grasim", "Grasim Industries"],
    ),
    (
        "HCLTECH",
        "HCL Technologies Ltd",
        "Information Technology",
        "IT Services",
        ["HCL Tech", "HCL Technologies", "HCL"],
    ),
    (
        "HDFCBANK",
        "HDFC Bank Ltd",
        "Banking & Finance",
        "Private Banks",
        ["HDFC Bank", "HDFC"],
    ),
    (
        "HDFCLIFE",
        "HDFC Life Insurance Co Ltd",
        "Banking & Finance",
        "Life Insurance",
        ["HDFC Life"],
    ),
    (
        "HEROMOTOCO",
        "Hero MotoCorp Ltd",
        "Automobiles",
        "Two-Wheelers",
        ["Hero MotoCorp", "Hero"],
    ),
    (
        "HINDALCO",
        "Hindalco Industries Ltd",
        "Metals & Mining",
        "Aluminium",
        ["Hindalco", "Novelis"],
    ),
    (
        "HINDUNILVR",
        "Hindustan Unilever Ltd",
        "FMCG",
        "FMCG",
        ["Hindustan Unilever", "HUL"],
    ),
    (
        "ICICIBANK",
        "ICICI Bank Ltd",
        "Banking & Finance",
        "Private Banks",
        ["ICICI Bank", "ICICI"],
    ),
    (
        "INDUSINDBK",
        "IndusInd Bank Ltd",
        "Banking & Finance",
        "Private Banks",
        ["IndusInd Bank"],
    ),
    (
        "INFY",
        "Infosys Ltd",
        "Information Technology",
        "IT Services",
        ["Infosys", "Infy"],
    ),
    ("ITC", "ITC Ltd", "FMCG", "FMCG Conglomerate", ["ITC"]),
    ("JSWSTEEL", "JSW Steel Ltd", "Metals & Mining", "Steel", ["JSW Steel", "JSW"]),
    (
        "KOTAKBANK",
        "Kotak Mahindra Bank Ltd",
        "Banking & Finance",
        "Private Banks",
        ["Kotak Mahindra Bank", "Kotak Bank", "Kotak"],
    ),
    (
        "LT",
        "Larsen & Toubro Ltd",
        "Infrastructure",
        "Engineering & Construction",
        ["Larsen & Toubro", "L&T"],
    ),
    (
        "M&M",
        "Mahindra & Mahindra Ltd",
        "Automobiles",
        "Automobiles",
        ["Mahindra & Mahindra", "Mahindra", "M&M"],
    ),
    (
        "MARUTI",
        "Maruti Suzuki India Ltd",
        "Automobiles",
        "Passenger Vehicles",
        ["Maruti Suzuki", "Maruti"],
    ),
    (
        "NESTLEIND",
        "Nestle India Ltd",
        "FMCG",
        "Food Products",
        ["Nestle India", "Nestle"],
    ),
    ("NTPC", "NTPC Ltd", "Power & Energy", "Power Generation", ["NTPC"]),
    (
        "ONGC",
        "Oil & Natural Gas Corporation Ltd",
        "Oil & Gas",
        "Oil Exploration & Production",
        ["ONGC"],
    ),
    (
        "POWERGRID",
        "Power Grid Corporation of India Ltd",
        "Power & Energy",
        "Power Transmission",
        ["Power Grid", "PGCIL"],
    ),
    (
        "RELIANCE",
        "Reliance Industries Ltd",
        "Oil & Gas",
        "Diversified Conglomerate",
        ["Reliance Industries", "Reliance", "RIL"],
    ),
    (
        "SBILIFE",
        "SBI Life Insurance Co Ltd",
        "Banking & Finance",
        "Life Insurance",
        ["SBI Life"],
    ),
    (
        "SBIN",
        "State Bank of India",
        "Banking & Finance",
        "Public Sector Banks",
        ["SBI", "State Bank"],
    ),
    ("SHREECEM", "Shree Cement Ltd", "Cement", "Cement", ["Shree Cement"]),
    (
        "SUNPHARMA",
        "Sun Pharmaceutical Industries Ltd",
        "Pharmaceuticals",
        "Pharmaceuticals",
        ["Sun Pharma", "Sun Pharmaceutical"],
    ),
    (
        "TATACONSUM",
        "Tata Consumer Products Ltd",
        "FMCG",
        "Food & Beverages",
        ["Tata Consumer", "Tata Consumer Products"],
    ),
    ("TATAMOTORS", "Tata Motors Ltd", "Automobiles", "Automobiles", ["Tata Motors"]),
    ("TATASTEEL", "Tata Steel Ltd", "Metals & Mining", "Steel", ["Tata Steel"]),
    (
        "TCS",
        "Tata Consultancy Services Ltd",
        "Information Technology",
        "IT Services",
        ["TCS", "Tata Consultancy Services"],
    ),
    (
        "TECHM",
        "Tech Mahindra Ltd",
        "Information Technology",
        "IT Services",
        ["Tech Mahindra"],
    ),
    (
        "TITAN",
        "Titan Company Ltd",
        "FMCG",
        "Jewellery & Watches",
        ["Titan", "Titan Company"],
    ),
    (
        "ULTRACEMCO",
        "UltraTech Cement Ltd",
        "Cement",
        "Cement",
        ["UltraTech Cement", "UltraTech"],
    ),
    ("VEDL", "Vedanta Ltd", "Metals & Mining", "Diversified Mining", ["Vedanta"]),
    ("WIPRO", "Wipro Ltd", "Information Technology", "IT Services", ["Wipro"]),
]


async def seed_stocks() -> None:
    """Insert Nifty 50 stocks into the database, skipping duplicates."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        inserted = 0
        skipped = 0

        for ticker, company_name, sector, industry, aliases in NIFTY50_STOCKS:
            yahoo_ticker = f"{ticker}.NS"

            # ON CONFLICT DO NOTHING via raw SQL for clean duplicate handling
            result = await session.execute(
                text(
                    """
                    INSERT INTO stocks (ticker, exchange, company_name, sector, industry, aliases)
                    VALUES (:ticker, :exchange, :company_name, :sector, :industry, :aliases::jsonb)
                    ON CONFLICT (ticker) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "ticker": yahoo_ticker,
                    "exchange": "NSE",
                    "company_name": company_name,
                    "sector": sector,
                    "industry": industry,
                    "aliases": str(aliases).replace("'", '"'),
                },
            )

            row = result.fetchone()
            if row:
                inserted += 1
            else:
                skipped += 1

        await session.commit()

    await engine.dispose()

    print(f"Seed complete: {inserted} inserted, {skipped} skipped (already existed)")
    print(f"Total Nifty 50 stocks: {len(NIFTY50_STOCKS)}")


if __name__ == "__main__":
    asyncio.run(seed_stocks())
