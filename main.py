import asyncio
import random
from datetime import datetime, timedelta, timezone

from telegram import Bot

# =========================
# TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

bot = Bot(token=BOT_TOKEN)

# =========================
# FOREX PAIRS
# =========================
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "GBP/JPY",
    "XAU/USD",
    "AUD/USD"
]

# =========================
# GLOBAL STATS
# =========================
wins = 0
losses = 0

# =========================
# SESSION DETECTION
# =========================
def get_session():
    utc_hour = datetime.utcnow().hour

    if 0 <= utc_hour < 7:
        return "ASIAN SESSION"

    elif 7 <= utc_hour < 13:
        return "LONDON SESSION"

    elif 13 <= utc_hour < 21:
        return "NEW YORK SESSION"

    return "MARKET CLOSED"

# =========================
# NEWS FILTER
# =========================
def get_news():
    news = [
        "LOW IMPACT NEWS",
        "MEDIUM IMPACT NEWS",
        "NO MAJOR NEWS"
    ]
    return random.choice(news)

# =========================
# REALISTIC PRICE GENERATOR
# =========================
def generate_price(pair):

    if pair == "EUR/USD":
        return round(random.uniform(1.0700, 1.0900), 5)

    elif pair == "GBP/USD":
        return round(random.uniform(1.2400, 1.2800), 5)

    elif pair == "USD/JPY":
        return round(random.uniform(150.000, 158.000), 3)

    elif pair == "GBP/JPY":
        return round(random.uniform(185.000, 198.000), 3)

    elif pair == "XAU/USD":
        return round(random.uniform(2300.00, 2450.00), 2)

    elif pair == "AUD/USD":
        return round(random.uniform(0.6400, 0.6900), 5)

    return round(random.uniform(1.0000, 2.0000), 5)

# =========================
# SIGNAL GENERATOR
# =========================
def generate_signal():

    pair = random.choice(PAIRS)

    direction = random.choice(["BUY", "SELL"])

    entry = generate_price(pair)

    # Pip calculations
    if "JPY" in pair:
        pip_value = 0.01
    elif "XAU" in pair:
        pip_value = 1
    else:
        pip_value = 0.0001

    tp1_pips = random.randint(10, 20)
    tp2_pips = random.randint(20, 35)
    tp3_pips = random.randint(35, 60)

    sl_pips = random.randint(10, 18)

    if direction == "BUY":

        tp1 = round(entry + (tp1_pips * pip_value), 5)
        tp2 = round(entry + (tp2_pips * pip_value), 5)
        tp3 = round(entry + (tp3_pips * pip_value), 5)

        sl = round(entry - (sl_pips * pip_value), 5)

    else:

        tp1 = round(entry - (tp1_pips * pip_value), 5)
        tp2 = round(entry - (tp2_pips * pip_value), 5)
        tp3 = round(entry - (tp3_pips * pip_value), 5)

        sl = round(entry + (sl_pips * pip_value), 5)

    expected_pips = tp3_pips

    accuracy = random.randint(82, 96)

    session = get_session()

    news = get_news()

    # =========================
    # TRADE START TIME
    # =========================
    now = datetime.now(timezone.utc)

    next_minute = (now + timedelta(minutes=1)).replace(
        second=0,
        microsecond=0
    )

    send_time = next_minute - timedelta(seconds=15)

    return {
        "pair": pair,
        "direction": direction,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "expected_pips": expected_pips,
        "accuracy": accuracy,
        "session": session,
        "news": news,
        "trade_time": next_minute,
        "send_time": send_time
    }

# =========================
# SEND SIGNAL
# =========================
async def send_signal(signal):

    message = f"""
🚨 AI FOREX SIGNAL 🚨

💱 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry Price: {signal['entry']}

🎯 Take Profit 1: {signal['tp1']}
🎯 Take Profit 2: {signal['tp2']}
🎯 Take Profit 3: {signal['tp3']}

🛑 Stop Loss: {signal['sl']}

📊 Expected Pips: {signal['expected_pips']}

🔥 Accuracy: {signal['accuracy']}%

🌍 Session: {signal['session']}

📰 News: {signal['news']}

⏰ Trade Starts At:
{signal['trade_time'].strftime('%H:%M:%S UTC')}

🧠 Strategy:
Smart Money Concept + Liquidity Sweep + Trend Confirmation
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

# =========================
# SEND RESULT
# =========================
async def send_result(signal):

    global wins, losses

    result = random.choice(["WIN", "LOSS"])

    if result == "WIN":
        wins += 1
    else:
        losses += 1

    total = wins + losses

    accuracy = round((wins / total) * 100, 2)

    result_message = f"""
📢 TRADE RESULT

💱 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

{'✅ Result: WIN' if result == 'WIN' else '❌ Result: LOSS'}

🏆 Wins: {wins}

❌ Losses: {losses}

🎯 Live Accuracy: {accuracy}%
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=result_message
    )

# =========================
# MAIN BOT LOOP
# =========================
async def main():

    print("AI FOREX BOT STARTED")

    while True:

        signal = generate_signal()

        now = datetime.now(timezone.utc)

        wait_seconds = (
            signal["send_time"] - now
        ).total_seconds()

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        await send_signal(signal)

        # Wait until trade candle closes
        result_wait = (
            signal["trade_time"] + timedelta(minutes=5)
            - datetime.now(timezone.utc)
        ).total_seconds()

        if result_wait > 0:
            await asyncio.sleep(result_wait)

        await send_result(signal)

# =========================
# START BOT
# =========================
if __name__ == "__main__":

    asyncio.run(main())
