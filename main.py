"""Run the full pipeline: Extract -> Transform -> Load."""

import logging

from etl import config
from etl.extract import extract_prices
from etl.load import load_prices
from etl.transform import transform_prices

logger = logging.getLogger("pipeline")


def main() -> None:
    # Print timestamped progress messages to the terminal.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logger.info("Extract: downloading %s (%s)", ", ".join(config.TICKERS), config.PERIOD)
    raw = extract_prices(config.TICKERS, config.PERIOD)

    logger.info("Transform: cleaning %d raw rows", len(raw))
    clean = transform_prices(raw)

    logger.info("Load: writing %d rows to %s", len(clean), config.DB_PATH)
    count = load_prices(clean, config.DB_PATH)

    logger.info("Done: %d rows loaded", count)


if __name__ == "__main__":
    main()
