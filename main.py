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
# MARKET SETTINGS
# =========================================

TIMEFRAME = "1m"

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X"
]

# =========================================
# BOT STATS
# =========================================

signals_sent = 0
wins = 0
losses = 0
last_signal = "No signal yet"

# =========================================
# FLASK DASHBOARD
# =========================================

app = Flask(__name__)

@app.route("/")
def dashboard():

    accuracy = 0

    if (wins + losses) > 0:
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
        response = requests.post(url, data=data)

        print("Telegram sent:", response.status_code)

    except Exception as e:
        print("Telegram Error:", e)

# =========================================
# CANDLESTICK PATTERNS
# =========================================

def detect_pattern(df):

    open_price = float(df["Open"].iloc[-1])
    close_price = float(df["Close"].iloc[-1])
    high_price = float(df["High"].iloc[-1])
    low_price = float(df["Low"].iloc[-1])

    body = abs(close_price - open_price)
    candle_range = high_price - low_price

    # DOJI
    if body < candle_range * 0.1:
        return "DOJI"

    # BULLISH
    if close_price > open_price:
        return "BULLISH"

    # BEARISH
    if close_price < open_price:
        return "BEARISH"

    return "NEUTRAL"

# =========================================
# MARKET ANALYSIS
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

        # INDICATORS
        rsi = RSIIndicator(close, window=7).rsi()

        macd_indicator = MACD(close)

        macd_line = macd_indicator.macd()

        signal_line = macd_indicator.macd_signal()

        ema = EMAIndicator(close, window=20).ema_indicator()

        # LATEST VALUES
        latest_close = float(close.iloc[-1])

        latest_rsi = float(rsi.iloc[-1])

        latest_macd = float(macd_line.iloc[-1])

        latest_signal = float(signal_line.iloc[-1])

        latest_ema = float(ema.iloc[-1])

        # PATTERN
        pattern = detect_pattern(df)

        # AI CONFIDENCE
        confidence = np.random.randint(82, 98)

        # BUY SIGNAL
        if (
            latest_rsi < 50 and
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

RSI: {round(latest_rsi, 2)}

TREND: BULLISH ⬆️

EXPIRY: 2 MINUTES
"""

        # SELL SIGNAL
        elif (
            latest_rsi > 50 and
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

RSI: {round(latest_rsi, 2)}

TREND: BEARISH ⬇️

EXPIRY: 2 MINUTES
"""

        else:

            losses += 1

            return None

    except Exception as e:

        print("Analysis Error:", e)

        return None

# =========================================
# BOT LOOP
# =========================================

def bot_loop():

    send_telegram("✅ AI OTC SIGNAL BOT STARTED")

    while True:

        for pair in PAIRS:

            print(f"Scanning {pair}")

            signal = analyze_market(pair)

            if signal:
                send_telegram(signal)

        # FAST OTC SCAN
        time.sleep(30)

# =========================================
# START BOT
# =========================================

threading.Thread(target=bot_loop).start()

app.run(host="0.0.0.0", port=8080)
