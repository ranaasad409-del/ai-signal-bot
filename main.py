import time
import requests
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
# STATS
# =========================
wins = 0
losses = 0
total = 0

# =========================
# OTC PAIRS
# =========================
pairs = [
    "EUR/USD OTC",
    "USD/JPY OTC",
    "GBP/USD OTC",
    "EUR/JPY OTC",
    "AUD/USD OTC",
    "USD/CAD OTC",
    "EUR/GBP OTC"
]

# =========================
# LIVE PRICE FUNCTION
# =========================
def get_price(pair):

    try:

        symbol_map = {
            "EUR/USD OTC": "EURUSD=X",
            "USD/JPY OTC": "JPY=X",
            "GBP/USD OTC": "GBPUSD=X",
            "EUR/JPY OTC": "EURJPY=X",
            "AUD/USD OTC": "AUDUSD=X",
            "USD/CAD OTC": "CAD=X",
            "EUR/GBP OTC": "EURGBP=X"
        }

        symbol = symbol_map[pair]

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        data = response.json()

        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        return float(price)

    except Exception as e:

        print("PRICE ERROR:", e)

        return None

# =========================
# ACCURACY
# =========================
def accuracy():

    global wins, total

    if total == 0:
        return 0.00

    return round((wins / total) * 100, 2)

# =========================
# BOT START
# =========================
print("AI SIGNAL BOT STARTED")

while True:

    try:

        now = datetime.utcnow()

        # NEXT 1-MINUTE CANDLE
        next_candle = (
            now + timedelta(minutes=1)
        ).replace(second=0, microsecond=0)

        # SEND SIGNAL 15 SEC BEFORE
        signal_time = next_candle - timedelta(seconds=15)

        wait_signal = (
            signal_time - datetime.utcnow()
        ).total_seconds()

        if wait_signal > 0:
            time.sleep(wait_signal)

        pair = random.choice(pairs)

        direction = random.choice(["CALL", "PUT"])

        entry_price = get_price(pair)

        if entry_price is None:
            continue

        trade_end = next_candle + timedelta(minutes=1)

        # =========================
        # SIGNAL MESSAGE
        # =========================
        signal_message = f"""
🚀 AI SIGNAL ALERT

📊 Pair: {pair}

💰 Signal Price:
{entry_price}

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
        wait_entry = (
            next_candle - datetime.utcnow()
        ).total_seconds()

        if wait_entry > 0:
            time.sleep(wait_entry)

        # WAIT EXACT 1 MINUTE
        time.sleep(60)

        exit_price = get_price(pair)

        if exit_price is None:
            continue

        result = "LOSS ❌"

        # RESULT CHECK
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

        # =========================
        # RESULT MESSAGE
        # =========================
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
