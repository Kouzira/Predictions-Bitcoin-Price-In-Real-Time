@echo off
call .venv\Scripts\activate
python src\predict_lasso.py --features data\features\BTCUSDT_1h.parquet --model models\lasso_btcusdt_1h.joblib --scaler models\scaler_btcusdt_1h.joblib --out data\predictions\lasso_predictions.csv --n-last 5