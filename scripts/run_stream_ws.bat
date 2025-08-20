@echo off
python src\stream_ws.py --symbol BTCUSDT --stream kline --interval 1m --out data\stream\btc_kline_1m.jsonl
pause
