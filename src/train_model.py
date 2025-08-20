"""
Train/evaluate a simple regression model for next-close prediction.
"""
from __future__ import annotations

import argparse
import numpy as np
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, root_mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="Parquet with engineered features")
    ap.add_argument("--model-out", default=None, help="Path to save fitted model (joblib)")
    ap.add_argument("--predict", action="store_true", help="Predict instead of training")
    ap.add_argument("--model-in", default=None, help="Load model for prediction")
    ap.add_argument("--pred-out", default=None, help="CSV to save predictions")
    return ap.parse_args()

def load_features(path: str):
    df = pd.read_parquet(path)
    y = df["y_next_close"]
    X = df.drop(columns=["y_next_close", "y_next_ret", "open_time", "close_time", "open_ts"])
    return X, y, df

def train_eval(X, y):
    tscv = TimeSeriesSplit(n_splits=5)
    maes, rmses = [], []
    for tr_idx, val_idx in tscv.split(X):
        Xtr, Xv = X.iloc[tr_idx], X.iloc[val_idx]
        ytr, yv = y.iloc[tr_idx], y.iloc[val_idx]
        model = RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            n_jobs=-1,
            random_state=42,
        )
        model.fit(Xtr, ytr)
        pred = model.predict(Xv)
        maes.append(mean_absolute_error(yv, pred))
        rmses.append(root_mean_squared_error(yv, pred))
    return float(sum(maes)/len(maes)), float(sum(rmses)/len(rmses))

def main():
    args = parse_args()
    X, y, df = load_features(args.features)
    if not args.predict:
        mae, rmse = train_eval(X, y)
        print(f"CV MAE: {mae:.6f}, RMSE: {rmse:.6f}")
        if args.model_out:
            # Fit on all data
            model = RandomForestRegressor(n_estimators=600, n_jobs=-1, random_state=42)
            model.fit(X, y)
            Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, args.model_out)
            # save metrics
            metrics = {"cv_mae": mae, "cv_rmse": rmse}
            with open(Path(args.model_out).with_suffix(".metrics.json"), "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"Saved model to {args.model_out}")
    else:
        if not args.model_in:
            raise SystemExit("--model-in is required with --predict")
        model = joblib.load(args.model_in)
        pred = model.predict(X)
        out_df = df[["open_time"]].copy()
        out_df["pred_next_close"] = pred
        if args.pred_out:
            Path(args.pred_out).parent.mkdir(parents=True, exist_ok=True)
            out_df.to_csv(args.pred_out, index=False)
            print(f"Wrote predictions to {args.pred_out}")
        else:
            print(out_df.tail(10))

if __name__ == "__main__":
    main()
