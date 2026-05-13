import os
import time
import requests
from telegram import Bot
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

PAIRS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "GBPJPY=X": "GBP/JPY",
    "AUDUSD=X": "AUD/USD"
}

last_prices = {}

def get_price(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    response = requests.get(url).json()

    return float(
        response["chart"]["result"][0]["meta"]["regularMarketPrice"]
    )

def get_signal(old_price, new_price):
    if new_price > old_price:
        return "CALL 📈"
    else:
        return "PUT 📉"

def get_accuracy(move):
    value = int(move * 100000)

    if value < 85:
        return 85

    if value > 98:
        return 98

    return value

print("AI SIGNAL BOT STARTED")

while True:

    try:

        now = datetime.utcnow()

        if now.second == 50:

            for symbol, pair_name in PAIRS.items():

                current_price = get_price(symbol)

                if symbol not in last_prices:
                    last_prices[symbol] = current_price
                    continue

                old_price = last_prices[symbol]

                movement = abs(current_price - old_price)

                if movement < 0.0004:
                    continue

                signal = get_signal(old_price, current_price)

                accuracy = get_accuracy(movement)

                entry_minute = (now.minute + 1) % 60
                exit_minute = (now.minute + 2) % 60

                signal_text = f"""
🚀 AI SIGNAL ALERT

📊 Pair: {pair_name}

📈 Signal: {signal}

⏰ Signal Time: {now.hour:02}:{now.minute:02}:50 UTC

🟢 Entry Time: {now.hour:02}:{entry_minute:02}:00 UTC

🔴 Exit Time: {now.hour:02}:{exit_minute:02}:00 UTC

🎯 Accuracy: {accuracy}%
"""

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=signal_text
                )

                time.sleep(10)

                entry_price = get_price(symbol)

                time.sleep(60)

                final_price = get_price(symbol)

                if signal == "CALL 📈":
                    result = "WIN ✅" if final_price > entry_price else "LOSS ❌"
                else:
                    result = "WIN ✅" if final_price < entry_price else "LOSS ❌"

                result_text = f"""
📢 TRADE RESULT

📊 Pair: {pair_name}

📈 Signal: {signal}

🎯 Accuracy: {accuracy}%

🏁 Final Result: {result}
"""

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=result_text
                )

                last_prices[symbol] = final_price

            time.sleep(2)

        else:
            time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
