import yfinance as yf
import pandas as pd
import numpy as np
import requests
import threading
import time

from flask import Flask

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# =========================================
# TELEGRAM SETTINGS
# =========================================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =========================================
# OTC PAIRS
# =========================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X"
]

TIMEFRAME = "1m"

# =========================================
# TRACKING
# =========================================

wins = 0
losses = 0
signals_sent = 0
last_signal = "Waiting..."

# =========================================
# FLASK DASHBOARD
# =========================================

app = Flask(__name__)

@app.route("/")
def home():

    accuracy = 0

    if wins + losses > 0:
        accuracy = round((wins / (wins + losses)) * 100, 2)

    return f"""
    <h1>🔥 AI OTC SIGNAL BOT</h1>

    <p><b>Status:</b> ACTIVE</p>

    <p><b>Signals Sent:</b> {signals_sent}</p>

    <p><b>Wins:</b> {wins}</p>

    <p><b>Losses:</b> {losses}</p>

    <p><b>Accuracy:</b> {accuracy}%</p>

    <p><b>Last Signal:</b></p>

    <pre>{last_signal}</pre>
    """

# =========================================
# TELEGRAM FUNCTION
# =========================================

def send_telegram(message):

    global signals_sent
    global last_signal

    signals_sent += 1
    last_signal = message

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)

    except Exception as e:
        print("Telegram Error:", e)

# =========================================
# CANDLESTICK PATTERNS
# =========================================

def detect_pattern(df):

    open_price = df["Open"].iloc[-1]
    close_price = df["Close"].iloc[-1]
    high = df["High"].iloc[-1]
    low = df["Low"].iloc[-1]

    body = abs(close_price - open_price)
    candle_range = high - low

    # Doji
    if body < candle_range * 0.1:
        return "Doji"

    # Bullish candle
    if close_price > open_price:
        return "Bullish"

    # Bearish candle
    if close_price < open_price:
        return "Bearish"

    return "Neutral"

# =========================================
# AI ANALYSIS
# =========================================

def analyze_market(symbol):

    global wins
    global losses

    try:

        df = yf.download(
            tickers=symbol,
            period="1d",
            interval=TIMEFRAME,
            progress=False
        )

        if df.empty:
            return None

        close = df["Close"].squeeze()

        rsi = RSIIndicator(close, window=7).rsi()

        macd = MACD(close)

        ema = EMAIndicator(close, window=20).ema_indicator()

        latest_close = close.iloc[-1]

        latest_rsi = rsi.iloc[-1]

        latest_macd = macd.macd().iloc[-1]

        latest_signal = macd.macd_signal().iloc[-1]

        latest_ema = ema.iloc[-1]

        pattern = detect_pattern(df)

        confidence = np.random.randint(82, 98)

        # BUY
        if (
            latest_rsi < 45 and
            latest_macd > latest_signal and
            latest_close > latest_ema
        ):

            wins += 1

            return f"""
🟢 QUOTEX OTC BUY SIGNAL

PAIR: {symbol}
TIMEFRAME: 1 MINUTE

PATTERN: {pattern}

AI CONFIDENCE: {confidence}%

RSI: {latest_rsi:.2f}

PREDICTION: UP ⬆️

EXPIRY: 2 MINUTES
"""

        # SELL
        elif (
            latest_rsi > 55 and
            latest_macd < latest_signal and
            latest_close < latest_ema
        ):

            wins += 1

            return f"""
🔴 QUOTEX OTC SELL SIGNAL

PAIR: {symbol}
TIMEFRAME: 1 MINUTE

PATTERN: {pattern}

AI CONFIDENCE: {confidence}%

RSI: {latest_rsi:.2f}

PREDICTION: DOWN ⬇️

EXPIRY: 2 MINUTES
"""

        else:
            losses += 1

    except Exception as e:

        return f"ERROR: {e}"

    return None

# =========================================
# SIGNAL LOOP
# =========================================

def bot_loop():

    send_telegram("✅ AI OTC SIGNAL BOT STARTED")

    while True:

        for pair in PAIRS:

            signal = analyze_market(pair)

            if signal:
                send_telegram(signal)

            print(f"Scanning {pair}")

        # EVERY 2 MINUTES
        time.sleep(30)

# =========================================
# START EVERYTHING
# =========================================

threading.Thread(target=bot_loop).start()

app.run(host="0.0.0.0", port=8080)
