@echo off
python src\fetch_klines.py --symbol BTCUSDT --interval 1h --start 2020-01-01 --end 2024-12-31 --out data\klines
pause
