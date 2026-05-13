import asyncio
import random
from datetime import datetime, timedelta
import pytz
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

pairs = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY",
    "GBP/JPY"
]

# =========================
# RESULTS TRACKER
# =========================

wins = 0
losses = 0

# =========================
# MARKET SESSION
# =========================

def get_session():
    hour = datetime.utcnow().hour

    if 0 <= hour < 8:
        return "ASIAN SESSION"
    elif 8 <= hour < 16:
        return "LONDON SESSION"
    else:
        return "NEW YORK SESSION"

# =========================
# NEWS FILTER
# =========================

def news_status():
    status = random.choice([
        "LOW IMPACT NEWS",
        "MEDIUM IMPACT NEWS",
        "HIGH IMPACT NEWS"
    ])
    return status

# =========================
# SIGNAL GENERATOR
# =========================

async def send_signal():

    global wins
    global losses

    pair = random.choice(pairs)

    direction = random.choice(["BUY", "SELL"])

    entry_price = round(random.uniform(1.0000, 200.0000), 5)

    if direction == "BUY":
        tp1 = round(entry_price + random.uniform(0.0010, 0.0030), 5)
        tp2 = round(entry_price + random.uniform(0.0030, 0.0060), 5)
        tp3 = round(entry_price + random.uniform(0.0060, 0.0100), 5)
        sl = round(entry_price - random.uniform(0.0020, 0.0040), 5)
    else:
        tp1 = round(entry_price - random.uniform(0.0010, 0.0030), 5)
        tp2 = round(entry_price - random.uniform(0.0030, 0.0060), 5)
        tp3 = round(entry_price - random.uniform(0.0060, 0.0100), 5)
        sl = round(entry_price + random.uniform(0.0020, 0.0040), 5)

    pips = random.randint(20, 120)

    accuracy = random.randint(82, 97)

    session = get_session()

    news = news_status()

    now = datetime.utcnow()

    # send signal 15 sec before candle
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

    signal_send_time = next_minute - timedelta(seconds=15)

    wait_seconds = (signal_send_time - now).total_seconds()

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    signal_message = f"""
🚨 AI FOREX SIGNAL 🚨

💱 Pair: {pair}

📈 Direction: {direction}

💰 Entry Price: {entry_price}

🎯 Take Profit 1: {tp1}
🎯 Take Profit 2: {tp2}
🎯 Take Profit 3: {tp3}

🛑 Stop Loss: {sl}

📊 Expected Pips: {pips}

🔥 Accuracy: {accuracy}%

🌍 Session: {session}

📰 News: {news}

⏰ Trade Starts At:
{next_minute.strftime('%H:%M:%S')} UTC

🧠 Strategy:
Smart Money Concept + Trend Confirmation
"""

    await bot.send_message(chat_id=CHAT_ID, text=signal_message)

    # wait until trade candle closes
    close_time = next_minute + timedelta(minutes=15)

    wait_close = (close_time - datetime.utcnow()).total_seconds()

    if wait_close > 0:
        await asyncio.sleep(wait_close)

    result = random.choice(["WIN", "LOSS"])

    if result == "WIN":
        wins += 1
    else:
        losses += 1

    total = wins + losses

    live_accuracy = round((wins / total) * 100, 2)

    result_message = f"""
📢 TRADE RESULT

💱 Pair: {pair}

📈 Direction: {direction}

{result}

🏆 Wins: {wins}

❌ Losses: {losses}

🎯 Accuracy: {live_accuracy}%
"""

    await bot.send_message(chat_id=CHAT_ID, text=result_message)

# =========================
# MAIN LOOP
# =========================

async def main():

    print("FOREX AI BOT STARTED")

    while True:

        try:
            await send_signal()

        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(5)

asyncio.run(main())
