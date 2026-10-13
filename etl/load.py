"""L = Load: write the clean data into a SQLite database."""

import sqlite3
from pathlib import Path

import pandas as pd

# The primary key (ticker, date) means one row per stock per day.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker            TEXT    NOT NULL,
    date              TEXT    NOT NULL,  -- 'YYYY-MM-DD'
    open              REAL    NOT NULL,
    high              REAL    NOT NULL,
    low               REAL    NOT NULL,
    close             REAL    NOT NULL,
    volume            INTEGER NOT NULL,
    daily_return_pct  REAL,              -- NULL on a ticker's first day
    ma_7              REAL,              -- NULL until 7 days of history exist
    PRIMARY KEY (ticker, date)
);
"""

# Upsert: insert new rows; if (ticker, date) already exists, update it instead.
# COALESCE keeps an old calculated value when the new run has no history for it
# (the oldest days of each run have no previous day / no 7-day window).
UPSERT_SQL = """
INSERT INTO daily_prices
    (ticker, date, open, high, low, close, volume, daily_return_pct, ma_7)
VALUES
    (:ticker, :date, :open, :high, :low, :close, :volume, :daily_return_pct, :ma_7)
ON CONFLICT (ticker, date) DO UPDATE SET
    open             = excluded.open,
    high             = excluded.high,
    low              = excluded.low,
    close            = excluded.close,
    volume           = excluded.volume,
    daily_return_pct = COALESCE(excluded.daily_return_pct, daily_prices.daily_return_pct),
    ma_7             = COALESCE(excluded.ma_7, daily_prices.ma_7);
"""


def load_prices(df: pd.DataFrame, db_path: Path) -> int:
    """Upsert rows into the daily_prices table. Returns the number of rows sent."""
    # Create the data/ folder on the first run.
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Turn pandas NaN into Python None so SQLite stores a real NULL.
    rows = df.astype(object).where(df.notna(), None).to_dict("records")

    conn = sqlite3.connect(db_path)
    try:
        # "with conn" commits if everything works, or rolls back on any error.
        with conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.executemany(UPSERT_SQL, rows)
    finally:
        conn.close()

    return len(rows)
