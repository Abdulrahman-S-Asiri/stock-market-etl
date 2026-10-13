# Stock Market ETL

A small, beginner-friendly data engineering project. It downloads daily stock prices,
cleans them, and loads them into a SQLite database you can query with SQL.

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

Settings (tickers, history length, DB path) live in `etl/config.py`.

## Project structure

```
├── etl/
│   ├── config.py        # settings
│   ├── extract.py       # E
│   ├── transform.py     # T
│   └── load.py          # L
├── tests/               # tests with fake data (no internet needed)
├── sql/example_queries.sql
├── main.py
└── requirements.txt
```

## How to run (Windows PowerShell)

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the tests
pytest

# 4. Run the pipeline
python main.py
```

The database is created at `data/stocks.db`.

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

## Note on the data source

`yfinance` is a free, unofficial wrapper around Yahoo Finance. It needs no API key, which
makes it great for learning, but it can rate-limit or change without notice. A production
pipeline would use an official, paid data API.
