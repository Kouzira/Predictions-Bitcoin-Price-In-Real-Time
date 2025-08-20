@echo off
python src\train_model.py --features data\features\BTCUSDT_1h.parquet --model-out models\rf_btcusdt_1h.joblib
pause
