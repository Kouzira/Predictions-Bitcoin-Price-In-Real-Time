"""
Binance REST client and OHLCV downloader.
Docs: https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Iterator, Optional
import requests
import pandas as pd

from utils import to_millis, from_millis, sleep_backoff

BASE_URL = "https://api.binance.com"

def _request(session: requests.Session, path: str, params: Dict, max_retries: int = 5) -> requests.Response:
    url = BASE_URL + path
    attempt = 0
    while True:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code == 418:
            logging.warning("Hit rate limit (%s). Retrying...", resp.status_code)
            attempt += 1
            sleep_backoff(attempt, base=1.0, cap=60.0)
            continue
        logging.error("HTTP %s: %s", resp.status_code, resp.text[:300])
        attempt += 1
        if attempt > max_retries:
            resp.raise_for_status()
        time.sleep(1.0)

def klines_generator(
    session: requests.Session,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    limit: int = 1000,
) -> Iterator[pd.DataFrame]:
    """
    Yield DataFrames of klines between start_ms and end_ms inclusive.
    Binance returns up to 1000 rows per call.
    """
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
        "startTime": start_ms,
        "endTime": end_ms,
    }
    last_open = None
    while True:
        resp = _request(session, "/api/v3/klines", params)
        data = resp.json()
        if not data:
            break
        cols = [
            "open_time","open","high","low","close","volume",
            "close_time","quote_asset_volume","number_of_trades",
            "taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore",
        ]
        df = pd.DataFrame(data, columns=cols)
        # types
        num_cols = ["open","high","low","close","volume","quote_asset_volume",
                    "taker_buy_base_asset_volume","taker_buy_quote_asset_volume"]
        for c in num_cols:
            df[c] = df[c].astype(float)
        df["number_of_trades"] = df["number_of_trades"].astype(int)
        # If Binance returns same first open_time, advance to avoid infinite loop
        if last_open is not None and int(df.iloc[0]["open_time"]) == last_open:
            break
        last_open = int(df.iloc[-1]["open_time"])
        yield df

        # next window: start at last close_time + 1ms
        next_start = int(df.iloc[-1]["close_time"]) + 1
        if next_start > end_ms:
            break
        params["startTime"] = next_start

def download_klines(symbol: str, interval: str, start: str, end: str) -> pd.DataFrame:
    import requests
    s = requests.Session()
    start_ms = to_millis(start)
    end_ms = to_millis(end)
    frames = []
    for chunk in klines_generator(s, symbol, interval, start_ms, end_ms):
        frames.append(chunk)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    # drop 'ignore'
    df = df.drop(columns=["ignore"])
    return df
