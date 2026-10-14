"""Pipeline settings. Change values here instead of inside the code."""

from pathlib import Path

# Stocks to pull (Yahoo Finance symbols).
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]

# How much history to download. Examples: "5d", "1mo", "6mo", "1y", "5y".
PERIOD = "1y"

# Where the pipeline saves its files.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "stocks.db"

# Used by the Airflow DAG: one CSV per run day, before (raw) and after (clean) the transform.
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
