# =========================================================
# AI OTC SIGNAL BOT — FINAL STABLE VERSION
# =========================================================

import os
import time
import sqlite3
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import yfinance as yf

from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

from sklearn.ensemble import RandomForestClassifier

from telegram import Bot
from flask import Flask

# =========================================================
# OPTIONAL CHART LIBRARY
# =========================================================

try:
    import mplfinance as mpf
    MPF_AVAILABLE = True
except:
    MPF_AVAILABLE = False

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q")
CHAT_ID = os.getenv("5974354691")

bot = Bot(token=BOT_TOKEN)

SCAN_INTERVAL = 20

PAIRS = [

    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X",
    "GBPJPY=X",

    "BRL=X",
    "MXN=X",
    "PKR=X"

]

# =========================================================
# FLASK SERVER
# =========================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "AI OTC SIGNAL BOT RUNNING"

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "signals.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS signals (

    pair TEXT,
    signal TEXT,
    confidence REAL,
    result TEXT,
    entry_price REAL,
    close_price REAL,
    timestamp TEXT

)

""")

conn.commit()

# =========================================================
# START MESSAGE
# =========================================================

try:

    bot.send_message(

        chat_id=CHAT_ID,

        text="""
✅ AI OTC SIGNAL BOT STARTED

📡 LIVE OTC SCANNING ENABLED
⚡ FAST SCAN MODE ENABLED
🤖 MACHINE LEARNING ACTIVE
📊 CANDLESTICK ANALYSIS ACTIVE
🧠 AI CONFIDENCE FILTER ENABLED
📈 REAL-TIME SIGNAL ENGINE READY
"""

    )

except Exception as e:

    print("Telegram Error:", e)

# =========================================================
# GET DATA
# =========================================================

def get_data(pair):

    try:

        df = yf.download(

            pair,
            period="2d",
            interval="1m",
            progress=False

        )

        if df.empty:
            return None

        df.dropna(inplace=True)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =========================================================
# ADD INDICATORS
# =========================================================

def add_indicators(df):

    close = df["Close"].squeeze()

    df["EMA10"] = EMAIndicator(
        close=close,
        window=10
    ).ema_indicator()

    df["EMA20"] = EMAIndicator(
        close=close,
        window=20
    ).ema_indicator()

    df["RSI"] = RSIIndicator(
        close=close,
        window=14
    ).rsi()

    macd = MACD(close=close)

    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()

    bb = BollingerBands(close=close)

    df["BB_HIGH"] = bb.bollinger_hband()
    df["BB_LOW"] = bb.bollinger_lband()

    return df

# =========================================================
# CANDLESTICK PATTERN
# =========================================================

def detect_pattern(df):

    try:

        last = df.iloc[-1]

        open_price = float(last["Open"])
        close_price = float(last["Close"])
        high_price = float(last["High"])
        low_price = float(last["Low"])

        body = abs(close_price - open_price)

        candle_range = high_price - low_price

        if candle_range == 0:
            return "NONE"

        # HAMMER

        if (
            body < candle_range * 0.3 and
            (min(open_price, close_price) - low_price) > body * 2
        ):
            return "HAMMER"

        # SHOOTING STAR

        if (
            body < candle_range * 0.3 and
            (high_price - max(open_price, close_price)) > body * 2
        ):
            return "SHOOTING_STAR"

        if close_price > open_price:
            return "BULLISH"

        if close_price < open_price:
            return "BEARISH"

        return "NONE"

    except Exception as e:

        print("PATTERN ERROR:", e)

        return "NONE"

# =========================================================
# MACHINE LEARNING MODEL
# =========================================================

def train_model(df):

    try:

        data = df.copy()

        data["TARGET"] = np.where(

            data["Close"].shift(-1) > data["Close"],
            1,
            0

        )

        data.dropna(inplace=True)

        features = data[[
            "RSI",
            "MACD",
            "MACD_SIGNAL"
        ]]

        target = data["TARGET"]

        model = RandomForestClassifier(
            n_estimators=100
        )

        model.fit(features, target)

        latest = features.iloc[-1:]

        prediction = model.predict(latest)[0]

        probability = model.predict_proba(latest)[0]

        confidence = round(
            max(probability) * 100,
            2
        )

        return prediction, confidence

    except Exception as e:

        print("ML ERROR:", e)

        return None, 0

# =========================================================
# CREATE CHART
# =========================================================

def create_chart(df, pair):

    try:

        if not MPF_AVAILABLE:
            return None

        filename = f"{pair}.png"

        mpf.plot(

            df.tail(80),
            type="candle",
            style="charles",
            volume=False,
            savefig=filename

        )

        return filename

    except Exception as e:

        print("CHART ERROR:", e)

        return None

# =========================================================
# SAVE SIGNAL
# =========================================================

def save_signal(

    pair,
    signal,
    confidence,
    result,
    entry_price,
    close_price

):

    try:

        cursor.execute("""

        INSERT INTO signals VALUES (?, ?, ?, ?, ?, ?, datetime('now'))

        """, (

            pair,
            signal,
            confidence,
            result,
            entry_price,
            close_price

        ))

        conn.commit()

    except Exception as e:

        print("DATABASE ERROR:", e)

# =========================================================
# ANALYZE MARKET
# =========================================================

def analyze(pair):

    try:

        print(f"Scanning {pair}")

        df = get_data(pair)

        if df is None:
            return

        df = add_indicators(df)

        pattern = detect_pattern(df)

        prediction, confidence = train_model(df)

        if prediction is None:
            return

        last = df.iloc[-1]

        current_price = round(
            float(last["Close"]),
            5
        )

        rsi = round(
            float(last["RSI"]),
            2
        )

        ema10 = float(last["EMA10"])
        ema20 = float(last["EMA20"])

        # =================================================
        # TREND
        # =================================================

        trend = "SIDEWAYS"

        if ema10 > ema20:
            trend = "UPTREND"

        elif ema10 < ema20:
            trend = "DOWNTREND"

        # =================================================
        # SIGNAL
        # =================================================

        signal = None

        if (

            prediction == 1 and
            confidence >= 75 and
            trend == "UPTREND"

        ):

            signal = "BUY"

        elif (

            prediction == 0 and
            confidence >= 75 and
            trend == "DOWNTREND"

        ):

            signal = "SELL"

        if signal is None:
            return

        # =================================================
        # PERFECT ENTRY TIMING
        # =================================================

        current_seconds = time.localtime().tm_sec

        if current_seconds < 50:

            wait_time = 50 - current_seconds

            print(f"Waiting {wait_time} sec...")

            time.sleep(wait_time)

        signal_time = time.strftime("%H:%M:%S")

        next_minute = (
            time.localtime().tm_min + 1
        ) % 60

        entry_time = time.strftime(
            f"%H:{next_minute:02d}:00"
        )

        # =================================================
        # SEND SIGNAL
        # =================================================

        message = f"""
