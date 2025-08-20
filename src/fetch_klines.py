"""
CLI to download OHLCV klines and write partitioned Parquet.
"""
from __future__ import annotations
import argparse
import logging
import pandas as pd

from binance_rest import download_klines
from storage import write_parquet_partitioned
from utils import setup_logging

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True, help="e.g., BTCUSDT")
    ap.add_argument("--interval", required=True, help="e.g., 1m, 5m, 1h, 1d")
    ap.add_argument("--start", required=True, help="ISO date (UTC) e.g., 2023-01-01")
    ap.add_argument("--end", required=True, help="ISO date (UTC) e.g., 2023-12-31")
    ap.add_argument("--out", required=True, help="Output base directory for Parquet")
    return ap.parse_args()

def main():
    setup_logging()
    args = parse_args()
    logging.info("Downloading %s %s from %s to %s", args.symbol, args.interval, args.start, args.end)
    df = download_klines(args.symbol, args.interval, args.start, args.end)
    if df.empty:
        logging.warning("No data returned.")
        return
    files = write_parquet_partitioned(df, args.out, args.symbol.upper(), args.interval)
    logging.info("Wrote %d files.", len(files))

if __name__ == "__main__":
    main()
