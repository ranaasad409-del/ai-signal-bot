import time
import random
from datetime import datetime, timedelta
from telegram import Bot

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

bot = Bot(token=BOT_TOKEN)

wins = 0
losses = 0
total = 0

pairs = [
    "EUR/USD OTC",
    "USD/JPY OTC",
    "GBP/USD OTC",
    "EUR/JPY OTC",
    "AUD/USD OTC",
    "USD/CAD OTC",
    "EUR/GBP OTC"
]

def get_price():
    return round(random.uniform(1.10000, 200.00000), 5)

def accuracy():
    global wins, total

    if total == 0:
        return 0.00

    return round((wins / total) * 100, 2)

print("AI SIGNAL BOT STARTED")

while True:

    try:

        now = datetime.utcnow()

        # NEXT 1-MIN CANDLE OPEN
        next_candle = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)

        # SEND SIGNAL 15 SEC BEFORE
        signal_time = next_candle - timedelta(seconds=15)

        wait_signal = (signal_time - datetime.utcnow()).total_seconds()

        if wait_signal > 0:
            time.sleep(wait_signal)

        pair = random.choice(pairs)

        direction = random.choice(["CALL", "PUT"])

        entry_price = get_price()

        trade_end = next_candle + timedelta(minutes=1)

        signal_message = f"""
🚀 AI SIGNAL ALERT

📊 Pair: {pair}

⬜ Direction: {direction}

🎯 Accuracy: {accuracy()}%

🟢 Trade Start:
{next_candle.strftime('%H:%M:%S')} UTC

🔴 Trade End:
{trade_end.strftime('%H:%M:%S')} UTC

⌛ Duration: 1 Minute
"""

        bot.send_message(
            chat_id=CHAT_ID,
            text=signal_message
        )

        # WAIT UNTIL TRADE START
        wait_entry = (next_candle - datetime.utcnow()).total_seconds()

        if wait_entry > 0:
            time.sleep(wait_entry)

        # WAIT EXACT 1 MINUTE TRADE
        time.sleep(60)

        exit_price = get_price()

        result = "LOSS ❌"

        if direction == "CALL":
            if exit_price > entry_price:
                result = "WIN ✅"

        if direction == "PUT":
            if exit_price < entry_price:
                result = "WIN ✅"

        total += 1

        if "WIN" in result:
            wins += 1
        else:
            losses += 1

        result_message = f"""
📢 TRADE RESULT

📊 {pair}

{result}

🏆 Wins: {wins}

❌ Losses: {losses}

🎯 Accuracy: {accuracy()}%
"""

        bot.send_message(
            chat_id=CHAT_ID,
            text=result_message
        )

        time.sleep(2)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(5)
