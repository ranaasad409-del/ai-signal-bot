import os
import time
import asyncio
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from telegram import Bot

# ============================================
# TELEGRAM CONFIG
# ============================================

BOT_TOKEN = os.getenv("8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q")
CHAT_ID = os.getenv("5974354691")

print("BOT TOKEN =", BOT_TOKEN)
print("CHAT ID =", CHAT_ID)

bot = Bot(token=BOT_TOKEN)

# ============================================
# PAIRS
# ============================================

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

# ============================================
# INDICATORS
# ============================================

def calculate_rsi(data, period=14):
    delta = data["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


def detect_signal(df):
    try:
        close = df["Close"]

        rsi = calculate_rsi(df).iloc[-1]

        ema_fast = close.ewm(span=5).mean().iloc[-1]
        ema_slow = close.ewm(span=10).mean().iloc[-1]

        current_price = close.iloc[-1]

        signal = None
        trend = "SIDEWAYS"
        confidence = 50

        # BUY
        if ema_fast > ema_slow and rsi > 50:
            signal = "BUY"
            trend = "UPTREND"
            confidence = min(99, int((rsi + 50) / 1.5))

        # SELL
        elif ema_fast < ema_slow and rsi < 50:
            signal = "SELL"
            trend = "DOWNTREND"
            confidence = min(99, int((100 - rsi + 50) / 1.5))

        return {
            "signal": signal,
            "trend": trend,
            "confidence": confidence,
            "rsi": round(float(rsi), 2),
            "price": round(float(current_price), 5)
        }

    except Exception as e:
        print("SIGNAL ERROR:", e)
        return None


# ============================================
# TELEGRAM MESSAGE
# ============================================

async def send_signal(pair, data):

    now = datetime.utcnow()

    # SIGNAL 10 seconds before candle
    entry_time = (now + timedelta(minutes=1)).replace(second=0)

    signal_time = entry_time - timedelta(seconds=10)

    exit_time = entry_time + timedelta(minutes=1)

    signal_text = f"""
📊 AI OTC SIGNAL

PAIR: {pair.replace("=X","")}

SIGNAL: {data['signal']}

AI CONFIDENCE: {data['confidence']}%

TREND: {data['trend']}

RSI: {data['rsi']}

PRICE: {data['price']}

⏰ SIGNAL TIME: {signal_time.strftime('%H:%M:%S')} UTC

🚀 ENTRY TIME: {entry_time.strftime('%H:%M:%S')} UTC

⌛ TRADE DURATION: 1 MINUTE

🏁 EXIT TIME: {exit_time.strftime('%H:%M:%S')} UTC

⚡ FAST SCAN MODE ENABLED
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=signal_text
    )

    print("SIGNAL SENT:", pair)


# ============================================
# SCAN MARKET
# ============================================

async def scan_market():

    while True:

        try:

            print("===================================")
            print("NEW MARKET SCAN:", datetime.utcnow())
            print("===================================")

            for pair in PAIRS:

                try:

                    print(f"Scanning {pair}")

                    df = yf.download(
                        pair,
                        period="1d",
                        interval="1m",
                        progress=False
                    )

                    if df.empty:
                        print("No data:", pair)
                        continue

                    signal_data = detect_signal(df)

                    if signal_data is None:
                        continue

                    if signal_data["signal"] is not None:

                        await send_signal(pair, signal_data)

                    await asyncio.sleep(2)

                except Exception as pair_error:
                    print("PAIR ERROR:", pair_error)

            print("Waiting 30 seconds...")
            await asyncio.sleep(30)

        except Exception as main_error:
            print("MAIN LOOP ERROR:", main_error)
            await asyncio.sleep(10)


# ============================================
# START BOT
# ============================================

async def main():

    print("===================================")
    print("AI SIGNAL BOT STARTED")
    print("===================================")

    await scan_market()


if __name__ == "__main__":
    asyncio.run(main())
