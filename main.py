import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import time

def analyze_market(symbol="EURUSD=X"):
    try:
        df = yf.download(symbol, period="1d", interval="5m")

        if df.empty:
            print("No market data found")
            return

        # Fix dataframe issue
        close = df["Close"].squeeze()

        # Indicators
        rsi = RSIIndicator(close=close, window=14).rsi()

        macd_indicator = MACD(close=close)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()

        latest_price = close.iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd_line.iloc[-1]
        latest_signal = signal_line.iloc[-1]

        print("\n========================")
        print(" AI SIGNAL BOT ")
        print("========================")
        print(f"Symbol: {symbol}")
        print(f"Current Price: {latest_price}")
        print(f"RSI: {latest_rsi:.2f}")
        print(f"MACD: {latest_macd:.5f}")
        print(f"Signal Line: {latest_signal:.5f}")

        # Signal Logic
        if latest_rsi < 30 and latest_macd > latest_signal:
            print(">>> BUY SIGNAL")
        elif latest_rsi > 70 and latest_macd < latest_signal:
            print(">>> SELL SIGNAL")
        else:
            print(">>> NO CLEAR SIGNAL")

    except Exception as e:
        print("Error:", e)

# Run continuously
while True:
    analyze_market()
    time.sleep(300)  # 5 minutes
