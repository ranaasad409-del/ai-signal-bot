import yfinance as yf
import pandas as pd
import numpy as np
import requests
import sqlite3
import threading
import time
import mplfinance as mpf
import matplotlib.pyplot as plt

from flask import Flask
from datetime import datetime, timedelta

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

from sklearn.ensemble import RandomForestClassifier

# =====================================================
# TELEGRAM SETTINGS
# =====================================================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =====================================================
# FLASK DASHBOARD
# =====================================================

app = Flask(__name__)

# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect(
    "signals.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS signals (
id INTEGER PRIMARY KEY AUTOINCREMENT,
pair TEXT,
signal TEXT,
confidence REAL,
result TEXT,
entry_price REAL,
close_price REAL,
entry_time TEXT
)
""")

conn.commit()

# =====================================================
# PAIRS
# =====================================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X",
    "GBPJPY=X"
]

# =====================================================
# BOT STATS
# =====================================================

wins = 0
losses = 0
total_signals = 0

signal_history = {}

# =====================================================
# TELEGRAM FUNCTIONS
# =====================================================

def send_telegram(text):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": text
        }

        requests.post(url, data=data)

        print("Telegram message sent")

    except Exception as e:

        print("Telegram Error:", e)

# =====================================================
# SEND CHART IMAGE
# =====================================================

def send_chart(df, pair, signal_type):

    try:

        chart_name = f"{pair}.png"

        mpf.plot(
            df.tail(50),
            type='candle',
            style='charles',
            volume=False,
            savefig=chart_name
        )

        files = {
            "photo": open(chart_name, "rb")
        }

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": f"{pair} {signal_type}"
            },
            files=files
        )

    except Exception as e:

        print("Chart Error:", e)

# =====================================================
# MACHINE LEARNING MODEL
# =====================================================

def train_model(df):

    try:

        df["target"] = np.where(
            df["Close"].shift(-1) > df["Close"],
            1,
            0
        )

        df.dropna(inplace=True)

        features = df[[
            "RSI",
            "MACD"
        ]]

        target = df["target"]

        model = RandomForestClassifier(
            n_estimators=100
        )

        model.fit(features, target)

        prediction = model.predict(
            features.tail(1)
        )[0]

        probability = model.predict_proba(
            features.tail(1)
        )[0]

        confidence = round(
            max(probability) * 100,
            2
        )

        return prediction, confidence

    except Exception as e:

        print("ML Error:", e)

        return None, 0

# =====================================================
# RESULT CHECK
# =====================================================

def check_result(
    pair,
    signal_type,
    entry_price
):

    global wins
    global losses
    global total_signals

    try:

        time.sleep(60)

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if df.empty:
            return

        close_prices = np.array(
            df["Close"]
        ).flatten()

        close_price = float(
            close_prices[-1]
        )

        result = "LOSS ❌"

        if signal_type == "BUY ✅":

            if close_price > entry_price:
                result = "WIN ✅"
                wins += 1
            else:
                losses += 1

        elif signal_type == "SELL 🔻":

            if close_price < entry_price:
                result = "WIN ✅"
                wins += 1
            else:
                losses += 1

        total_signals += 1

        accuracy = round(
            (wins / total_signals) * 100,
            2
        )

        # SAVE RESULT

        cursor.execute("""
        INSERT INTO signals (
            pair,
            signal,
            confidence,
            result,
            entry_price,
            close_price,
            entry_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pair,
            signal_type,
            accuracy,
            result,
            entry_price,
            close_price,
            datetime.now().strftime("%H:%M")
        ))

        conn.commit()

        result_message = f"""
🏁 TRADE RESULT

PAIR: {pair.replace('=X', ' OTC')}

RESULT: {result}

ENTRY PRICE: {entry_price}

CLOSE PRICE: {round(close_price, 5)}

📊 TOTAL SIGNALS: {total_signals}

✅ WINS: {wins}

❌ LOSSES: {losses}

🎯 ACCURACY: {accuracy}%
"""

        send_telegram(result_message)

    except Exception as e:

        print("Result Error:", e)

# =====================================================
# MARKET ANALYSIS
# =====================================================

