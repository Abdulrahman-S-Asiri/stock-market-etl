"""Airflow DAG: run the stock ETL every weekday after the US market closes."""

from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

from etl import config


@dag(
    schedule="0 22 * * 1-5",  # 22:00 UTC, Mon-Fri = 1:00 AM Riyadh, after the US market closes
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,  # don't run all the past days at once
    max_active_runs=1,  # one run at a time: runs share the same CSV files and SQLite database
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},  # Yahoo can rate-limit
    tags=["stocks", "etl"],
)
def stock_etl():
    # Heavy imports (pandas, yfinance) live inside the tasks: Airflow re-reads this file often.

    @task
    def extract() -> str:
        """Download raw prices and save them as data/raw/<today>.csv."""
        from etl.extract import extract_prices

        raw = extract_prices(config.TICKERS, config.PERIOD)
        path = config.RAW_DIR / f"{pendulum.now('UTC').to_date_string()}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(path, index=False)

        # Pass the file path to the next task (small), not the data itself (big).
        return str(path)

    @task
    def transform(raw_path: str) -> str:
        """Clean the raw CSV and save it as data/clean/<same name>.csv."""
        import pandas as pd

        from etl.transform import transform_prices

        clean = transform_prices(pd.read_csv(raw_path))
        path = config.CLEAN_DIR / Path(raw_path).name
        path.parent.mkdir(parents=True, exist_ok=True)
        clean.to_csv(path, index=False)
        return str(path)

    @task
    def load(clean_path: str) -> int:
        """Upsert the clean CSV into SQLite. Returns the number of rows sent."""
        import pandas as pd

        from etl.load import load_prices

        return load_prices(pd.read_csv(clean_path), config.DB_PATH)

    # Calling the tasks like functions sets the order: extract -> transform -> load.
    load(transform(extract()))


stock_etl()
