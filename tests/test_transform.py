"""Tests for the transform step. They use fake data, so no internet is needed."""

import math

import pandas as pd
from pandas.testing import assert_frame_equal

from etl.transform import transform_prices


def make_raw(ticker: str, closes: list[float], start: str = "2025-01-01") -> pd.DataFrame:
    """Build a fake table shaped like the extract step's output."""
    dates = pd.date_range(start, periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": [1000.0] * len(closes),
            "Dividends": 0.0,
            "Stock Splits": 0.0,
            "Ticker": ticker,
        }
    )


def test_keeps_only_clean_columns():
    result = transform_prices(make_raw("AAPL", [100, 101]))

    assert list(result.columns) == [
        "ticker", "date", "open", "high", "low", "close", "volume",
        "daily_return_pct", "ma_7",
    ]
    assert result["date"].tolist() == ["2025-01-01", "2025-01-02"]


def test_daily_return_is_calculated_per_ticker():
    raw = pd.concat([make_raw("AAPL", [100, 110]), make_raw("MSFT", [200, 180])])

    result = transform_prices(raw).set_index("ticker")

    # First day of each ticker has no previous day -> missing, not mixed with the other ticker.
    assert math.isnan(result.loc["AAPL", "daily_return_pct"].iloc[0])
    assert math.isnan(result.loc["MSFT", "daily_return_pct"].iloc[0])
    assert result.loc["AAPL", "daily_return_pct"].iloc[1] == 10.0
    assert result.loc["MSFT", "daily_return_pct"].iloc[1] == -10.0


def test_moving_average_needs_seven_days():
    result = transform_prices(make_raw("AAPL", [1, 2, 3, 4, 5, 6, 7, 8]))

    assert result["ma_7"].iloc[:6].isna().all()
    assert result["ma_7"].iloc[6] == 4.0  # mean of 1..7
    assert result["ma_7"].iloc[7] == 5.0  # mean of 2..8


def test_drops_missing_and_duplicate_rows():
    raw = make_raw("AAPL", [100, 101, 102])
    raw.loc[1, "Close"] = None                           # missing price
    raw = pd.concat([raw, raw.iloc[[2]]])                # duplicate day

    result = transform_prices(raw)

    assert result["date"].tolist() == ["2025-01-01", "2025-01-03"]


def test_same_result_after_csv_round_trip(tmp_path):
    # The Airflow DAG saves raw data as CSV between tasks; nothing may change on the way.
    raw = make_raw("AAPL", [100, 101, 102, 103, 104, 105, 106, 107])
    csv_path = tmp_path / "raw.csv"
    raw.to_csv(csv_path, index=False)

    assert_frame_equal(transform_prices(pd.read_csv(csv_path)), transform_prices(raw))
