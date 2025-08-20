@echo off
python src\features.py --root data\klines --symbol BTCUSDT --interval 1h --out data\features\BTCUSDT_1h.parquet
pause
