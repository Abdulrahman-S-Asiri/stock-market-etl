"""E = Extract: download raw daily prices from Yahoo Finance."""

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def extract_prices(tickers: list[str], period: str) -> pd.DataFrame:
    """Download daily prices for each ticker and stack them into one table."""
    frames = []
    for ticker in tickers:
        # Ask Yahoo for this ticker's daily history (one row per trading day).
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)

        # Skip a ticker that returns nothing (bad symbol, network issue, rate limit).
        if df.empty:
            logger.warning("No data returned for %s, skipping", ticker)
            continue

        # Yahoo dates carry the exchange timezone; drop it so all tickers match.
        df.index = df.index.tz_localize(None)

        # Tag each row with its ticker and turn the Date index into a normal column.
        df["Ticker"] = ticker
        frames.append(df.reset_index())
        logger.info("Extracted %d rows for %s", len(df), ticker)

    if not frames:
        raise RuntimeError("No data extracted for any ticker.")

    # Stack all tickers into one long table.
    return pd.concat(frames, ignore_index=True)
