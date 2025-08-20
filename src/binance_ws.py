"""
Binance WebSocket helpers.
Docs: https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams
"""
from __future__ import annotations

import asyncio
import json
import logging
import websockets

WS_URL = "wss://stream.binance.com:9443/ws"

async def stream(symbol: str, stream_type: str, interval: str | None = None):
    symbol_l = symbol.lower()
    if stream_type == "kline":
        if not interval:
            raise ValueError("interval required for kline stream")
        stream_path = f"{symbol_l}@kline_{interval}"
    elif stream_type == "trade":
        stream_path = f"{symbol_l}@trade"
    else:
        raise ValueError("stream_type must be 'kline' or 'trade'")
    url = f"{WS_URL}/{stream_path}"
    logging.info("Connecting %s", url)
    async for ws in websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=10_000_000):
        try:
            async for msg in ws:
                yield json.loads(msg)
        except Exception as e:
            logging.warning("WebSocket error: %s. Reconnecting...", e)
            continue  # reconnect

