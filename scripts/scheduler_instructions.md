# Windows Task Scheduler Instructions

1. Open Task Scheduler → Create Basic Task.
2. Choose trigger (Daily, 00:10 for example).
3. Action: Start a Program.
   - Program/script: C:\path\to\python.exe
   - Arguments: src\fetch_klines.py --symbol BTCUSDT --interval 1h --start 2023-01-01 --end 2023-12-31 --out data\klines
   - Start in: C:\path\to\crypto-ml-pipeline-binance-windows
