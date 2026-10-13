"""Pipeline settings. Change values here instead of inside the code."""

from pathlib import Path

# Stocks to pull (Yahoo Finance symbols).
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]

# How much history to download. Examples: "5d", "1mo", "6mo", "1y", "5y".
PERIOD = "1y"

# Where the SQLite database file is saved.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "stocks.db"
