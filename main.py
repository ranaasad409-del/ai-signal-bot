import os
import time
import asyncio
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from telegram import Bot

# =========================================================
# ENV VARIABLES
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found in Railway Variables")

if not CHAT_ID:
    raise Exception("CHAT_ID not found in Railway Variables")

bot = Bot(token=BOT_TOKEN)

# =========================================================
# PAIRS
# =========================================================

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "USDCAD=X",
    "USDCHF=X",
    "NZDUSD=X",
    "EURJPY=X",
    "GBPJPY=X",
    "USDTRY=X",
    "USDZAR=X",
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X"
]

# =========================================================
# RSI
# =========================================================

def calculate_rsi(df, period=14):

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================================================
# SIGNAL DETECTION
# =========================================================

def detect_signal(df):

    try:

        if len(df) < 20:
            return None

        close = df["Close"]

        # RSI
        rsi_series = calculate_rsi(df)
        rsi = float(rsi_series.iloc[-1])

        # EMA
        ema_fast_series = close.ewm(span=5).mean()
        ema_slow_series = close.ewm(span=10).mean()

        ema_fast = float(ema_fast_series.iloc[-1])
        ema_slow = float(ema_slow_series.iloc[-1])

        current_price = float(close.iloc[-1])

        signal = None
        trend = "SIDEWAYS"
        confidence = 50

        # BUY SIGNAL
        if ema_fast > ema_slow and rsi > 55:

            signal = "BUY"
            trend = "UPTREND"

            confidence = min(
                99,
                int((rsi + 50) / 1.4)
            )

        # SELL SIGNAL
        elif ema_fast < ema_slow and rsi < 45:

            signal = "SELL"
            trend = "DOWNTREND"

            confidence = min(
                99,
                int((100 - rsi + 50) / 1.4)
            )

        else:
            return None

        return {
            "signal": signal,
            "trend": trend,
            "confidence": confidence,
            "rsi": round(rsi, 2),
            "price": round(current_price, 5)
        }

    except Exception as e:

        print("SIGNAL ERROR:", str(e))
        return None

# =========================================================
# TELEGRAM MESSAGE
# =========================================================

async def send_signal(pair, data):

    try:

        now = datetime.utcnow()

        # SIGNAL 10 sec before next minute
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

        signal_time = next_minute - timedelta(seconds=10)

        entry_time = next_minute.strftime("%H:%M")
        exit_time = (next_minute + timedelta(minutes=1)).strftime("%H:%M")

        pair_name = pair.replace("=X", "")

        message = f"""
🔥 AI OTC SIGNAL 🔥

📊 Pair: {pair_name}

📈 Signal: {data['signal']}

💪 Confidence: {data['confidence']}%

📈 Trend: {data['trend']}

💰 Price: {data['price']}

📉 RSI: {data['rsi']}

⏰ Signal Time: {signal_time.strftime("%H:%M:%S")}

🟢 Entry Time: {entry_time}

🔴 Exit Time: {exit_time}

⚡ Duration: 1 Minute
"""

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        print(f"SENT: {pair_name} {data['signal']}")

    except Exception as e:

        print("TELEGRAM ERROR:", str(e))

# =========================================================
# GET MARKET DATA
# =========================================================

def get_data(pair):

    try:

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True
        )

        return df

    except Exception as e:

        print("DATA ERROR:", str(e))
        return None

# =========================================================
# MAIN LOOP
# =========================================================

async def scanner():

    print("AI SIGNAL BOT STARTED")

    while True:

        try:

            current_second = datetime.utcnow().second

            # Run near 50 seconds
            if current_second >= 50:

                print("SCANNING MARKET...")

                for pair in PAIRS:

                    try:

                        print(f"Scanning: {pair}")

                        df = get_data(pair)

                        if df is None or df.empty:
                            continue

                        signal = detect_signal(df)

                        if signal:

                            await send_signal(pair, signal)

                            await asyncio.sleep(2)

                    except Exception as e:

                        print("PAIR ERROR:", str(e))

                print("Waiting next cycle...")

                await asyncio.sleep(15)

            else:

                await asyncio.sleep(1)

        except Exception as e:

            print("MAIN LOOP ERROR:", str(e))

            await asyncio.sleep(10)

# =========================================================
# START BOT
# =========================================================

asyncio.run(scanner())
