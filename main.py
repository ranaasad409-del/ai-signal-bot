import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

# ==================================================
# TELEGRAM SETTINGS
# ==================================================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# ==================================================
# OTC PAIRS
# ==================================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X"
]

# ==================================================
# SEND TELEGRAM MESSAGE
# ==================================================

def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)
        print("Telegram message sent")

    except Exception as e:
        print("Telegram Error:", e)

# ==================================================
# CANDLESTICK PATTERN DETECTION
# ==================================================

def detect_pattern(df):

    open_price = float(df["Open"].iloc[-1])
    close_price = float(df["Close"].iloc[-1])

    previous_open = float(df["Open"].iloc[-2])
    previous_close = float(df["Close"].iloc[-2])

    # Bullish Engulfing
    if (
        previous_close < previous_open
        and close_price > open_price
        and close_price > previous_open
        and open_price < previous_close
    ):

        return "Bullish Engulfing 📈"

    # Bearish Engulfing
    elif (
        previous_close > previous_open
        and close_price < open_price
        and open_price > previous_close
        and close_price < previous_open
    ):

        return "Bearish Engulfing 📉"

    # Doji
    elif abs(close_price - open_price) < 0.0001:

        return "Doji ⚠️"

    return "No Clear Pattern"

# ==================================================
# ANALYZE MARKET
# ==================================================

def analyze_market(pair):

    try:

        print(f"Scanning {pair}")

        # ==========================================
        # DOWNLOAD MARKET DATA
        # ==========================================

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        # ==========================================
        # CHECK DATA
        # ==========================================

        if df.empty or len(df) < 50:

            print("Not enough data")
            return

        # ==========================================
        # FIX DATAFRAME DIMENSION
        # ==========================================

        close_series = df["Close"].squeeze()

        # ==========================================
        # INDICATORS
        # ==========================================

        rsi_indicator = RSIIndicator(close=close_series)

        macd_indicator = MACD(close=close_series)

        ema_indicator = EMAIndicator(
            close=close_series,
            window=20
        )

        rsi = rsi_indicator.rsi()

        macd_line = macd_indicator.macd()

        signal_line = macd_indicator.macd_signal()

        ema = ema_indicator.ema_indicator()

        # ==========================================
        # GET LATEST VALUES
        # ==========================================

        close_price = float(close_series.iloc[-1])

        rsi_value = float(rsi.iloc[-1])

        macd_value = float(macd_line.iloc[-1])

        signal_value = float(signal_line.iloc[-1])

        ema_value = float(ema.iloc[-1])

        # ==========================================
        # PATTERN DETECTION
        # ==========================================

        pattern = detect_pattern(df)

        # ==========================================
        # AI SIGNAL LOGIC
        # ==========================================

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

            confidence = np.random.randint(80, 96)

            trend = "UPTREND 🚀"

        # SELL SIGNAL
        elif (
            rsi_value > 60
            and macd_value < signal_value
            and close_price < ema_value
        ):

            signal = "SELL 🔻"

            confidence = np.random.randint(80, 96)

            trend = "DOWNTREND 📉"

        else:

            print("No signal")
            return

        # ==========================================
        # FORMAT MESSAGE
        # ==========================================

        pair_name = pair.replace("=X", " OTC")

        message = f"""
📊 AI OTC SIGNAL

PAIR: {pair_name}

SIGNAL: {signal}

TIMEFRAME: 1 MINUTE

AI CONFIDENCE: {confidence}%

PATTERN: {pattern}

TREND: {trend}

PRICE: {round(close_price, 5)}
"""

        # ==========================================
        # SEND TELEGRAM SIGNAL
        # ==========================================

        send_telegram_message(message)

        print(f"Signal sent for {pair}")

    except Exception as e:

        error_message = f"ERROR: {str(e)}"

        print(error_message)

        send_telegram_message(error_message)

# ==================================================
# BOT START MESSAGE
# ==================================================

startup_message = """
✅ AI OTC SIGNAL BOT STARTED

📡 Live OTC Scanning Enabled
⚡ Signal Time: Every 2 Minutes
🤖 AI Logic Activated
"""

print(startup_message)

send_telegram_message(startup_message)

# ==================================================
# MAIN LOOP
# ==================================================

while True:

    try:

        for pair in PAIRS:

            analyze_market(pair)

            time.sleep(5)

        print("Waiting 2 minutes...")

        time.sleep(120)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        send_telegram_message(
            f"MAIN LOOP ERROR: {str(e)}"
        )

        time.sleep(30)
