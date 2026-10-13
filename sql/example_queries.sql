-- Practice queries for data/stocks.db (table: daily_prices).

-- 1. How many days of data do we have per stock?
SELECT ticker, COUNT(*) AS days, MIN(date) AS first_day, MAX(date) AS last_day
FROM daily_prices
GROUP BY ticker
ORDER BY ticker;

-- 2. Latest close price per stock.
SELECT ticker, date, close
FROM daily_prices
WHERE date = (SELECT MAX(date) FROM daily_prices)
ORDER BY close DESC;

-- 3. Best and worst single day per stock.
SELECT ticker,
       MAX(daily_return_pct) AS best_day_pct,
       MIN(daily_return_pct) AS worst_day_pct
FROM daily_prices
GROUP BY ticker
ORDER BY best_day_pct DESC;

-- 4. Average close per stock per month.
SELECT ticker,
       substr(date, 1, 7)   AS month,  -- 'YYYY-MM'
       ROUND(AVG(close), 2) AS avg_close
FROM daily_prices
GROUP BY ticker, month
ORDER BY ticker, month;

-- 5. Days where the close crossed above its 7-day moving average.
--    LAG() looks at the previous row of the same ticker.
WITH with_prev AS (
    SELECT ticker, date, close, ma_7,
           LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS prev_close,
           LAG(ma_7)  OVER (PARTITION BY ticker ORDER BY date) AS prev_ma_7
    FROM daily_prices
)
SELECT ticker, date, close, ma_7
FROM with_prev
WHERE prev_close <= prev_ma_7
  AND close > ma_7
ORDER BY date DESC
LIMIT 20;
