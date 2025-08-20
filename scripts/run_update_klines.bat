@echo off
python src\update_fetch_klines.py --symbol BTCUSDT --interval 1h --out data\klines
pause
