# Stock Market ETL

A small, beginner-friendly data engineering project. It downloads daily stock prices,
cleans them, and loads them into a SQLite database you can query with SQL.
Run it once with `python main.py`, or every weekday with Apache Airflow.

```
Yahoo Finance  ──►  Extract  ──►  Transform  ──►  Load  ──►  data/stocks.db
                   (raw rows)     (clean +        (upsert into
                                   new columns)    SQLite)
```

## What each step does

| Step | File | What happens |
|------|------|--------------|
| **Extract** | `etl/extract.py` | Downloads 1 year of daily prices for each ticker with `yfinance` and stacks them into one table. |
| **Transform** | `etl/transform.py` | Renames columns, removes missing and duplicate rows, then adds `daily_return_pct` and `ma_7` (7-day moving average). |
| **Load** | `etl/load.py` | Creates the `daily_prices` table and **upserts** rows: new days are inserted, existing days are updated. |
| **Run** | `main.py` | Runs Extract → Transform → Load and logs each step. |
| **Schedule** | `dags/stock_etl_dag.py` | Airflow DAG that runs the same steps as three tasks, every weekday. |

Settings (tickers, history length, DB path) live in `etl/config.py`.

## Project structure

```
├── etl/
│   ├── config.py        # settings
│   ├── extract.py       # E
│   ├── transform.py     # T
│   └── load.py          # L
├── dags/
│   └── stock_etl_dag.py # Airflow DAG
├── tests/               # tests with fake data (no internet needed)
├── sql/example_queries.sql
├── docs/explained-ar.html  # step-by-step guide in Arabic
├── main.py
├── Dockerfile           # Airflow image + project packages
├── docker-compose.yml   # runs Airflow locally
└── requirements.txt
```

## How to run (Windows PowerShell)

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the tests (the Airflow DAG tests are skipped here; they run in Docker)
pytest

# 4. Run the pipeline
python main.py
```

The database is created at `data/stocks.db`.

## Run with Airflow (Docker)

Airflow runs the same three steps as **separate tasks**, every weekday at 22:00 UTC
(1:00 AM Riyadh), after the US market closes. Each task saves a CSV file and passes
only the file path to the next task:

```
extract  ──►  transform  ──►  load
   │              │             │
data/raw/      data/clean/    data/stocks.db
<day>.csv      <day>.csv
```

This setup runs all of Airflow in one container (`airflow standalone`). It is meant for
learning, not production. Requirement: Docker Desktop is running.

```powershell
# 1. Build the image and start Airflow (the first build downloads ~660 MB)
docker compose up -d --build

# 2. Open http://localhost:8080 (no login; reachable only from this PC).
#    Unpause the "stock_etl" DAG (new DAGs start paused), then press Trigger.

# 3. Or run the whole DAG once from the terminal
docker compose exec airflow airflow dags test stock_etl

# 4. Run all tests inside the container (including the DAG tests)
docker compose exec -w /opt/airflow/project airflow python -m pytest -q -p no:cacheprovider

# 5. Stop and start again (keeps Airflow's run history)
docker compose stop
docker compose start
```

`docker compose down` removes the container and Airflow's run history, but not your data
in `data/`. Don't run `python main.py` while the DAG's `load` task is running: both write
the same SQLite file.

## Query the data

The queries in `sql/example_queries.sql` can be run with any SQLite tool
(for example the *SQLite Viewer* extension in VS Code, or *DB Browser for SQLite*).

Or straight from Python:

```powershell
python -c "import sqlite3; c = sqlite3.connect('data/stocks.db'); print(c.execute('SELECT ticker, COUNT(*) FROM daily_prices GROUP BY ticker').fetchall())"
```

## Table: `daily_prices`

| Column | Type | Notes |
|--------|------|-------|
| `ticker` | TEXT | e.g. `AAPL` |
| `date` | TEXT | `YYYY-MM-DD` |
| `open`, `high`, `low`, `close` | REAL | Adjusted prices, rounded to 2 decimals |
| `volume` | INTEGER | Shares traded |
| `daily_return_pct` | REAL | % change vs previous day. `NULL` on each ticker's first day |
| `ma_7` | REAL | Average close of the last 7 trading days. `NULL` for the first 6 days |

Primary key: `(ticker, date)` — one row per stock per day.

## Key data engineering ideas in this project

- **Separation of steps** — each of E, T and L is its own file and can be tested alone.
- **Idempotency** — running the pipeline twice gives the same result. The primary key
  plus `INSERT ... ON CONFLICT DO UPDATE` (an *upsert*) prevents duplicate rows.
- **Data cleaning** — missing values and duplicates are removed before loading.
- **Window calculations** — returns and moving averages are calculated *per ticker*
  (`groupby` in pandas, `PARTITION BY` in SQL).
- **Tests on transform logic** — fake input, known expected output.
- **Orchestration** — Airflow runs the steps on a schedule, in order, with retries and logs.
- **Raw and clean layers** — the DAG keeps a CSV copy of the data before and after
  cleaning, so any step can be re-run or inspected on its own.

## Note on the data source

`yfinance` is a free, unofficial wrapper around Yahoo Finance. It needs no API key, which
makes it great for learning, but it can rate-limit or change without notice. A production
pipeline would use an official, paid data API.
