import os
import asyncio
import warnings
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import ta

from telegram import Bot
from telegram.constants import ParseMode

warnings.filterwarnings("ignore")

# =====================================================
# CONFIG
# =====================================================

BOT_TOKEN = os.getenv("8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q")
CHAT_ID = os.getenv("5974354691")

bot = Bot(token=BOT_TOKEN)

SCAN_INTERVAL = 30

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "EURJPY=X",
    "GBPJPY=X",
    "USDBRL=X",
    "USDPKR=X",
    "USDMXN=X"
]

# =====================================================
# TELEGRAM
# =====================================================

async def send_telegram_message(message):

    try:

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )

        print("Telegram message sent")

    except Exception as e:

        print(f"Telegram Error: {e}")

# =====================================================
# DOWNLOAD DATA
# =====================================================

def get_data(pair):

    try:

        df = yf.download(
            pair,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        df.dropna(inplace=True)

        return df

    except Exception as e:

        print(f"DATA ERROR {pair}: {e}")
        return None

# =====================================================
# PATTERN DETECTION
# =====================================================

def detect_pattern(df):

    try:

        last = df.iloc[-1]
        prev = df.iloc[-2]

        open_price = float(last["Open"])
        close_price = float(last["Close"])

        prev_open = float(prev["Open"])
        prev_close = float(prev["Close"])

        # Bullish engulfing
        if (
            close_price > open_price and
            prev_close < prev_open and
            close_price > prev_open and
            open_price < prev_close
        ):
            return "BUY"

        # Bearish engulfing
        if (
            close_price < open_price and
            prev_close > prev_open and
            close_price < prev_open and
            open_price > prev_close
        ):
            return "SELL"

        return "HOLD"

    except Exception as e:

        print(f"PATTERN ERROR: {e}")
        return "HOLD"

# =====================================================
# SIGNAL GENERATOR
# =====================================================

def generate_signal(df):

    try:

        close_series = df["Close"]

        close = float(close_series.iloc[-1])

        rsi = ta.momentum.RSIIndicator(
            close_series
        ).rsi().iloc[-1]

        sma_fast = ta.trend.SMAIndicator(
            close_series,
            window=5
        ).sma_indicator().iloc[-1]

        sma_slow = ta.trend.SMAIndicator(
            close_series,
            window=20
        ).sma_indicator().iloc[-1]

        macd = ta.trend.MACD(
            close_series
        ).macd_diff().iloc[-1]

        pattern = detect_pattern(df)

        signal = "HOLD"
        trend = "SIDEWAYS"
        confidence = 50

        # BUY LOGIC
        if (
            rsi > 50 and
            sma_fast > sma_slow and
            macd > 0 and
            pattern == "BUY"
        ):

            signal = "BUY"
            trend = "UPTREND"
            confidence = 90

        # SELL LOGIC
        elif (
            rsi < 50 and
            sma_fast < sma_slow and
            macd < 0 and
            pattern == "SELL"
        ):

            signal = "SELL"
            trend = "DOWNTREND"
            confidence = 90

        return {
            "signal": signal,
            "trend": trend,
            "confidence": confidence,
            "rsi": round(float(rsi), 2),
            "price": round(close, 5)
        }

    except Exception as e:

        print(f"SIGNAL ERROR: {e}")

        return None

# =====================================================
# ENTRY TIME
# =====================================================

def get_entry_times():

    now = datetime.now()

    next_minute = (now + timedelta(minutes=1)).replace(
        second=0,
        microsecond=0
    )

    signal_time = next_minute - timedelta(seconds=10)

    expiry_time = next_minute + timedelta(minutes=1)

    return (
        signal_time.strftime("%H:%M:%S"),
        next_minute.strftime("%H:%M"),
        expiry_time.strftime("%H:%M")
    )

# =====================================================
# SEND SIGNAL
# =====================================================

async def process_pair(pair):

    try:

        print(f"Scanning {pair}")

        df = get_data(pair)

        if df is None:
            return

        result = generate_signal(df)

        if result is None:
            return

        signal = result["signal"]

        if signal == "HOLD":
            return

        signal_time, entry_time, expiry_time = get_entry_times()

        pair_name = pair.replace("=X", "")

        message = f"""
📊 <b>AI OTC SIGNAL</b>

💱 <b>PAIR:</b> {pair_name} OTC

📢 <b>SIGNAL:</b> {signal}

🧠 <b>AI CONFIDENCE:</b> {result['confidence']}%

📈 <b>TREND:</b> {result['trend']}

📍 <b>RSI:</b> {result['rsi']}

💰 <b>PRICE:</b> {result['price']}

⏰ <b>SIGNAL TIME:</b> {signal_time}

🟢 <b>ENTRY TIME:</b> {entry_time}

🔴 <b>EXIT TIME:</b> {expiry_time}

⏳ <b>TRADE DURATION:</b> 1 MINUTE

⚡ FAST OTC AI MODE ENABLED
"""

        await send_telegram_message(message)

    except Exception as e:

        print(f"PAIR ERROR {pair}: {e}")

# =====================================================
# MAIN LOOP
# =====================================================

async def main():

    startup = """
✅ <b>AI OTC SIGNAL BOT STARTED</b>

🚀 Live OTC Scanning Enabled
⚡ Fast Scan Every 30 Seconds
🧠 AI Candlestick Logic Activated
"""

    await send_telegram_message(startup)

    while True:

        try:

            tasks = []

            for pair in PAIRS:

                tasks.append(
                    process_pair(pair)
                )

            await asyncio.gather(*tasks)

        except Exception as e:

            print(f"MAIN LOOP ERROR: {e}")

        print("Waiting 30 seconds...\n")

        await asyncio.sleep(SCAN_INTERVAL)

# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    asyncio.run(main())
