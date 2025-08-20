"""
Storage helpers: Parquet partitioned writer.
"""
from __future__ import annotations
import os
import pathlib
from typing import Optional
import pandas as pd

def write_parquet_partitioned(df: pd.DataFrame, base_dir: str, symbol: str, interval: str) -> list[str]:
    """
    Write df grouped by calendar date (UTC) to partitioned Parquet files:
      {base_dir}/symbol={symbol}/interval={interval}/date=YYYY-MM-DD/{min_open_time_ms}-{max_open_time_ms}.parquet
    Returns a list of written file paths.
    """
    if df.empty:
        return []
    df = df.copy()
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    files = []
    base = pathlib.Path(base_dir) / f"symbol={symbol}" / f"interval={interval}"
    for date_str, g in df.groupby("date"):
        outdir = base / f"date={date_str}"
        outdir.mkdir(parents=True, exist_ok=True)
        start_ms = int(g["open_time"].min())
        end_ms = int(g["open_time"].max())
        outfile = outdir / f"{start_ms}-{end_ms}.parquet"
        # order by open_time and drop helper column
        g = g.sort_values("open_time").drop(columns=["date"])
        g.to_parquet(outfile, index=False)
        files.append(str(outfile))
    return files
