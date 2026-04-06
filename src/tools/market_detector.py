"""Market detection from ticker symbols."""

from enum import Enum


class Market(Enum):
    US = "us"
    A_SHARE = "a_share"
    HK = "hk"


def detect_market(ticker: str) -> Market:
    """Detect market from ticker symbol.

    Rules:
    - A-share: 6 digits, starts with 0/3/6/8 (Shanghai=6, Shenzhen=0/3, Beijing=8)
    - HK: 5 digits (e.g., "00700", "09988")
    - US: contains letters (e.g., "AAPL", "SPY")
    """
    stripped = ticker.strip()

    if stripped.isdigit():
        if len(stripped) == 6 and stripped[0] in ("0", "3", "6", "8", "4"):
            return Market.A_SHARE
        if len(stripped) == 5:
            return Market.HK
        if len(stripped) == 6 and stripped.startswith(("00", "30", "60", "68", "83", "87", "43")):
            return Market.A_SHARE

    # Contains letters = US (or other international, default to US)
    return Market.US
