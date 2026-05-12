import os
import time
import asyncio
import nest_asyncio

from datetime import datetime, timedelta

import pandas as pd

from telegram import Bot

from pyquotex.stable_api import Quotex

nest_asyncio.apply()

# ======================================================
# TELEGRAM
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# ======================================================
# QUOTEX LOGIN
# ======================================================

QUOTEX_EMAIL = os.getenv("QUOTEX_EMAIL")
QUOTEX_PASSWORD = os.getenv("QUOTEX_PASSWORD")

client = Quotex(
    email=QUOTEX_EMAIL,
    password=QUOTEX_PASSWORD
)

# ======================================================
# OTC PAIRS
# ======================================================

PAIRS = [
    "USDBRL_otc",
    "USDPKR_otc",
    "USDMXN_otc",
    "CADCHF_otc",
    "EURUSD_otc",
    "GBPUSD_otc",
    "USDJPY_otc"
]

# ======================================================
# GLOBAL STATS
# ======================================================

total_signals = 0
total_wins = 0
total_losses = 0

# ======================================================
# TELEGRAM SEND
# ======================================================

async def send_message(text):

    try:

        await bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )

    except Exception as e:

        print("TELEGRAM ERROR:", e)

# ======================================================
# RSI
# ======================================================

def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ======================================================
# GET OTC SIGNAL
# ======================================================

def get_signal(pair):

    try:

        candles = client.get_candles(
            pair,
            60,
            100
        )

        if candles is None:
            return None

        df = pd.DataFrame(candles)

        if df.empty:
            return None

        close = df["close"].astype(float)

        if len(close) < 30:
            return None

        # ==========================================
        # INDICATORS
        # ==========================================

        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()

        rsi = calculate_rsi(close)

        current_price = close.iloc[-1]

        latest_ema9 = ema9.iloc[-1]
        latest_ema21 = ema21.iloc[-1]

        latest_rsi = rsi.iloc[-1]

        previous_close = close.iloc[-2]

        signal = None

        # ==========================================
        # BUY
        # ==========================================

        if (
            latest_ema9 > latest_ema21
            and latest_rsi > 55
            and current_price > previous_close
        ):

            signal = "BUY"

        # ==========================================
        # SELL
        # ==========================================

        elif (
            latest_ema9 < latest_ema21
            and latest_rsi < 45
            and current_price < previous_close
        ):

            signal = "SELL"

        if signal is None:
            return None

        return {
            "signal": signal,
            "price": float(current_price)
        }

    except Exception as e:

        print("SIGNAL ERROR:", e)

        return None

# ======================================================
# RESULT CHECKER
# ======================================================

async def check_result(pair, signal, entry_price):

    global total_signals
    global total_wins
    global total_losses

    try:

        await asyncio.sleep(60)

        candles = client.get_candles(
            pair,
            60,
            5
        )

        if candles is None:
            return

        df = pd.DataFrame(candles)

        close_price = float(df["close"].iloc[-1])

        result = "LOSS"

        if signal == "BUY":

            if close_price > entry_price:
                result = "WIN"

        elif signal == "SELL":

            if close_price < entry_price:
                result = "WIN"

        # ==========================================
        # STATS
        # ==========================================

        total_signals += 1

        if result == "WIN":
            total_wins += 1
        else:
            total_losses += 1

        accuracy = round(
            (total_wins / total_signals) * 100,
            2
        )

        result_message = f"""
🏁 TRADE RESULT

📊 Pair: {pair}

📈 Signal: {signal}

💰 Entry Price: {round(entry_price,5)}

💰 Close Price: {round(close_price,5)}

{"✅ THIS TRADE = WIN 1" if result == "WIN" else "❌ THIS TRADE = LOSS 0"}

━━━━━━━━━━━━━━━

📡 TOTAL SIGNALS: {total_signals}

✅ WINS: {total_wins}

❌ LOSSES: {total_losses}

🎯 ACCURACY: {accuracy}%
"""

        await send_message(result_message)

    except Exception as e:

        print("RESULT ERROR:", e)

# ======================================================
# SEND SIGNAL
# ======================================================

async def send_signal(pair, signal_data):

    signal = signal_data["signal"]

    price = signal_data["price"]

    now = datetime.now()

    signal_time = now.strftime("%H:%M:%S")

    # ==========================================
    # ENTRY / EXIT
    # ==========================================

    entry_time_obj = (
        now + timedelta(minutes=1)
    ).replace(second=0, microsecond=0)

    signal_send_time = entry_time_obj - timedelta(seconds=10)

    exit_time_obj = entry_time_obj + timedelta(minutes=1)

    entry_time = entry_time_obj.strftime("%H:%M:%S")

    exit_time = exit_time_obj.strftime("%H:%M:%S")

    # ==========================================
    # SIGNAL MESSAGE
    # ==========================================

    message = f"""
🔥 QUOTEX OTC SIGNAL 🔥

📊 Pair: {pair}

💰 Price: {round(price,5)}

{"🟢 BUY SIGNAL" if signal == "BUY" else "🔴 SELL SIGNAL"}

⏰ Signal Time: {signal_send_time.strftime("%H:%M:%S")}

🎯 Entry Time: {entry_time}

⌛ Exit Time: {exit_time}

🕐 Expiry: 1 Minute
"""

    await send_message(message)

    asyncio.create_task(
        check_result(
            pair,
            signal,
            price
        )
    )

# ======================================================
# MAIN LOOP
# ======================================================

async def main():

    print("CONNECTING TO QUOTEX...")

    connected = client.connect()

    if not connected:

        print("QUOTEX CONNECTION FAILED")

        await send_message(
            "❌ Quotex connection failed"
        )

        return

    print("QUOTEX CONNECTED")

    await send_message(
        "✅ Quotex OTC Bot Connected"
    )

    while True:

        try:

            current_second = datetime.now().second

            # ======================================
            # SEND SIGNAL AT :50
            # ======================================

            if current_second == 50:

                print("SCANNING MARKET...")

                for pair in PAIRS:

                    print(f"Checking {pair}")

                    signal_data = get_signal(pair)

                    if signal_data:

                        await send_signal(
                            pair,
                            signal_data
                        )

                    await asyncio.sleep(2)

                print("WAITING NEXT MINUTE...")

                await asyncio.sleep(10)

            await asyncio.sleep(1)

        except Exception as e:

            print("MAIN LOOP ERROR:", e)

            await asyncio.sleep(5)

# ======================================================
# START
# ======================================================

asyncio.run(main())
