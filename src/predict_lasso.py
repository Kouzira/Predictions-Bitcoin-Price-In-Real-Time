"""
Predict next close price using trained Lasso model
"""
import argparse
import logging
import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from utils import setup_logging

def load_features(path: str):
    """Load features parquet and return X, y, df"""
    df = pd.read_parquet(path)
    df = df.sort_values("open_time").reset_index(drop=True)

    # target return
    if "y_next_ret" not in df.columns:
        raise ValueError("Features file missing 'y_next_ret'")

    df = df.dropna().reset_index(drop=True)
    y = df["y_next_ret"].values

    drop_cols = ["y_next_close", "y_next_ret", "open_time", "close_time", "open_ts"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")
    X = X.select_dtypes(include=["number"])

    return X.values, y, df


def main():
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="Path to features parquet")
    ap.add_argument("--model", required=True, help="Path to trained Lasso model")
    ap.add_argument("--scaler", required=True, help="Path to saved Scaler (joblib)")
    ap.add_argument("--n-last", type=int, default=5, help="Number of last rows to predict")
    ap.add_argument("--out", help="Optional path to save predictions as CSV")
    args = ap.parse_args()

    # load data
    X, y, df = load_features(args.features)
    last_close = df["close"].iloc[-1]
    logging.info("Loaded features: %s with %d rows", args.features, len(df))

    # load model + scaler
    model = joblib.load(args.model)
    scaler = joblib.load(args.scaler)

    # select last N rows for prediction
    X_new = X[-args.n_last:]
    closes = df["close"].iloc[-args.n_last:]

    X_scaled = scaler.transform(X_new)
    y_pred = model.predict(X_scaled)

    # convert return → price prediction
    pred_prices = closes.values * (1 + y_pred)

    results = []
    for ts, close, ret_pred, price_pred in zip(
        df["open_ts"].iloc[-args.n_last:], closes, y_pred, pred_prices
    ):
        print(f"{ts} | last_close={close:.2f} | pred_ret={ret_pred:.6f} | pred_price={price_pred:.2f}")
        results.append({
            "timestamp": ts,
            "last_close": close,
            "pred_ret": ret_pred,
            "pred_price": price_pred
        })

    # predict next step (beyond last row)
    X_last = X_new[-1].reshape(1, -1)
    X_last_scaled = scaler.transform(X_last)
    next_ret_pred = model.predict(X_last_scaled)[0]
    next_price_pred = last_close * (1 + next_ret_pred)
    logging.info("Next prediction -> return: %.6f, price: %.2f", next_ret_pred, next_price_pred)

    # save results to CSV if --out specified
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out = pd.DataFrame(results)
        df_out.to_csv(out_path, index=False)
        logging.info("Saved predictions to %s", out_path)


if __name__ == "__main__":
    main()
