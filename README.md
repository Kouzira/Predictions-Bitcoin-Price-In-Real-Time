# Crypto ML Pipeline (Binance, Windows Version)
## 🚀 Quickstart

### 1) Chuẩn bị môi trường Python
Yêu cầu Python 3.9+

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### 2) Tải dữ liệu lịch sử (klines → Parquet)
Chạy file batch:  
```bat
scripts\run_fetch_klines.bat
```

Dữ liệu sẽ được lưu dạng partitioned:
```
data\klines\symbol=BTCUSDT\interval=1h\date=2023-01-01\*.parquet
```

---

### 3) Stream realtime klines (JSONL)
```bat
scripts\run_stream_ws.bat
```

Output:  
```
data\stream\btc_kline_1m.jsonl
```

---

### 4) Xây dựng features từ Parquet
```bat
scripts\run_features.bat
```

Output:  
```
data\features\BTCUSDT_1h.parquet
```

---

### 5) Huấn luyện mô hình
```bat
scripts\run_train_model.bat
```

Output:  
```
models\rf_btcusdt_1h.joblib
```

---

### 6) Dự đoán (batch) với model đã lưu
```bat
python src\train_model.py --predict ^
  --features data\features\BTCUSDT_1h.parquet ^
  --model-in models\rf_btcusdt_1h.joblib ^
  --pred-out data\predictions\BTCUSDT_1h.csv
```
---

## ⏰ Scheduling trên Windows
Để chạy tự động (thay vì double click `.bat`):
1. Mở **Task Scheduler** → *Create Basic Task*.
2. Chọn trigger (VD: daily, 00:10).
3. Action: **Start a program**  
   - Program/script: `C:\path\to\python.exe`  
   - Arguments: `src\fetch_klines.py --symbol BTCUSDT --interval 1h --start 2023-01-01 --end 2023-12-31 --out data\klines`  
   - Start in: `C:\path\to\crypto-ml-pipeline-binance-windows`

---

## 📝 Notes
- Public endpoints → không cần API key. Nếu sau này cần private endpoints, bạn phải thêm `.env`.
- Parquet dùng `pyarrow`.  
- Đây là repo **học tập**, không nên dùng trực tiếp cho trading production.  
