"""
Build ML features from OHLCV Parquet partitions.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.clip(lower=0)).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss.replace(0, np.nan))
    return 100 - (100 / (1 + rs))

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def load_parquet_root(root: str, symbol: str, interval: str) -> pd.DataFrame:
    base = Path(root) / f"symbol={symbol}" / f"interval={interval}"
    parts = list(base.rglob("*.parquet"))
    if not parts:
        raise FileNotFoundError(f"No parquet files under {base}")
    dfs = [pd.read_parquet(p) for p in sorted(parts)]
    df = pd.concat(dfs, ignore_index=True)
    return df

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("open_time").reset_index(drop=True)
    # core time index
    df["open_ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    # returns
    df["ret_1"] = df["close"].pct_change()
    df["ret_5"] = df["close"].pct_change(5)
    df["ret_10"] = df["close"].pct_change(10)
    # rolling stats
    for w in [7, 20, 50]:
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
        df[f"ema_{w}"] = df["close"].ewm(span=w, adjust=False).mean()
        df[f"std_{w}"] = df["close"].rolling(w).std()
    # RSI & MACD
    df["rsi_14"] = rsi(df["close"], 14)
    macd_line, signal_line, hist = macd(df["close"])
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = hist
    # lags
    for l in [1,2,3,5,10]:
        df[f"close_lag_{l}"] = df["close"].shift(l)
        df[f"vol_lag_{l}"] = df["volume"].shift(l)
    # target: next close (regression) & next return
    df["y_next_close"] = df["close"].shift(-1)
    df["y_next_ret"] = df["close"].pct_change().shift(-1)
    # drop early NaNs
    df = df.dropna().reset_index(drop=True)
    return df

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Parquet root created by fetch_klines.py")
    ap.add_argument("--symbol", required=True, help="e.g., BTCUSDT")
    ap.add_argument("--interval", required=True, help="e.g., 1h")
    ap.add_argument("--out", required=True, help="Output Parquet file for features")
    return ap.parse_args()

def main():
    args = parse_args()
    df = load_parquet_root(args.root, args.symbol.upper(), args.interval)
    feat = build_features(df)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    feat.to_parquet(args.out, index=False)
    print(f"Wrote features: {args.out} ({len(feat)} rows)")

if __name__ == "__main__":
    main()
