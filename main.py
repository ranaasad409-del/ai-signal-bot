import os
import time
import asyncio
import pandas as pd
import yfinance as yf

from telegram import Bot

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing")

if not CHAT_ID:
    raise Exception("CHAT_ID missing")

bot = Bot(token=BOT_TOKEN)

# =========================
# OTC PAIRS ONLY
# =========================

PAIRS = [
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X"
]

# =========================
# TELEGRAM SEND
# =========================

async def send_signal(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("Telegram message sent")
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# SIGNAL LOGIC
# =========================

def get_signal(symbol):

    try:
        data = yf.download(
            symbol,
            period="1d",
            interval="1m",
            progress=False
        )

        if data.empty:
            print("No data:", symbol)
            return None

        close = data["Close"]

        # FIX FOR SERIES ERROR
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = close.dropna()

        if len(close) < 20:
            return None

        price = float(close.iloc[-1])

        sma5 = float(close.tail(5).mean())
        sma10 = float(close.tail(10).mean())

        # SIMPLE SIGNALS
        if sma5 > sma10:
            return f"🟢 BUY SIGNAL\n\nPair: {symbol}\nPrice: {price}"

        elif sma5 < sma10:
            return f"🔴 SELL SIGNAL\n\nPair: {symbol}\nPrice: {price}"

        return None

    except Exception as e:
        print("SIGNAL ERROR:", e)
        return None

# =========================
# MAIN LOOP
# =========================

async def main():

    print("AI SIGNAL BOT STARTED")

    # TEST MESSAGE
    await send_signal("✅ BOT CONNECTED SUCCESSFULLY")

    while True:

        for pair in PAIRS:

            print("Scanning:", pair)

            signal = get_signal(pair)

            if signal:
                await send_signal(signal)

            await asyncio.sleep(5)

        print("Waiting next cycle...")
        await asyncio.sleep(60)

# =========================
# START BOT
# =========================

asyncio.run(main())
