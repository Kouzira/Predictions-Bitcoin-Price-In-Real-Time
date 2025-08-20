# src/update_fetch_klines.py
import argparse
import os
from datetime import datetime, timedelta
import pandas as pd

from binance_rest import download_klines as get_klines
from storage import write_parquet_partitioned


def main():
    parser = argparse.ArgumentParser(description="Auto update OHLCV from Binance")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--out", default="data/klines")
    args = parser.parse_args()

    start_date = datetime(2020, 1, 1).date()
    end_date = datetime.utcnow().date()  # hôm nay UTC

    # Kiểm tra xem trong thư mục đã có dữ liệu đến ngày nào
    last_date = start_date
    symbol_dir = os.path.join(args.out, f"symbol={args.symbol}", f"interval={args.interval}")
    if os.path.exists(symbol_dir):
        dates = []
        for d in os.listdir(symbol_dir):
            if d.startswith("date="):
                try:
                    dates.append(datetime.strptime(d.split("=")[1], "%Y-%m-%d").date())
                except:
                    pass
        if dates:
            last_date = max(dates) + timedelta(days=1)  # tải từ ngày tiếp theo

    print(f"Updating {args.symbol} {args.interval} from {last_date} to {end_date}")

    # Lặp từng ngày
    cur = last_date
    while cur <= end_date:
        next_day = cur + timedelta(days=1)
        df = get_klines(args.symbol, args.interval, cur, next_day)
        if not df.empty:
            write_parquet_partitioned(df, args.out, args.symbol, args.interval)
            print(f"Saved {len(df)} rows for {cur}")
        cur = next_day


if __name__ == "__main__":
    main()
