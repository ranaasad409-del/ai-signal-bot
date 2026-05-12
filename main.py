import os
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
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
# STATS
# ============================================

wins = 0
losses = 0

# ============================================
# SEND TELEGRAM MESSAGE
# ============================================

async def send_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# ============================================
# SIGNAL GENERATOR
# ============================================

async def check_signal(pair):
    global wins, losses

    try:
        print(f"Checking {pair}")

        data = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if data.empty:
            return

        close = data["Close"]

        if len(close) < 30:
            return

        # ============================================
        # INDICATORS
        # ============================================

        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        delta = close.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        # ============================================
        # SAFE FLOAT VALUES
        # ============================================

        current_price = close.iloc[-1].item()

        last_candle = close.iloc[-1].item()
        prev_candle = close.iloc[-2].item()

        latest_rsi = rsi.iloc[-1].item()

        latest_ema9 = ema9.iloc[-1].item()
        latest_ema21 = ema21.iloc[-1].item()

        # ============================================
        # SIGNAL LOGIC
        # ============================================

        signal = None

        # BUY
        if (
            latest_ema9 > latest_ema21
            and latest_rsi < 70
            and last_candle > prev_candle
        ):
            signal = "BUY"

        # SELL
        elif (
            latest_ema9 < latest_ema21
            and latest_rsi > 30
            and last_candle < prev_candle
        ):
            signal = "SELL"

        if signal is None:
            return

        # ============================================
        # TIME
        # ============================================

        now = datetime.now()

        signal_time = now.strftime("%H:%M:%S")

        entry_time_dt = (now + timedelta(seconds=10)).replace(second=0)

        exit_time_dt = entry_time_dt + timedelta(minutes=1)

        entry_time = entry_time_dt.strftime("%H:%M:%S")
        exit_time = exit_time_dt.strftime("%H:%M:%S")

        # ============================================
        # SEND SIGNAL
        # ============================================

        message = f"""
🔥 QUOTEX OTC SIGNAL 🔥

📊 Pair: {pair.replace("=X", "")} OTC

💰 Price: {round(current_price, 5)}

{"🟢 BUY SIGNAL" if signal == "BUY" else "🔴 SELL SIGNAL"}

⏰ Signal Time: {signal_time}

🎯 Entry Time: {entry_time}

⌛ Exit Time: {exit_time}

🕐 Expiry: 1 Minute
"""

        await send_message(message)

        # ============================================
        # WAIT FOR RESULT
        # ============================================

        wait_seconds = (
            exit_time_dt - datetime.now()
        ).total_seconds()

        if wait_seconds > 0:
            time.sleep(wait_seconds)

        # ============================================
        # CHECK RESULT
        # ============================================

        result_data = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False
        )

        if result_data.empty:
            return

        close_price = result_data["Close"].iloc[-1].item()

        result = "LOSS"

        if signal == "BUY" and close_price > current_price:
            result = "WIN"

        elif signal == "SELL" and close_price < current_price:
            result = "WIN"

        # ============================================
        # STATS
        # ============================================

        if result == "WIN":
            wins += 1
        else:
            losses += 1

        total = wins + losses

        accuracy = 0

        if total > 0:
            accuracy = round((wins / total) * 100, 2)

        # ============================================
        # SEND RESULT
        # ============================================

        result_message = f"""
📈 SIGNAL RESULT

📊 Pair: {pair.replace("=X", "")}

{"✅ WIN = 1" if result == "WIN" else "❌ LOSS = 0"}

🏆 Wins: {wins}

💀 Losses: {losses}

🎯 Accuracy: {accuracy}%
"""

        await send_message(result_message)

    except Exception as e:
        print("SIGNAL ERROR:", e)

# ============================================
# MAIN LOOP
# ============================================

async def main():
    print("AI SIGNAL BOT STARTED")

    await send_message("✅ Quotex OTC Signal Bot Connected")

    while True:
        try:
            current_second = datetime.now().second

            # SEND SIGNALS AT :50
            if current_second == 50:

                for pair in PAIRS:
                    await check_signal(pair)

                print("WAITING NEXT MINUTE...")
                time.sleep(15)

            time.sleep(1)

        except Exception as e:
            print("MAIN LOOP ERROR:", e)
            time.sleep(5)

# ============================================
# START
# ============================================

import asyncio
asyncio.run(main())
