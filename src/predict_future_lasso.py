"""
Recursive multi-step prediction with Lasso
"""
import argparse
import logging
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from utils import setup_logging
from features import build_features 

def recursive_forecast(df: pd.DataFrame, model, scaler, steps: int, interval="1h"):
    history = df.copy()
    preds = []

    for i in range(steps):
        # build features lại từ history
        feat = build_features(history.copy())

        # lấy hàng cuối cùng làm input
        X = feat.drop(columns=["y_next_close", "y_next_ret", "open_time",
                               "close_time", "open_ts"], errors="ignore")
        X = X.select_dtypes(include=["number"])
        X_last = X.values[-1].reshape(1, -1)

        # scale và predict return
        X_last_scaled = scaler.transform(X_last)
        pred_ret = model.predict(X_last_scaled)[0]

        last_close = history["close"].iloc[-1]
        pred_price = last_close * (1 + pred_ret)

        ts_next = history["open_ts"].iloc[-1] + pd.to_timedelta(1, unit=interval)
        preds.append((ts_next, last_close, pred_ret, pred_price))

        # thêm hàng giả lập cho bước tiếp theo
        new_row = history.iloc[-1].copy()
        new_row["open_time"] = (ts_next.value // 10**6)   # ms
        new_row["close"] = pred_price
        new_row["open_ts"] = ts_next
        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

    return pd.DataFrame(preds, columns=["timestamp", "last_close", "pred_ret", "pred_price"])


def main():
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="Path to features parquet")
    ap.add_argument("--model", required=True, help="Path to Lasso model")
    ap.add_argument("--scaler", required=True, help="Path to saved Scaler")
    ap.add_argument("--steps", type=int, default=24, help="How many future steps to predict")
    ap.add_argument("--out", default="pred_future.csv", help="CSV output file")
    args = ap.parse_args()

    # load data
    df = pd.read_parquet(args.features).sort_values("open_time").reset_index(drop=True)
    logging.info("Loaded %s with %d rows", args.features, len(df))

    model = joblib.load(args.model)
    scaler = joblib.load(args.scaler)

    preds = recursive_forecast(df, model, scaler, steps=args.steps, interval="h")
    preds.to_csv(args.out, index=False)
    logging.info("Saved future predictions to %s", args.out)
    print(preds)

        # save results to CSV if --out specified
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out = pd.DataFrame(preds)
        df_out.to_csv(out_path, index=False)
        logging.info("Saved predictions to %s", out_path)


if __name__ == "__main__":
    main()
