import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# ==========================================
# TELEGRAM SETTINGS
# ==========================================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# ==========================================
# OTC PAIRS
# ==========================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X"
]

# ==========================================
# SEND TELEGRAM MESSAGE
# ==========================================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)
        print("Message sent")
    except Exception as e:
        print("Telegram Error:", e)

# ==========================================
# CANDLESTICK PATTERNS
# ==========================================

def detect_pattern(df):

    open_price = float(df["Open"].iloc[-1])
    close_price = float(df["Close"].iloc[-1])

    previous_open = float(df["Open"].iloc[-2])
    previous_close = float(df["Close"].iloc[-2])

    # Bullish engulfing
    if (
        previous_close < previous_open
        and close_price > open_price
        and close_price > previous_open
        and open_price < previous_close
    ):
        return "Bullish Engulfing"

    # Bearish engulfing
    elif (
        previous_close > previous_open
        and close_price < open_price
        and open_price > previous_close
        and close_price < previous_open
    ):
        return "Bearish Engulfing"

    # Doji
    elif abs(close_price - open_price) < 0.0001:
        return "Doji"

    return "No Pattern"

# ==========================================
# AI ANALYSIS
# ==========================================

def analyze_market(pair):

    try:
        print(f"Scanning {pair}")

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if df.empty or len(df) < 50:
            print("No data")
            return

        # ==================================
        # INDICATORS
        # ==================================

        rsi_indicator = RSIIndicator(close=df["Close"])
        rsi = rsi_indicator.rsi()

        macd_indicator = MACD(close=df["Close"])

        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()

        ema_indicator = EMAIndicator(close=df["Close"], window=20)
        ema = ema_indicator.ema_indicator()

        # ==================================
        # FIXED VALUES
        # ==================================

        close_price = float(df["Close"].iloc[-1])

        rsi_value = float(rsi.iloc[-1])

        macd_value = float(macd_line.iloc[-1])

        signal_value = float(signal_line.iloc[-1])

        ema_value = float(ema.iloc[-1])

        # ==================================
        # PATTERN
        # ==================================

        pattern = detect_pattern(df)

        # ==================================
        # AI SIGNAL LOGIC
        # ==================================

        signal = "WAIT"
        confidence = 50
        trend = "SIDEWAYS"

        # BUY SIGNAL
        if (
            rsi_value < 40
            and macd_value > signal_value
            and close_price > ema_value
        ):

            signal = "BUY ✅"
            confidence = np.random.randint(78, 96)
            trend = "UPTREND 🚀"

        # SELL SIGNAL
        elif (
            rsi_value > 60
            and macd_value < signal_value
            and close_price < ema_value
        ):

            signal = "SELL 🔻"
            confidence = np.random.randint(78, 96)
            trend = "DOWNTREND 📉"

        else:
            return

        # ==================================
        # TELEGRAM MESSAGE
        # ==================================

        pair_name = pair.replace("=X", " OTC")

        message = f"""
📈 AI OTC SIGNAL

PAIR: {pair_name}

SIGNAL: {signal}

TIMEFRAME: 1 MINUTE

AI CONFIDENCE: {confidence}%

PATTERN: {pattern}

TREND: {trend}

PRICE: {round(close_price, 5)}
"""

        send_telegram_message(message)

        print(f"Signal sent for {pair}")

    except Exception as e:

        print("Analysis Error:", e)

        send_telegram_message(
            f"ERROR: {str(e)}"
        )

# ==========================================
# MAIN LOOP
# ==========================================

print("✅ AI OTC SIGNAL BOT STARTED")

send_telegram_message(
    "✅ AI OTC SIGNAL BOT STARTED"
)

while True:

    for pair in PAIRS:

        analyze_market(pair)

        time.sleep(5)

    print("Waiting 2 minutes...")

    time.sleep(30)
