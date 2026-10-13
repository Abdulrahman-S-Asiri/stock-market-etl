"""T = Transform: clean the raw data and add useful columns."""

import pandas as pd

# Raw Yahoo column name -> clean column name we store.
COLUMN_MAP = {
    "Ticker": "ticker",
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
}

# Moving average window, in trading days (matches the ma_7 column name).
MA_WINDOW = 7


def transform_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a clean table with one row per (ticker, date)."""
    # Keep only the columns we need, with clean snake_case names.
    df = raw[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)

    # Store dates as 'YYYY-MM-DD' text (SQLite has no real date type).
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Drop rows with missing values, then duplicate (ticker, date) rows.
    df = df.dropna(subset=["open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")

    # Sort each ticker's days in order; the calculations below depend on it.
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Daily return: % change of close vs the previous trading day, per ticker.
    prev_close = df.groupby("ticker")["close"].shift(1)
    df["daily_return_pct"] = (df["close"] / prev_close - 1) * 100

    # Moving average: mean close of the last 7 trading days, per ticker.
    df["ma_7"] = df.groupby("ticker")["close"].transform(
        lambda s: s.rolling(MA_WINDOW).mean()
    )

    # Round money values to 2 decimals and make volume a whole number.
    decimal_cols = ["open", "high", "low", "close", "daily_return_pct", "ma_7"]
    df[decimal_cols] = df[decimal_cols].round(2)
    df["volume"] = df["volume"].astype("int64")

    return df