📊 AI OTC SIGNAL

💱 PAIR: {pair.replace("=X", "")} OTC

📈 SIGNAL: {signal}

🎯 AI CONFIDENCE: {confidence}%

📊 TREND: {trend}

🕯 PATTERN: {pattern}

📉 RSI: {rsi}

💰 PRICE: {current_price}

🚨 SIGNAL TIME: {signal_time}

⏰ ENTRY TIME: {entry_time}

⌛ DURATION: 1 MINUTE

⚡ ENTER EXACTLY ON NEXT CANDLE
"""

        bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        print("Signal Sent")

        # =================================================
        # SEND CHART
        # =================================================

        chart = create_chart(df, pair)

        if chart:

            bot.send_photo(

                chat_id=CHAT_ID,
                photo=open(chart, "rb")

            )

        # =================================================
        # WAIT FOR ENTRY
        # =================================================

        seconds = time.localtime().tm_sec

        if seconds < 60:
            time.sleep(60 - seconds)

        # =================================================
        # ENTRY PRICE
        # =================================================

        entry_df = get_data(pair)

        if entry_df is None:
            return

        entry_price = round(
            float(entry_df.iloc[-1]["Close"]),
            5
        )

        print("Trade Started")

        # =================================================
        # WAIT 1 MINUTE
        # =================================================

        time.sleep(60)

        # =================================================
        # CLOSE PRICE
        # =================================================

        result_df = get_data(pair)

        if result_df is None:
            return

        close_price = round(
            float(result_df.iloc[-1]["Close"]),
            5
        )

        # =================================================
        # RESULT
        # =================================================

        result = "LOSS"

        if (
            signal == "BUY" and
            close_price > entry_price
        ):

            result = "WIN"

        elif (
            signal == "SELL" and
            close_price < entry_price
        ):

            result = "WIN"

        # =================================================
        # SAVE HISTORY
        # =================================================

        save_signal(

            pair,
            signal,
            confidence,
            result,
            entry_price,
            close_price

        )

        # =================================================
        # SEND RESULT
        # =================================================

        result_message = f"""
📋 TRADE CLOSED

💱 PAIR: {pair.replace("=X", "")}

📈 SIGNAL: {signal}

💰 ENTRY: {entry_price}

💵 CLOSE: {close_price}

🏆 RESULT: {result}

⌛ CLOSED AFTER 1 MINUTE
"""

        bot.send_message(

            chat_id=CHAT_ID,
            text=result_message

        )

        print("Trade Completed")

    except Exception as e:

        print("ANALYZE ERROR:", e)

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        for pair in PAIRS:

            analyze(pair)

        print("Waiting 20 seconds...")

        time.sleep(SCAN_INTERVAL)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(10)
