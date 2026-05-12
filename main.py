import yfinance as yf
import pandas as pd
import requests
import time

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

PAIR = "EURUSD=X"
TIMEFRAME = "1m"

# =========================
# TELEGRAM
# =========================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

# =========================
# AI SIGNAL
# =========================

def analyze_market():

    df = yf.download(
        tickers=PAIR,
        period="1d",
        interval=TIMEFRAME,
        progress=False
    )

    if df.empty:
        return None

    close = df["Close"].squeeze()

    # Indicators
    rsi = RSIIndicator(close, window=7).rsi()

    macd = MACD(close)

    ema = EMAIndicator(close, window=20).ema_indicator()

    latest_close = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]

    latest_macd = macd.macd().iloc[-1]
    latest_signal = macd.macd_signal().iloc[-1]

    latest_ema = ema.iloc[-1]

    # BUY SIGNAL
    if latest_rsi < 45 and latest_macd > latest_signal and latest_close > latest_ema:

        return f"""
🟢 BUY SIGNAL

Pair: EUR/USD OTC
Timeframe: 1 Minute

RSI: {latest_rsi:.2f}

AI Prediction: UP ⬆️
Expiry: 2 Minute
"""

    # SELL SIGNAL
    elif latest_rsi > 55 and latest_macd < latest_signal and latest_close < latest_ema:

        return f"""
🔴 SELL SIGNAL

Pair: EUR/USD OTC
Timeframe: 1 Minute

RSI: {latest_rsi:.2f}

AI Prediction: DOWN ⬇️
Expiry: 2 Minute
"""

    return None

# =========================
# START BOT
# =========================

send_telegram("✅ AI OTC SIGNAL BOT STARTED")

while True:

    try:

        signal = analyze_market()

        if signal:
            send_telegram(signal)

        print("Scanning market...")

    except Exception as e:

        send_telegram(f"Bot Error: {e}")

    # EVERY 2 MINUTES
    time.sleep(120)
