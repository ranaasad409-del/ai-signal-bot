import os
import time
import asyncio
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from telegram import Bot

# ==================================================
# TELEGRAM CONFIG
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing")

if not CHAT_ID:
    raise Exception("CHAT_ID missing")

bot = Bot(token=BOT_TOKEN)

# ==================================================
# OTC PAIRS (QUOTEX STYLE)
# ==================================================

PAIRS = [
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X",
    "CADCHF=X"
]

# ==================================================
# SAVE LAST SIGNALS
# ==================================================

last_signal = {}

# ==================================================
# FORMAT OTC NAME
# ==================================================

def pair_name(pair):
    return pair.replace("=X", "") + " OTC"

# ==================================================
# RSI CALCULATION
# ==================================================

def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ==================================================
# SIGNAL LOGIC
# ==================================================

def generate_signal(df):

    try:

        close = df["Close"]

        # FIX SERIES ISSUE
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = close.astype(float)

        if len(close) < 30:
            return None, None

        # EMA
        ema_fast = close.ewm(span=5).mean()
        ema_slow = close.ewm(span=13).mean()

        # RSI
        rsi = calculate_rsi(close)

        # VALUES
        fast_now = float(ema_fast.iloc[-1])
        slow_now = float(ema_slow.iloc[-1])

        fast_prev = float(ema_fast.iloc[-2])
        slow_prev = float(ema_slow.iloc[-2])

        latest_rsi = float(rsi.iloc[-1])

        current_price = float(close.iloc[-1])

        # BUY SIGNAL
        if (
            fast_prev < slow_prev
            and fast_now > slow_now
            and latest_rsi > 50
        ):
            return "BUY", current_price

        # SELL SIGNAL
        elif (
            fast_prev > slow_prev
            and fast_now < slow_now
            and latest_rsi < 50
        ):
            return "SELL", current_price

        return None, current_price

    except Exception as e:

        print("SIGNAL ERROR:", e)
        return None, None

# ==================================================
# TIME FORMAT
# ==================================================

def get_times():

    now = datetime.utcnow()

    # NEXT CANDLE
    entry_time = (
        now + timedelta(minutes=1)
    ).replace(second=0, microsecond=0)

    # SIGNAL BEFORE 10 SEC
    signal_time = entry_time - timedelta(seconds=10)

    # EXIT AFTER 1 MIN
    exit_time = entry_time + timedelta(minutes=1)

    return (
        signal_time.strftime("%H:%M:%S"),
        entry_time.strftime("%H:%M:%S"),
        exit_time.strftime("%H:%M:%S")
    )

# ==================================================
# SEND TELEGRAM
# ==================================================

async def send_signal(pair, signal, price):

    signal_time, entry_time, exit_time = get_times()

    message = f"""
🚨 QUOTEX OTC SIGNAL 🚨

📊 Pair: {pair_name(pair)}

💰 Price: {price:.4f}

{'🟢 BUY SIGNAL' if signal == 'BUY' else '🔴 SELL SIGNAL'}

⏰ Signal Time: {signal_time} UTC

🎯 Entry Time: {entry_time} UTC

🛑 Exit Time: {exit_time} UTC

⏳ Expiry: 1 Minute
"""

    try:

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        print(f"SIGNAL SENT: {pair} {signal}")

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# ==================================================
# MARKET SCANNER
# ==================================================

async def market_scanner():

    print("QUOTEX OTC BOT STARTED")

    # STARTUP MESSAGE
    await bot.send_message(
        chat_id=CHAT_ID,
        text="✅ Quotex OTC Signal Bot Connected"
    )

    while True:

        try:

            current_second = datetime.utcnow().second

            # SEND SIGNALS AROUND XX:XX:50
            if current_second >= 50:

                print("SCANNING MARKET...")

                for pair in PAIRS:

                    try:

                        print(f"Checking {pair}")

                        df = yf.download(
                            pair,
                            period="1d",
                            interval="1m",
                            progress=False
                        )

                        if df.empty:
                            continue

                        signal, price = generate_signal(df)

                        if signal is None:
                            continue

                        current = f"{pair}_{signal}"

                        # NO DUPLICATE SIGNALS
                        if last_signal.get(pair) == current:
                            continue

                        last_signal[pair] = current

                        await send_signal(
                            pair,
                            signal,
                            price
                        )

                        await asyncio.sleep(2)

                    except Exception as pair_error:

                        print(
                            "PAIR ERROR:",
                            pair_error
                        )

                print("WAITING NEXT MINUTE...")

                await asyncio.sleep(12)

            else:

                await asyncio.sleep(1)

        except Exception as main_error:

            print(
                "MAIN LOOP ERROR:",
                main_error
            )

            await asyncio.sleep(5)

# ==================================================
# START BOT
# ==================================================

asyncio.run(market_scanner())
