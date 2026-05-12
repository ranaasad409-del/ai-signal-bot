import os
import time
import asyncio
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from telegram import Bot

# ============================================
# TELEGRAM SETTINGS
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found in Railway Variables")

if not CHAT_ID:
    raise Exception("CHAT_ID not found in Railway Variables")

bot = Bot(token=BOT_TOKEN)

# ============================================
# OTC PAIRS ONLY
# ============================================

PAIRS = [
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X"
]

# ============================================
# SEND TELEGRAM MESSAGE
# ============================================

async def send_telegram_message(message):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        print("Signal sent successfully")

    except Exception as e:
        print("Telegram Error:", e)

# ============================================
# SIGNAL GENERATOR
# ============================================

def generate_signal(symbol):

    try:
        print(f"Scanning: {symbol}")

        df = yf.download(
            symbol,
            period="1d",
            interval="1m",
            progress=False
        )

        if df.empty or len(df) < 30:
            return None

        # CLOSE PRICE
        close = df["Close"].astype(float)

        current_price = float(close.iloc[-1])

        # EMA STRATEGY
        ema_fast = close.ewm(span=5).mean()
        ema_slow = close.ewm(span=13).mean()

        fast_now = float(ema_fast.iloc[-1])
        slow_now = float(ema_slow.iloc[-1])

        # SIGNAL TYPE
        if fast_now > slow_now:
            signal = "BUY"

        elif fast_now < slow_now:
            signal = "SELL"

        else:
            return None

        # TIME
        now = datetime.utcnow()

        next_candle = (now + timedelta(minutes=1)).replace(
            second=0,
            microsecond=0
        )

        signal_time = next_candle - timedelta(seconds=10)

        entry_time = next_candle.strftime("%H:%M")
        exit_time = (next_candle + timedelta(minutes=1)).strftime("%H:%M")

        # MESSAGE
        message = f"""
🔥 AI OTC SIGNAL 🔥

PAIR: {symbol.replace('=X', '')}
SIGNAL: {signal}

SIGNAL TIME: {signal_time.strftime('%H:%M:%S')} UTC
ENTRY TIME: {entry_time} UTC
EXIT TIME: {exit_time} UTC

PRICE: {round(current_price, 5)}
"""

        return message

    except Exception as e:
        print("SIGNAL ERROR:", e)
        return None

# ============================================
# MAIN LOOP
# ============================================

async def main():

    print("AI SIGNAL BOT STARTED")

    while True:

        for pair in PAIRS:

            signal = generate_signal(pair)

            if signal:
                await send_telegram_message(signal)

            await asyncio.sleep(5)

        print("Waiting next cycle...")
        await asyncio.sleep(30)

# ============================================
# START BOT
# ============================================

if __name__ == "__main__":
    asyncio.run(main())
