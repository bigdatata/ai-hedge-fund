from __future__ import annotations

import pandas as pd

from src.tools.api import get_price_data
from src.tools.market_detector import detect_market, Market


# Benchmark index mapping by market
BENCHMARK_MAP = {
    Market.US: "SPY",          # S&P 500 ETF
    Market.A_SHARE: "000300",   # CSI 300 (沪深300)
    Market.HK: "HSI",           # Hang Seng Index (恒生指数)
}


def get_benchmark_for_tickers(tickers: list[str]) -> str:
    """Determine appropriate benchmark ticker based on majority of tickers.

    Returns the benchmark index code for the dominant market.
    """
    if not tickers:
        return "SPY"

    market_counts: dict[Market, int] = {Market.US: 0, Market.A_SHARE: 0, Market.HK: 0}
    for t in tickers:
        m = detect_market(t)
        market_counts[m] = market_counts.get(m, 0) + 1

    # Use the market with the most tickers
    dominant_market = max(market_counts, key=market_counts.get)
    return BENCHMARK_MAP.get(dominant_market, "SPY")


class BenchmarkCalculator:
    def get_return_pct(self, ticker: str, start_date: str, end_date: str) -> float | None:
        """Compute simple buy-and-hold return % for ticker from start_date to end_date.

        Return is (last_close / first_close - 1) * 100, or None if unavailable.
        """
        try:
            df = get_price_data(ticker, start_date, end_date)
            if df.empty:
                return None
            first_close = df.iloc[0]["close"]
            last_close = df.iloc[-1]["close"]
            if first_close is None or pd.isna(first_close):
                return None
            if last_close is None or pd.isna(last_close):
                # Try last valid close
                last_valid = df["close"].dropna()
                if last_valid.empty:
                    return None
                last_close = float(last_valid.iloc[-1])
            return (float(last_close) / float(first_close) - 1.0) * 100.0
        except Exception:
            return None
