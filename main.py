import yfinance as yf
import pandas as pd
import requests
import time

from ta.momentum import RSIIndicator
from ta.trend import MACD

# =========================
# TELEGRAM
# =========================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =========================
# SETTINGS
# =========================

PAIR = "EURUSD=X"
TIMEFRAME = "1m"

# =========================
# TELEGRAM FUNCTION
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print(response.text)
    except Exception as e:
        print(e)

# =========================
# MARKET ANALYSIS
# =========================

def analyze_market():

    df = yf.download(
        tickers=PAIR,
        period="1d",
        interval=TIMEFRAME,
        progress=False
    )

    if df.empty:
        return "No data"

    close = df["Close"].squeeze()

    rsi = RSIIndicator(close, window=14).rsi()
    macd = MACD(close)

    latest_rsi = rsi.iloc[-1]
    latest_macd = macd.macd().iloc[-1]
    latest_signal = macd.macd_signal().iloc[-1]

    # BUY
    if latest_rsi < 30 and latest_macd > latest_signal:
        return f"""
🟢 BUY SIGNAL

Pair: EUR/USD OTC
Timeframe: 1 Minute
RSI: {latest_rsi:.2f}

AI Prediction: UP
"""

    # SELL
    elif latest_rsi > 70 and latest_macd < latest_signal:
        return f"""
🔴 SELL SIGNAL

Pair: EUR/USD OTC
Timeframe: 1 Minute
RSI: {latest_rsi:.2f}

AI Prediction: DOWN
"""

    return None

# =========================
# MAIN LOOP
# =========================

send_telegram("✅ AI Signal Bot Started")

while True:

    try:
        signal = analyze_market()

        if signal:
            send_telegram(signal)

        print("Running...")

    except Exception as e:
        print(e)
        send_telegram(f"Error: {e}")

    time.sleep(60)
