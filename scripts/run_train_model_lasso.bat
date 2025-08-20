@echo off
python src\train_model_lasso.py --features data\features\BTCUSDT_1h.parquet --model-out models\lasso_btcusdt_1h.joblib --scaler-out models\scaler_btcusdt_1h.joblib --alpha 0.001
pause