"""AKShare data provider for A-share and Hong Kong stocks.

Maps AKShare DataFrame outputs to the same dict structure as the existing
Pydantic models (Price, FinancialMetrics, LineItem, InsiderTrade, CompanyNews).
"""

import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

from src.tools.market_detector import Market, detect_market

# Lazy import: AKShare is heavy and may not be installed
_akshare = None


def _get_akshare():
    """Lazy-load AKShare to avoid import overhead when not needed."""
    global _akshare
    if _akshare is None:
        import akshare as ak
        _akshare = ak
    return _akshare


# ── Helpers ──────────────────────────────────────────────────────────

def _to_akshare_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to YYYYMMDD for AKShare."""
    return date_str.replace("-", "")


def _safe_float(value) -> float | None:
    """Safely convert to float, returning None on failure."""
    if value is None:
        return None
    # Handle pandas Series (can happen with duplicate column names)
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else None
    if isinstance(value, str):
        # Strip % sign and convert
        value = value.replace("%", "").strip()
    try:
        v = float(value)
        return None if pd.isna(v) else v
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> int | None:
    """Safely convert to int, returning None on failure."""
    if value is None or pd.isna(value):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _safe_str(value) -> str | None:
    """Safely convert to string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value)


def _safe_date(value) -> str | None:
    """Convert various date formats to YYYY-MM-DD."""
    s = _safe_str(value)
    if not s:
        return None
    # Already in correct format
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    # YYYYMMDD
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    # Try pandas
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return s


