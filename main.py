import time
import os
import requests
import pandas as pd
import ta
from tvDatafeed import TvDatafeed, Interval

# =====================================
# TELEGRAM SETTINGS
# =====================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =====================================
# MARKET SETTINGS
# =====================================

SYMBOL = "XAUUSD"
EXCHANGE = "OANDA"

CHECK_INTERVAL = 60

# =====================================
# SIGNAL MEMORY
# =====================================

last_signal = None

# =====================================
# CONNECT TRADINGVIEW
# =====================================

tv = TvDatafeed()

# =====================================
# TELEGRAM FUNCTION
# =====================================

def send_telegram(message):

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

        print("TELEGRAM:", response.status_code)

    except Exception as e:

        print("Telegram Error:", e)

# =====================================
# GET REAL TRADINGVIEW DATA
# =====================================

def get_data():

    try:

        df = tv.get_hist(
            symbol=SYMBOL,
            exchange=EXCHANGE,
            interval=Interval.in_1_minute,
            n_bars=200
        )

        if df is None or df.empty:

            print("No market data")

            return None

        df.reset_index(inplace=True)

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

    ema20 = latest["ema20"]

    ema50 = latest["ema50"]

    rsi = latest["rsi"]

    macd_value = latest["macd"]

    macd_signal = latest["macd_signal"]

    # =====================================
    # SIGNAL LOGIC
    # =====================================

    buy_score = 0

    sell_score = 0

    if ema20 > ema50:
        buy_score += 1

    if rsi > 55:
        buy_score += 1

    if macd_value > macd_signal:
        buy_score += 1

    if close > ema20:
        buy_score += 1

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

    else:

        print("No strong setup")

        return

    # =====================================
    # SKIP DUPLICATES
    # =====================================

    if signal == last_signal:

        print("Duplicate signal skipped")

        return

    last_signal = signal

    # =====================================
    # ENTRY / TP / SL
    # =====================================

    entry = round(close, 2)

    sl_points = 15
    tp_points = 30

    if signal == "BUY":

        tp = round(
            entry + tp_points,
            2
        )

        sl = round(
            entry - sl_points,
            2
        )

    elif signal == "SELL":

        tp = round(
            entry - tp_points,
            2
        )

        sl = round(
            entry + sl_points,
            2
        )

    print(
        f"{signal} | Entry={entry} | TP={tp} | SL={sl}"
    )

    # =====================================
    # CLEAN TELEGRAM MESSAGE
    # =====================================

    message = f"""
{signal} XAUUSD

Entry: {entry}

TP: {tp}

SL: {sl}
"""

    print(message)

    send_telegram(message)

# =====================================
# START BOT
# =====================================

print("AI GOLD BOT STARTED")

send_telegram("AI GOLD BOT CONNECTED")

# =====================================
# MAIN LOOP
# =====================================

while True:

    try:

        analyze_market()

    except Exception as e:

        print("ERROR:", e)

    time.sleep(CHECK_INTERVAL)
