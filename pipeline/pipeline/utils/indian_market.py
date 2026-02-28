"""Indian market utilities, constants, and helper functions."""

from datetime import datetime, timezone, timedelta

# IST timezone offset
IST = timezone(timedelta(hours=5, minutes=30))

# Nifty 50 constituent tickers (NSE)
NIFTY50_TICKERS: list[str] = [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJFINANCE",
    "BAJAJFINSV",
    "BPCL",
    "BHARTIARTL",
    "BRITANNIA",
    "CIPLA",
    "COALINDIA",
    "DIVISLAB",
    "DRREDDY",
    "EICHERMOT",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SBIN",
    "SHREECEM",
    "SUNPHARMA",
    "TATACONSUM",
    "TATAMOTORS",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
    "VEDL",
    "WIPRO",
]

# Indian market sectors with descriptions
SECTORS: dict[str, str] = {
    "Banking & Finance": "Commercial banks, NBFCs, insurance, and financial services",
    "Information Technology": "IT services, software, and technology companies",
    "Oil & Gas": "Upstream, downstream, and integrated oil & gas companies",
    "Pharmaceuticals": "Drug manufacturers, API producers, and healthcare",
    "Automobiles": "Car, two-wheeler, and commercial vehicle manufacturers",
    "FMCG": "Fast-moving consumer goods and consumer staples",
    "Metals & Mining": "Steel, aluminum, copper, and mining companies",
    "Telecom": "Telecommunications service providers",
    "Infrastructure": "Construction, engineering, and infrastructure developers",
    "Real Estate": "Real estate developers and REITs",
    "Power & Energy": "Power generation, transmission, and distribution",
    "Cement": "Cement and building materials manufacturers",
    "Chemicals": "Specialty and commodity chemicals producers",
    "Media & Entertainment": "Broadcasting, digital media, and entertainment",
    "Aviation": "Airlines and aviation services",
}

# Keywords for sector classification from news articles
SECTOR_KEYWORDS: dict[str, list[str]] = {
    "Banking & Finance": [
        "bank",
        "banking",
        "NBFC",
        "loan",
        "credit",
        "deposit",
        "NPA",
        "interest rate",
        "RBI",
        "monetary policy",
        "repo rate",
        "lending",
        "insurance",
        "mutual fund",
        "fintech",
        "UPI",
        "digital payment",
    ],
    "Information Technology": [
        "IT",
        "software",
        "technology",
        "tech",
        "digital",
        "cloud",
        "SaaS",
        "outsourcing",
        "cybersecurity",
        "AI",
        "artificial intelligence",
        "machine learning",
        "data center",
        "semiconductor",
    ],
    "Oil & Gas": [
        "oil",
        "gas",
        "petroleum",
        "crude",
        "OPEC",
        "refinery",
        "fuel",
        "petrol",
        "diesel",
        "LPG",
        "natural gas",
        "energy",
    ],
    "Pharmaceuticals": [
        "pharma",
        "drug",
        "medicine",
        "healthcare",
        "hospital",
        "API",
        "FDA",
        "clinical trial",
        "vaccine",
        "generic",
        "biosimilar",
    ],
    "Automobiles": [
        "auto",
        "automobile",
        "car",
        "vehicle",
        "EV",
        "electric vehicle",
        "two-wheeler",
        "SUV",
        "motorcycle",
        "scooter",
        "truck",
    ],
    "FMCG": [
        "FMCG",
        "consumer",
        "food",
        "beverage",
        "personal care",
        "household",
        "retail",
        "e-commerce",
        "staples",
    ],
    "Metals & Mining": [
        "steel",
        "metal",
        "mining",
        "aluminum",
        "copper",
        "zinc",
        "iron ore",
        "gold",
        "silver",
        "commodity",
    ],
    "Telecom": [
        "telecom",
        "5G",
        "spectrum",
        "broadband",
        "mobile",
        "subscriber",
        "ARPU",
        "tower",
        "fiber",
    ],
    "Infrastructure": [
        "infrastructure",
        "construction",
        "highway",
        "road",
        "railway",
        "metro",
        "port",
        "smart city",
        "urban development",
    ],
    "Real Estate": [
        "real estate",
        "property",
        "housing",
        "residential",
        "commercial",
        "REIT",
        "builder",
        "apartment",
        "office space",
    ],
    "Power & Energy": [
        "power",
        "electricity",
        "solar",
        "wind",
        "renewable",
        "thermal",
        "hydro",
        "transmission",
        "grid",
    ],
    "Cement": [
        "cement",
        "concrete",
        "clinker",
        "building material",
    ],
    "Chemicals": [
        "chemical",
        "specialty chemical",
        "agrochemical",
        "fertilizer",
        "polymer",
        "plastic",
    ],
    "Media & Entertainment": [
        "media",
        "entertainment",
        "OTT",
        "streaming",
        "broadcasting",
        "advertising",
        "content",
        "film",
        "cinema",
    ],
    "Aviation": [
        "airline",
        "aviation",
        "airport",
        "flight",
        "aircraft",
        "passenger",
        "cargo",
    ],
}


def get_yahoo_ticker(nse_ticker: str) -> str:
    """Convert an NSE ticker symbol to Yahoo Finance format.

    Args:
        nse_ticker: NSE ticker symbol (e.g., "RELIANCE").

    Returns:
        Yahoo Finance ticker with .NS suffix (e.g., "RELIANCE.NS").
    """
    return f"{nse_ticker}.NS"


def is_market_hours() -> bool:
    """Check if the Indian stock market (NSE/BSE) is currently open.

    Market hours: 9:15 AM - 3:30 PM IST, Monday to Friday.
    Does not account for market holidays.

    Returns:
        True if current time is within market hours, False otherwise.
    """
    now = datetime.now(IST)

    # Check weekday (Monday=0, Friday=4)
    if now.weekday() > 4:
        return False

    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return market_open <= now <= market_close
