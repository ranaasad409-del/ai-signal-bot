import os
import asyncio
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

from telegram import Bot

# ============================================
# TELEGRAM CONFIG
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# ============================================
# PAIRS
# ============================================

PAIRS = [
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X",
    "CADCHF=X",
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
]

# ============================================
# RESULTS
# ============================================

wins = 0
losses = 0

# ============================================
# GET SIGNAL
# ============================================

def get_signal(pair):

    try:

        data = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if data.empty or len(data) < 30:
            return None

        close = data["Close"]

        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        current_price = float(close.iloc[-1])

        rsi_period = 14

        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(rsi_period).mean()
        avg_loss = loss.rolling(rsi_period).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        latest_rsi = float(rsi.iloc[-1])

        latest_ema9 = float(ema9.iloc[-1])
        latest_ema21 = float(ema21.iloc[-1])

        last_candle = float(close.iloc[-1])
        prev_candle = float(close.iloc[-2])

        # BUY SIGNAL

        if (
            latest_ema9 > latest_ema21
            and latest_rsi > 55
            and last_candle > prev_candle
        ):

            return {
                "signal": "BUY",
                "price": current_price
            }

        # SELL SIGNAL

        elif (
            latest_ema9 < latest_ema21
            and latest_rsi < 45
            and last_candle < prev_candle
        ):

            return {
                "signal": "SELL",
                "price": current_price
            }

        return None

    except Exception as e:

        print("SIGNAL ERROR:", e)
        return None

# ============================================
# CHECK RESULT
# ============================================

async def check_result(pair, signal, entry_price):

    global wins, losses

    await asyncio.sleep(60)

    try:

        data = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if data.empty:
            return

        close_price = float(data["Close"].iloc[-1])

        result = "LOSS"

        if signal == "BUY" and close_price > entry_price:
            result = "WIN"

        elif signal == "SELL" and close_price < entry_price:
            result = "WIN"

        if result == "WIN":
            wins += 1
        else:
            losses += 1

        total = wins + losses

        accuracy = round((wins / total) * 100, 2)

        result_message = f"""
🏁 RESULT

📊 Pair: {pair}

🎯 Result: {result}

✅ Win = {wins}
❌ Loss = {losses}

📈 Accuracy = {accuracy}%
"""

        await bot.send_message(
            chat_id=CHAT_ID,
            text=result_message
        )

    except Exception as e:

        print("RESULT ERROR:", e)

# ============================================
# SEND SIGNAL
# ============================================

async def send_signal(pair, signal_data):

    signal = signal_data["signal"]
    price = signal_data["price"]

    now = datetime.utcnow()

    signal_time = now.strftime("%H:%M:%S UTC")

    entry_time_obj = now + timedelta(seconds=10)
    exit_time_obj = entry_time_obj + timedelta(minutes=1)

    entry_time = entry_time_obj.strftime("%H:%M:%S UTC")
    exit_time = exit_time_obj.strftime("%H:%M:%S UTC")

    pair_name = pair.replace("=X", "")

    message = f"""
🔥 QUOTEX OTC SIGNAL 🔥

📊 Pair: {pair_name} OTC

💰 Price: {round(price, 5)}

{"🟢 BUY SIGNAL" if signal == "BUY" else "🔴 SELL SIGNAL"}

⏰ Signal Time: {signal_time}

🎯 Entry Time: {entry_time}

⌛ Exit Time: {exit_time}

🕐 Expiry: 1 Minute
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

    asyncio.create_task(
        check_result(
            pair,
            signal,
            price
        )
    )

# ============================================
# MAIN LOOP
# ============================================

async def main():

    print("AI SIGNAL BOT STARTED")

    while True:

        try:

            current_second = datetime.utcnow().second

            # SEND SIGNAL AT xx:xx:50

            if current_second == 50:

                for pair in PAIRS:

                    print(f"Checking {pair}")

                    signal_data = get_signal(pair)

                    if signal_data:

                        await send_signal(pair, signal_data)

                    await asyncio.sleep(2)

                print("WAITING NEXT MINUTE...")

            await asyncio.sleep(1)

        except Exception as e:

            print("MAIN ERROR:", e)
            await asyncio.sleep(5)

# ============================================
# START
# ============================================

asyncio.run(main())
