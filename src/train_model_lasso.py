"""
Train Lasso Regression model to predict next return
"""
import argparse
import logging
import pandas as pd
import numpy as np
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import joblib

from utils import setup_logging

def load_features(path: str):
    df = pd.read_parquet(path)

    # dùng y_next_ret làm target (tỷ suất sinh lời)
    df["target"] = df["y_next_ret"]
    df = df.dropna()

    drop_cols = ["target", "y_next_close", "y_next_ret",
                 "open_time", "close_time", "open_ts"]

    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.select_dtypes(include=["number"])

    y = df["target"].values
    return X.values, y, df

def train_eval(X, y, alpha=0.001):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    maes, rmses = [], []
    for tr, val in kf.split(X):
        Xt, Xv = X[tr], X[val]
        yt, yv = y[tr], y[val]
        scaler = StandardScaler()
        Xt_scaled = scaler.fit_transform(Xt)
        Xv_scaled = scaler.transform(Xv)
        model = Lasso(alpha=alpha, max_iter=10000, random_state=42)
        model.fit(Xt_scaled, yt)
        pred = model.predict(Xv_scaled)
        maes.append(mean_absolute_error(yv, pred))
        rmses.append(root_mean_squared_error(yv, pred))
    return np.mean(maes), np.mean(rmses)

def main():
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="Path to features parquet")
    ap.add_argument("--model-out", required=True, help="Path to save model")
    ap.add_argument("--scaler-out", required=True, help="Path to save scaler")
    ap.add_argument("--alpha", type=float, default=0.001, help="Lasso regularization strength")
    args = ap.parse_args()

    X, y, df = load_features(args.features)
    logging.info("Loaded %s with shape %s", args.features, X.shape)

    mae, rmse = train_eval(X, y, alpha=args.alpha)
    logging.info("CV MAE: %.6f, RMSE: %.6f", mae, rmse)

    # Train final model with scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = Lasso(alpha=args.alpha, max_iter=10000, random_state=42)
    model.fit(X_scaled, y)

    joblib.dump(model, args.model_out)
    joblib.dump(scaler, args.scaler_out)
    logging.info("Saved Lasso model to %s", args.model_out)
    logging.info("Saved Scaler to %s", args.scaler_out)

if __name__ == "__main__":
    main()
