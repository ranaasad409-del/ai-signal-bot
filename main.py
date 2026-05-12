import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# =====================================
# TELEGRAM SETTINGS
# =====================================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =====================================
# MARKET SETTINGS
# =====================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "GBPJPY=X",
    "AUDUSD=X"
]

TIMEFRAME = "1m"

# =====================================
# TELEGRAM ALERT
# =====================================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)

    except Exception as e:
        print("Telegram Error:", e)

# =====================================
# GET LIVE MARKET DATA
# =====================================

def get_data(symbol):

    try:

        df = yf.download(
            symbol,
            period="1d",
            interval=TIMEFRAME,
            progress=False
        )

        if df.empty:
            return None

        return df

    except Exception as e:

        print("Data Error:", e)
        return None

# =====================================
# CANDLESTICK PATTERNS
# =====================================

def bullish_engulfing(df):

    try:

        prev_open = df["Open"].iloc[-2]
        prev_close = df["Close"].iloc[-2]

        curr_open = df["Open"].iloc[-1]
        curr_close = df["Close"].iloc[-1]

        return (
            prev_close < prev_open and
            curr_close > curr_open and
            curr_close > prev_open and
            curr_open < prev_close
        )

    except:
        return False

def bearish_engulfing(df):

    try:

        prev_open = df["Open"].iloc[-2]
        prev_close = df["Close"].iloc[-2]

        curr_open = df["Open"].iloc[-1]
        curr_close = df["Close"].iloc[-1]

        return (
            prev_close > prev_open and
            curr_close < curr_open and
            curr_open > prev_close and
            curr_close < prev_open
        )

    except:
        return False

# =====================================
# AI SIGNAL ANALYSIS
# =====================================

def analyze_market(symbol):

    df = get_data(symbol)

    if df is None:
        return None

    close = df["Close"].squeeze()

    # RSI
    rsi = RSIIndicator(close, window=14).rsi()

    # MACD
    macd = MACD(close)

    macd_line = macd.macd()
    signal_line = macd.macd_signal()

    # EMA
    ema_fast = EMAIndicator(close, window=9).ema_indicator()
    ema_slow = EMAIndicator(close, window=21).ema_indicator()

    latest_rsi = rsi.iloc[-1]
    latest_macd = macd_line.iloc[-1]
    latest_signal = signal_line.iloc[-1]

    latest_fast = ema_fast.iloc[-1]
    latest_slow = ema_slow.iloc[-1]

    # =====================================
    # AI CONFIDENCE SCORE
    # =====================================

    score_buy = 0
    score_sell = 0

    # RSI
    if latest_rsi < 35:
        score_buy += 25

    if latest_rsi > 65:
        score_sell += 25

    # MACD
    if latest_macd > latest_signal:
        score_buy += 25

    if latest_macd < latest_signal:
        score_sell += 25

    # EMA TREND
    if latest_fast > latest_slow:
        score_buy += 25

    if latest_fast < latest_slow:
        score_sell += 25

    # CANDLE PATTERN
    if bullish_engulfing(df):
        score_buy += 25

    if bearish_engulfing(df):
        score_sell += 25

    # =====================================
    # FINAL SIGNAL
    # =====================================

    if score_buy >= 75:

        return {
            "signal": "BUY",
            "confidence": score_buy,
            "rsi": round(latest_rsi, 2)
        }

    elif score_sell >= 75:

        return {
            "signal": "SELL",
            "confidence": score_sell,
            "rsi": round(latest_rsi, 2)
        }

    return None

# =====================================
# MAIN BOT LOOP
# =====================================

print("🚀 QUOTEX AI SIGNAL BOT STARTED")

last_signal = ""

while True:

    try:

        for pair in PAIRS:

            result = analyze_market(pair)

            if result:

                signal = result["signal"]
                confidence = result["confidence"]

                signal_id = f"{pair}-{signal}"

                if signal_id != last_signal:

                    pair_name = pair.replace("=X", "")

                    message = f"""
🚨 QUOTEX OTC SIGNAL 🚨

💱 Pair: {pair_name}
📈 Signal: {signal}
🕐 Expiry: 1 Minute
🔥 Confidence: {confidence}%
📊 RSI: {result['rsi']}

⚡ AI + Candlestick Strategy
"""

                    print(message)

                    send_telegram(message)

                    last_signal = signal_id

            else:

                print(f"No signal on {pair}")

            time.sleep(10)

        print("Scanning market again...")

        time.sleep(30)

    except Exception as e:

        print("Main Error:", e)

        time.sleep(60)