def _get_price_col_map(market: Market) -> dict:
    """Get column name mapping from AKShare to Price model fields."""
    if market == Market.A_SHARE:
        return {
            "日期": "time",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
    elif market == Market.HK:
        return {
            "日期": "time",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
    return {}


# ── Price data ───────────────────────────────────────────────────────

def ak_get_prices(ticker: str, start_date: str, end_date: str) -> list[dict]:
    """Fetch OHLCV price data via AKShare. Returns list of Price-compatible dicts."""
    market = detect_market(ticker)
    try:
        ak = _get_akshare()
        if market == Market.A_SHARE:
            df = ak.stock_zh_a_hist(
                symbol=ticker,
                period="daily",
                start_date=_to_akshare_date(start_date),
                end_date=_to_akshare_date(end_date),
                adjust="qfq",
            )
        elif market == Market.HK:
            df = ak.stock_hk_hist(
                symbol=ticker,
                period="daily",
                start_date=_to_akshare_date(start_date),
                end_date=_to_akshare_date(end_date),
                adjust="qfq",
            )
        else:
            return []
    except Exception as e:
        logger.warning("AKShare price fetch failed for %s: %s", ticker, e)
        return []

    if df is None or df.empty:
        return []

    col_map = _get_price_col_map(market)
    df = df.rename(columns=col_map)

    results = []
    for _, row in df.iterrows():
        time_val = _safe_str(row.get("time"))
        if time_val:
            # Normalize date format
            try:
                time_val = pd.to_datetime(time_val).strftime("%Y-%m-%d")
            except Exception:
                pass

        results.append({
            "time": time_val,
            "open": _safe_float(row.get("open")),
            "close": _safe_float(row.get("close")),
            "high": _safe_float(row.get("high")),
            "low": _safe_float(row.get("low")),
            "volume": _safe_int(row.get("volume")),
        })

    return results


# ── Financial metrics ────────────────────────────────────────────────

# AKShare stock_financial_abstract_ths column name mapping
# to FinancialMetrics model fields
_FINANCIAL_METRICS_MAP = {
    # From stock_financial_abstract_ths - actual column names
    "净利润": "net_income_raw",
    "净利润同比增长率": "earnings_growth",
    "营业总收入": "revenue_raw",
    "营业总收入同比增长率": "revenue_growth",
    "基本每股收益": "earnings_per_share",
    "每股净资产": "book_value_per_share",
    "每股资本公积金": "capital_reserve_per_share",
    "每股未分配利润": "undistributed_profit_per_share",
    "每股经营现金流": "free_cash_flow_per_share",
    "净资产收益率": "return_on_equity",
    "净资产收益率-摊薄": "return_on_equity",
    "资产负债率": "debt_to_assets",
    "销售毛利率": "gross_margin",
    "销售净利率": "net_margin",
    "流动比率": "current_ratio",
    "速动比率": "quick_ratio",
    "保守速动比率": "quick_ratio",
    "产权比率": "debt_to_equity",
    "存货周转率": "inventory_turnover",
    "营业周期": "operating_cycle",
    "存货周转天数": "inventory_turnover",
    "应收账款周转天数": "days_sales_outstanding",
}


def ak_get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[dict]:
    """Fetch financial metrics via AKShare. Returns list of FinancialMetrics-compatible dicts."""
    market = detect_market(ticker)
    if market == Market.US:
        return []

    try:
        ak = _get_akshare()
        # Primary source: THS financial abstract (more reliable than stock_financial_analysis_indicator)
        df = ak.stock_financial_abstract_ths(symbol=ticker, indicator="按报告期")
    except Exception as e:
        logger.warning("AKShare financial abstract fetch failed for %s: %s", ticker, e)
        return []

    if df is None or df.empty:
        return []

    # Rename known columns and deduplicate
    df = df.rename(columns=_FINANCIAL_METRICS_MAP)
    # Remove duplicate columns, keeping the last occurrence (most recent data)
    df = df.loc[:, ~df.columns.duplicated(keep="last")]

    results = []
    for _, row in df.tail(limit).iterrows():
        report_period = end_date
        for col in ["报告期", "报告日期", "日期"]:
            if col in df.columns:
                rp = _safe_str(row.get(col))
                if rp:
                    report_period = rp
                break

        metric = {
            "ticker": ticker,
            "report_period": report_period,
            "period": period,
            "currency": "CNY" if market == Market.A_SHARE else "HKD",
            "market_cap": None,
            "enterprise_value": None,
            "price_to_earnings_ratio": None,
            "price_to_book_ratio": None,
            "price_to_sales_ratio": None,
            "enterprise_value_to_ebitda_ratio": None,
            "enterprise_value_to_revenue_ratio": None,
            "free_cash_flow_yield": None,
            "peg_ratio": None,
            "gross_margin": _safe_float(row.get("gross_margin")),
            "operating_margin": None,
            "net_margin": _safe_float(row.get("net_margin")),
            "return_on_equity": _safe_float(row.get("return_on_equity")),
            "return_on_assets": None,
            "return_on_invested_capital": None,
            "asset_turnover": None,
            "inventory_turnover": None,
            "receivables_turnover": None,
            "days_sales_outstanding": None,
            "operating_cycle": None,
            "working_capital_turnover": None,
            "current_ratio": None,
            "quick_ratio": None,
            "cash_ratio": None,
            "operating_cash_flow_ratio": None,
            "debt_to_equity": None,
            "debt_to_assets": _safe_float(row.get("debt_to_assets")),
            "interest_coverage": None,
            "revenue_growth": _safe_float(row.get("revenue_growth")),
            "earnings_growth": _safe_float(row.get("earnings_growth")),
            "book_value_growth": None,
            "earnings_per_share_growth": None,
            "free_cash_flow_growth": None,
            "operating_income_growth": None,
            "ebitda_growth": None,
            "payout_ratio": None,
            "earnings_per_share": _safe_float(row.get("earnings_per_share")),
            "book_value_per_share": _safe_float(row.get("book_value_per_share")),
            "free_cash_flow_per_share": None,
        }
        results.append(metric)

    return results


# ── Line items ───────────────────────────────────────────────────────

def ak_search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[dict]:
    """Search financial line items via AKShare. Returns list of LineItem-compatible dicts.

    Since AKShare doesn't have a direct line-items search API, we derive from
    financial indicators and available financial statement data.
    """
    market = detect_market(ticker)
    if market == Market.US:
        return []

    # Try to get detailed financial statement data
    try:
        ak = _get_akshare()
        # Use THS financial abstract as source for line item derivation
        df = ak.stock_financial_abstract_ths(symbol=ticker, indicator="按报告期")
    except Exception as e:
        logger.warning("AKShare line items fetch failed for %s: %s", ticker, e)
        return []

    if df is None or df.empty:
        return []

    # Map available data to LineItem format
    results = []
    for _, row in df.head(limit).iterrows():
        report_period = end_date
        for col in ["报告日期", "日期", "REPORT_DATE", "报告期"]:
            if col in df.columns:
                rp = _safe_str(row.get(col))
                if rp:
                    report_period = rp
                break

        line_item = {
            "ticker": ticker,
            "report_period": report_period,
            "period": period,
            "currency": "CNY" if market == Market.A_SHARE else "HKD",
        }

        # Map any additional fields that could correspond to line items
        # These are approximations since AKShare's indicator API provides ratios, not raw values
        if "net_income" in line_items or "净利润" in line_items:
            line_item["net_income"] = None
        if "revenue" in line_items or "营业收入" in line_items:
            line_item["revenue"] = None
        if "free_cash_flow" in line_items:
            line_item["free_cash_flow"] = None
        if "total_debt" in line_items:
            line_item["total_debt"] = None
        if "cash_and_equivalents" in line_items:
            line_item["cash_and_equivalents"] = None
        if "working_capital" in line_items:
            line_item["working_capital"] = None

        results.append(line_item)

    return results


# ── Insider trades ───────────────────────────────────────────────────

def ak_get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    """Fetch insider/holder change data via AKShare. Returns list of InsiderTrade-compatible dicts."""
    market = detect_market(ticker)
    if market == Market.US:
        return []

    try:
        ak = _get_akshare()
        # Use EastMoney holder changes API
        df = ak.stock_changes_holder_em(symbol=ticker)
    except Exception as e:
        logger.warning("AKShare insider trades fetch failed for %s: %s", ticker, e)
        return []

    if df is None or df.empty:
        return []

    results = []
    for _, row in df.head(limit).iterrows():
        # Map holder changes to InsiderTrade model
        # Column names vary: 股东名称, 持股变动数, 变动日期, etc.
        trade = {
            "ticker": ticker,
            "issuer": None,
            "name": _safe_str(row.get("股东名称")),
            "title": _safe_str(row.get("职务")),
            "is_board_director": None,
            "transaction_date": _safe_date(row.get("变动日期")),
            "transaction_shares": _safe_float(row.get("持股变动数")),
            "transaction_price_per_share": None,
            "transaction_value": None,
            "shares_owned_before_transaction": _safe_float(row.get("变动前持股数") or row.get("期初持股数")),
            "shares_owned_after_transaction": _safe_float(row.get("变动后持股数") or row.get("期末持股数")),
            "security_title": None,
            "filing_date": _safe_date(row.get("公告日期")) or end_date,
        }
        results.append(trade)

    return results


# ── Company news ─────────────────────────────────────────────────────

def ak_get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    """Fetch company news via AKShare. Returns list of CompanyNews-compatible dicts."""
    market = detect_market(ticker)
    if market == Market.US:
        return []

    try:
        ak = _get_akshare()
        df = ak.stock_news_em(symbol=ticker)
    except Exception as e:
        logger.warning("AKShare news fetch failed for %s: %s", ticker, e)
        return []

    if df is None or df.empty:
        return []

    results = []
    for _, row in df.head(limit).iterrows():
        news_date = _safe_date(row.get("发布时间"))
        if news_date and start_date and news_date < start_date:
            continue

        news = {
            "ticker": ticker,
            "title": _safe_str(row.get("新闻标题", "")) or "",
            "author": _safe_str(row.get("作者")),
            "source": "东方财富",
            "date": news_date or end_date,
            "url": _safe_str(row.get("新闻链接", "")) or "",
            "sentiment": None,  # LLM agents will analyze sentiment
        }
        results.append(news)

    return results


# ── Market cap ───────────────────────────────────────────────────────

def ak_get_market_cap(ticker: str, end_date: str) -> float | None:
    """Fetch market cap via AKShare. Returns market cap in local currency."""
    market = detect_market(ticker)
    if market == Market.US:
        return None

    try:
        ak = _get_akshare()
        # Use individual stock info endpoint which includes market cap
        df = ak.stock_individual_info_em(symbol=ticker)
    except Exception as e:
        logger.warning("AKShare market cap fetch failed for %s: %s", ticker, e)
        return None

    if df is None or df.empty:
        return None

    # Try to find market cap column
    for col in ["总市值", "总市值(元)", "market_cap", "市值"]:
        if col in df.columns:
            val = df[col].iloc[0]
            return _safe_float(val)

    # Some versions return a DataFrame with key-value pairs
    for _, row in df.iterrows():
        item_name = str(row.iloc[0]) if len(row) > 0 else ""
        if "总市值" in item_name or "市值" in item_name:
            val = row.iloc[1] if len(row) > 1 else None
            return _safe_float(val)

    return None


# ── Index/Benchmark data ────────────────────────────────────────────

def ak_get_index_prices(
    index_code: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Fetch index prices for benchmark calculations.

    index_code: "000300" for CSI 300, "HSI" for Hang Seng
    """
    try:
        ak = _get_akshare()
        # A-share indices
        df = ak.index_zh_a_hist(
            symbol=index_code,
            period="daily",
            start_date=_to_akshare_date(start_date),
            end_date=_to_akshare_date(end_date),
        )
    except Exception as e:
        logger.warning("AKShare index fetch failed for %s: %s", index_code, e)
        return []

    if df is None or df.empty:
        return []

    # Index column names: 日期, 开盘, 收盘, 最高, 最低, 成交量, etc.
    col_map = {"日期": "time", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "volume"}
    df = df.rename(columns=col_map)

    results = []
    for _, row in df.iterrows():
        time_val = _safe_str(row.get("time"))
        if time_val:
            try:
                time_val = pd.to_datetime(time_val).strftime("%Y-%m-%d")
            except Exception:
                pass
        results.append({
            "time": time_val,
            "open": _safe_float(row.get("open")),
            "close": _safe_float(row.get("close")),
            "high": _safe_float(row.get("high")),
            "low": _safe_float(row.get("low")),
            "volume": _safe_int(row.get("volume")),
        })

    return results
