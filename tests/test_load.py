"""Tests for the load step, using a temporary database file."""

import sqlite3

import pandas as pd

from etl.load import load_prices


def make_clean(close: float, ma_7: float | None) -> pd.DataFrame:
    """Build a one-row table shaped like the transform step's output."""
    return pd.DataFrame(
        [{
            "ticker": "AAPL", "date": "2025-01-10",
            "open": close, "high": close, "low": close, "close": close,
            "volume": 1000, "daily_return_pct": 1.5, "ma_7": ma_7,
        }]
    )


def read_rows(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT ticker, date, close, ma_7 FROM daily_prices").fetchall()
    finally:
        conn.close()


def test_running_twice_does_not_duplicate_rows(tmp_path):
    db_path = tmp_path / "test.db"

    load_prices(make_clean(100.0, 99.0), db_path)
    load_prices(make_clean(100.0, 99.0), db_path)

    assert read_rows(db_path) == [("AAPL", "2025-01-10", 100.0, 99.0)]


def test_rerun_updates_prices_but_keeps_old_calculated_value(tmp_path):
    db_path = tmp_path / "test.db"

    load_prices(make_clean(100.0, 99.0), db_path)
    load_prices(make_clean(105.0, None), db_path)  # new run: price changed, no ma_7

    assert read_rows(db_path) == [("AAPL", "2025-01-10", 105.0, 99.0)]
