@echo off
call .venv\Scripts\activate
python src\predict_future_lasso.py --features data/features/BTCUSDT_1h.parquet --model models/lasso_btcusdt_1h.joblib --scaler models/scaler_btcusdt_1h.joblib --steps 72 --out data/predictions/pred_future.csv
