"""Map extracted entities to Indian stock tickers (NSE)."""

import logging

logger = logging.getLogger(__name__)

# Ticker alias dictionary: NSE ticker -> list of known aliases
# Covers Nifty 50 constituents and other major Indian companies
TICKER_ALIASES: dict[str, list[str]] = {
    "RELIANCE": ["Reliance", "RIL", "Reliance Industries"],
    "TCS": ["TCS", "Tata Consultancy", "Tata Consultancy Services"],
    "INFY": ["Infosys", "Infy"],
    "HDFCBANK": ["HDFC Bank", "HDFC"],
    "ICICIBANK": ["ICICI Bank", "ICICI"],
    "HINDUNILVR": ["Hindustan Unilever", "HUL"],
    "ITC": ["ITC", "ITC Limited"],
    "SBIN": ["SBI", "State Bank of India", "State Bank"],
    "BHARTIARTL": ["Bharti Airtel", "Airtel"],
    "KOTAKBANK": ["Kotak Mahindra Bank", "Kotak Bank", "Kotak"],
    "LT": ["Larsen & Toubro", "L&T", "Larsen and Toubro"],
    "AXISBANK": ["Axis Bank", "Axis"],
    "ASIANPAINT": ["Asian Paints", "Asian Paint"],
    "MARUTI": ["Maruti Suzuki", "Maruti"],
    "HCLTECH": ["HCL Technologies", "HCL Tech", "HCL"],
    "SUNPHARMA": ["Sun Pharma", "Sun Pharmaceutical"],
    "TATAMOTORS": ["Tata Motors", "Tata Motor"],
    "BAJFINANCE": ["Bajaj Finance", "Bajaj Fin"],
    "WIPRO": ["Wipro"],
    "ULTRACEMCO": ["UltraTech Cement", "UltraTech"],
    "ONGC": ["ONGC", "Oil and Natural Gas"],
    "NTPC": ["NTPC"],
    "POWERGRID": ["Power Grid", "Power Grid Corporation"],
    "TITAN": ["Titan", "Titan Company"],
    "ADANIENT": ["Adani Enterprises", "Adani"],
    "ADANIPORTS": ["Adani Ports", "Adani Ports and SEZ"],
    "TECHM": ["Tech Mahindra", "TechM"],
    "TATASTEEL": ["Tata Steel"],
    "NESTLEIND": ["Nestle India", "Nestle"],
    "BAJAJFINSV": ["Bajaj Finserv"],
    "JSWSTEEL": ["JSW Steel", "JSW"],
    "INDUSINDBK": ["IndusInd Bank", "IndusInd"],
    "DIVISLAB": ["Divi's Laboratories", "Divi's Lab", "Divis Lab"],
    "GRASIM": ["Grasim", "Grasim Industries"],
    "DRREDDY": ["Dr. Reddy's", "Dr Reddy", "Dr. Reddy's Laboratories"],
    "CIPLA": ["Cipla"],
    "EICHERMOT": ["Eicher Motors", "Royal Enfield"],
    "APOLLOHOSP": ["Apollo Hospitals", "Apollo"],
    "COALINDIA": ["Coal India", "CIL"],
    "BPCL": ["BPCL", "Bharat Petroleum"],
    "HEROMOTOCO": ["Hero MotoCorp", "Hero"],
    "BRITANNIA": ["Britannia", "Britannia Industries"],
    "HINDALCO": ["Hindalco", "Hindalco Industries"],
    "SBILIFE": ["SBI Life", "SBI Life Insurance"],
    "BAJAJ-AUTO": ["Bajaj Auto"],
    "TATACONSUM": ["Tata Consumer", "Tata Consumer Products"],
    "M&M": ["Mahindra & Mahindra", "M&M", "Mahindra"],
    "HDFCLIFE": ["HDFC Life", "HDFC Life Insurance"],
    "SHREECEM": ["Shree Cement"],
    "VEDL": ["Vedanta", "Vedanta Limited"],
    "BANKBARODA": ["Bank of Baroda", "BoB"],
    "PNB": ["Punjab National Bank", "PNB"],
    "ZOMATO": ["Zomato"],
    "PAYTM": ["Paytm", "One97 Communications"],
    "NYKAA": ["Nykaa", "FSN E-Commerce"],
}


class TickerResolver:
    """Resolves company names and aliases to NSE ticker symbols."""

    def __init__(self) -> None:
        """Initialize the ticker resolver with the alias dictionary.

        Builds a reverse lookup map from aliases to NSE tickers.
        """
        self._alias_to_ticker: dict[str, str] = {}
        for ticker, aliases in TICKER_ALIASES.items():
            for alias in aliases:
                self._alias_to_ticker[alias.lower()] = ticker
        logger.info(
            "TickerResolver initialized with %d aliases for %d tickers",
            len(self._alias_to_ticker),
            len(TICKER_ALIASES),
        )

    def resolve(self, entity: str) -> str | None:
        """Resolve a company name or alias to an NSE ticker symbol.

        Args:
            entity: Company name, abbreviation, or alias.

        Returns:
            NSE ticker symbol string, or None if no match found.
        """
        # Direct lookup (case-insensitive)
        ticker = self._alias_to_ticker.get(entity.lower())
        if ticker:
            return ticker

        # Partial match: check if entity contains any known alias
        entity_lower = entity.lower()
        for alias, ticker in self._alias_to_ticker.items():
            if alias in entity_lower or entity_lower in alias:
                return ticker

        return None

    def resolve_all(self, entities: list[str]) -> list[dict]:
        """Resolve a list of entity names to tickers.

        Args:
            entities: List of company names/aliases to resolve.

        Returns:
            List of dicts with keys: entity, ticker (or None).
        """
        results = []
        for entity in entities:
            ticker = self.resolve(entity)
            results.append({"entity": entity, "ticker": ticker})
        return results
