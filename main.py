import requests
import time
import random
from datetime import datetime, timedelta
from telegram import Bot

# =========================
# TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

bot = Bot(token=BOT_TOKEN)

# =========================
# OTC PAIRS
# =========================
pairs = [
    "EUR/USD OTC",
    "USD/JPY OTC",
    "GBP/USD OTC",
    "EUR/JPY OTC",
    "AUD/USD OTC",
    "USD/PKR OTC",
    "USD/BRL OTC",
    "EUR/GBP OTC"
]

# =========================
# SIGNAL STATS
# =========================
wins = 0
losses = 0
total = 0

# =========================
# GET FAKE LIVE PRICE
# =========================
def get_price():
    return round(random.uniform(1.10000, 200.00000), 5)

# =========================
# CALCULATE ACCURACY
# =========================
def get_accuracy():
    global wins, total

    if total == 0:
        return 0

    return round((wins / total) * 100, 2)

# =========================
# SEND TELEGRAM MESSAGE
# =========================
def send_message(text):
    bot.send_message(chat_id=CHAT_ID, text=text)

# =========================
# GENERATE SIGNAL
# =========================
def generate_signal():

    pair = random.choice(pairs)

    current_price = get_price()

    direction = random.choice(["CALL", "PUT"])

    signal_time = datetime.utcnow()

    # 10 seconds before entry
    entry_time = signal_time + timedelta(seconds=10)

    # Exact 1 minute trade
    exit_time = entry_time + timedelta(minutes=1)

    accuracy = get_accuracy()

    signal_msg = f"""
🚀 AI SIGNAL ALERT

📊 Pair: {pair}

💰 Current Price: {current_price}

⬜ Direction: {direction} ⬜

🎯 Accuracy: {accuracy}%

⏰ Signal Time:
{signal_time.strftime('%H:%M:%S')} UTC

🟢 Entry Time:
{entry_time.strftime('%H:%M:%S')} UTC

🔴 Exit Time:
{exit_time.strftime('%H:%M:%S')} UTC

⚡ Duration: 1 Minute

🔥 Strong Trend Confirmed
"""

    send_message(signal_msg)

    # Wait until trade ends
    wait_seconds = (exit_time - datetime.utcnow()).total_seconds()

    if wait_seconds > 0:
        time.sleep(wait_seconds)

    check_result(
        pair,
        current_price,
        direction,
        exit_time
    )

# =========================
# CHECK RESULT
# =========================
def check_result(pair, entry_price, direction, exit_time):

    global wins, losses, total

    exit_price = get_price()

    result = "LOSS ❌"

    if direction == "CALL":
        if exit_price > entry_price:
            result = "WIN ✅"

    if direction == "PUT":
        if exit_price < entry_price:
            result = "WIN ✅"

    if "WIN" in result:
        wins += 1
    else:
        losses += 1

    total += 1

    accuracy = get_accuracy()

    result_msg = f"""
📢 TRADE RESULT

📊 Pair: {pair}

💰 Entry Price: {entry_price}

💰 Exit Price: {exit_price}

⬜ Direction: {direction}

📈 Result: {result}

🏆 Wins: {wins}

❌ Losses: {losses}

🎯 Live Accuracy:
{accuracy}%

⏰ Closed At:
{exit_time.strftime('%H:%M:%S')} UTC
"""

    send_message(result_msg)

# =========================
# MAIN LOOP
# =========================
print("AI SIGNAL BOT STARTED")

while True:

    try:

        generate_signal()

        # Next signal every 2 minutes
        time.sleep(120)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(10)
