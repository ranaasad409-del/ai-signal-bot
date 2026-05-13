import time
import os
import requests
import pandas as pd
import ta
import yfinance as yf
from datetime import datetime

# =====================================
# TELEGRAM SETTINGS
# =====================================

# AUTO LOAD FROM RAILWAY VARIABLES

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHAT_ID = os.getenv("CHAT_ID")

# =====================================
# MARKET SETTINGS
# =====================================

SYMBOL = "GC=F"   # GOLD FUTURES

CHECK_INTERVAL = 60

# =====================================
# DUPLICATE SIGNAL PROTECTION
# =====================================

last_signal = None

# =====================================
# TELEGRAM FUNCTION
# =====================================

def send_telegram(message):

    # CHECK VARIABLES

    if not BOT_TOKEN or not CHAT_ID:

        print("Missing BOT_TOKEN or CHAT_ID")

        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            url,
            data=payload,
            timeout=10
        )

        print("TELEGRAM STATUS:", response.status_code)

        print("TELEGRAM RESPONSE:", response.text)

    except Exception as e:

        print("Telegram Error:", e)

# =====================================
# GET MARKET DATA
# =====================================

def get_data():

    try:

        df = yf.download(
            tickers=SYMBOL,
            interval="1m",
            period="1d",
            progress=False,
            auto_adjust=False
        )

        if df.empty:

            print("No market data found")

            return None

        # FIX MULTIINDEX

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        # RESET INDEX

        df.reset_index(inplace=True)

        # LOWERCASE COLUMNS

        df.columns = [str(col).lower() for col in df.columns]

        print("COLUMNS:", df.columns)

        # CONVERT TO NUMBERS

        numeric_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]

        for col in numeric_cols:

            if col in df.columns:

                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        # REMOVE EMPTY VALUES

        df.dropna(inplace=True)

        return df

    except Exception as e:

        print("DATA ERROR:", e)

        return None

# =====================================
# ANALYZE MARKET
# =====================================

def analyze_market():

    global last_signal

    df = get_data()

    if df is None:

        return

    # =====================================
    # INDICATORS
    # =====================================

    df["ema20"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    df["rsi"] = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    macd = ta.trend.MACD(
        close=df["close"]
    )

    df["macd"] = macd.macd()

    df["macd_signal"] = macd.macd_signal()

    # =====================================
    # LATEST CANDLE
    # =====================================

    latest = df.iloc[-1]

    close = float(latest["close"])

    print("LIVE PRICE:", close)

    ema20 = latest["ema20"]

    ema50 = latest["ema50"]

    rsi = latest["rsi"]

    macd_value = latest["macd"]

    macd_signal = latest["macd_signal"]

    # =====================================
    # BUY CONDITIONS
    # =====================================

    buy_score = 0

    if ema20 > ema50:
        buy_score += 1

    if rsi > 55:
        buy_score += 1

    if macd_value > macd_signal:
        buy_score += 1

    if close > ema20:
        buy_score += 1

    # =====================================
    # SELL CONDITIONS
    # =====================================

    sell_score = 0

    if ema20 < ema50:
        sell_score += 1

    if rsi < 45:
        sell_score += 1

    if macd_value < macd_signal:
        sell_score += 1

    if close < ema20:
        sell_score += 1

    # =====================================
    # FINAL SIGNAL
    # =====================================

    signal = None

    if buy_score >= 4:

        signal = "BUY"

    elif sell_score >= 4:

        signal = "SELL"

    # =====================================
    # PREVENT DUPLICATES
    # =====================================

    if signal == last_signal:

        print("Duplicate signal skipped")

        return

    last_signal = signal

    # =====================================
    # TP / SL CALCULATION
    # =====================================

    risk_percent = 0.002
    reward_percent = 0.004

    if signal == "BUY":

        entry = round(close, 2)

        stop_loss = round(
            entry * (1 - risk_percent),
            2
        )

        take_profit = round(
            entry * (1 + reward_percent),
            2
        )

    elif signal == "SELL":

        entry = round(close, 2)

        stop_loss = round(
            entry * (1 + risk_percent),
            2
        )

        take_profit = round(
            entry * (1 - reward_percent),
            2
        )

    else:

        print("No strong setup found")

        return

    # =====================================
    # SIGNAL CONFIDENCE
    # =====================================

    confidence = max(
        buy_score,
        sell_score
    ) * 25

    # =====================================
    # TELEGRAM MESSAGE
    # =====================================

    message = f"""
🔥 AI GOLD SNIPER SIGNAL 🔥

📊 Symbol: GOLD (GC=F)

📈 Signal: {signal}

🎯 Entry: {entry}

🛑 Stop Loss: {stop_loss}

💰 Take Profit: {take_profit}

📉 RSI: {round(rsi, 2)}

⚡ Confidence: {confidence}%

🕒 Time:
{datetime.now()}
"""

    print(message)

    send_telegram(message)

# =====================================
# START BOT
# =====================================

print("AI GOLD BOT STARTED")

send_telegram("✅ AI GOLD BOT CONNECTED SUCCESSFULLY")

# =====================================
# MAIN LOOP
# =====================================

while True:

    try:

        analyze_market()

    except Exception as e:

        print("ERROR:", e)

    time.sleep(CHECK_INTERVAL)