def analyze_market(pair):

    global signal_history

    try:

        print(f"Scanning {pair}")

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if df.empty or len(df) < 100:
            return

        close_prices = np.array(
            df["Close"]
        ).flatten()

        close_series = pd.Series(
            close_prices
        )

        # =========================================
        # INDICATORS
        # =========================================

        rsi_indicator = RSIIndicator(
            close_series
        )

        rsi = rsi_indicator.rsi()

        macd_indicator = MACD(
            close_series
        )

        macd = macd_indicator.macd()

        macd_signal = macd_indicator.macd_signal()

        ema_indicator = EMAIndicator(
            close_series,
            window=20
        )

        ema = ema_indicator.ema_indicator()

        # =========================================
        # DATAFRAME
        # =========================================

        df["RSI"] = rsi.values
        df["MACD"] = macd.values

        df.dropna(inplace=True)

        # =========================================
        # ML PREDICTION
        # =========================================

        prediction, confidence = train_model(df)

        # =========================================
        # LAST VALUES
        # =========================================

        last_close = float(
            close_prices[-1]
        )

        last_rsi = float(
            rsi.iloc[-1]
        )

        last_macd = float(
            macd.iloc[-1]
        )

        last_macd_signal = float(
            macd_signal.iloc[-1]
        )

        last_ema = float(
            ema.iloc[-1]
        )

        # =========================================
        # SIGNAL LOGIC
        # =========================================

        signal_type = None

        trend = "SIDEWAYS"

        if (
            prediction == 1
            and last_macd > last_macd_signal
            and last_close > last_ema
        ):

            signal_type = "BUY ✅"

            trend = "UPTREND 🚀"

        elif (
            prediction == 0
            and last_macd < last_macd_signal
            and last_close < last_ema
        ):

            signal_type = "SELL 🔻"

            trend = "DOWNTREND 📉"

        if signal_type is None:
            return

        # =========================================
        # DUPLICATE FILTER
        # =========================================

        signal_key = f"{pair}_{signal_type}"

        current_time = time.time()

        if signal_key in signal_history:

            previous_time = signal_history[
                signal_key
            ]

            if current_time - previous_time < 120:
                return

        signal_history[
            signal_key
        ] = current_time

        # =========================================
        # ENTRY / EXPIRY
        # =========================================

        entry_time = datetime.now()

        expiry_time = (
            entry_time +
            timedelta(minutes=1)
        )

        entry_text = entry_time.strftime(
            "%I:%M %p"
        )

        expiry_text = expiry_time.strftime(
            "%I:%M %p"
        )

        # =========================================
        # MESSAGE
        # =========================================

        message = f"""
📊 AI OTC SIGNAL

PAIR: {pair.replace('=X', ' OTC')}

SIGNAL: {signal_type}

AI CONFIDENCE: {confidence}%

TREND: {trend}

ENTRY TIME: {entry_text}

EXPIRY TIME: {expiry_text}

TRADE TIME: 1 Minute

RSI: {round(last_rsi, 2)}

PRICE: {round(last_close, 5)}

⚡ Fast Scan Mode Enabled
"""

        send_telegram(message)

        send_chart(
            df,
            pair,
            signal_type
        )

        print("Signal sent")

        # =========================================
        # RESULT CHECK
        # =========================================

        threading.Thread(
            target=check_result,
            args=(
                pair,
                signal_type,
                last_close
            )
        ).start()

    except Exception as e:

        print("ERROR:", e)

# =====================================================
# FLASK DASHBOARD ROUTE
# =====================================================

@app.route("/")

def dashboard():

    accuracy = 0

    if total_signals > 0:

        accuracy = round(
            (wins / total_signals) * 100,
            2
        )

    html = f"""
    <h1>AI OTC SIGNAL BOT</h1>

    <h2>LIVE STATS</h2>

    <p>Total Signals: {total_signals}</p>

    <p>Wins: {wins}</p>

    <p>Losses: {losses}</p>

    <p>Accuracy: {accuracy}%</p>

    <p>Scanner Running...</p>
    """

    return html

# =====================================================
# START FLASK
# =====================================================

def start_flask():

    app.run(
        host="0.0.0.0",
        port=5000
    )

# =====================================================
# STARTUP MESSAGE
# =====================================================

send_telegram("""
🚀 AI OTC SIGNAL BOT STARTED

🛰 Live OTC Scanner Active

⚡ Fast Signal Engine Running

🤖 Machine Learning Enabled

📈 Real-Time Charts Enabled

📊 Dashboard Running

🔥 AI Trading System Online
""")

# =====================================================
# START DASHBOARD THREAD
# =====================================================

threading.Thread(
    target=start_flask
).start()

# =====================================================
# MAIN LOOP
# =====================================================

while True:

    try:

        for pair in PAIRS:

            analyze_market(pair)

            time.sleep(5)

        print("Waiting 30 seconds...")

        time.sleep(30)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        time.sleep(10)
