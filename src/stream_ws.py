"""
CLI: stream Binance WebSocket (kline/trade) to JSONL.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from binance_ws import stream
from utils import setup_logging

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True, help="BTCUSDT, ETHUSDT, ...")
    ap.add_argument("--stream", required=True, choices=["kline","trade"])
    ap.add_argument("--interval", default=None, help="Required for kline (1m, 5m, 1h, 1d)")
    ap.add_argument("--out", required=True, help="Output JSONL file path")
    return ap.parse_args()

async def run(args):
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    count = 0
    async for evt in stream(args.symbol, args.stream, args.interval):
        # Enrich with ingest_ts
        evt["_ingest_ts"] = datetime.now(tz=timezone.utc).isoformat()
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
        count += 1
        if count % 50 == 0:
            logging.info("Wrote %d events to %s", count, args.out)

def main():
    setup_logging()
    args = parse_args()
    if args.stream == "kline" and not args.interval:
        raise SystemExit("--interval is required for kline stream")
    asyncio.run(run(args))

if __name__ == "__main__":
    main()
