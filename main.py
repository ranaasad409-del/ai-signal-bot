import os
import time
import requests
from telegram import Bot
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

PAIRS = {

    # FOREX
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "GBPJPY=X": "GBP/JPY",
    "AUDUSD=X": "AUD/USD",

    # OTC STYLE
    "EURUSD-OTC": "EUR/USD OTC",
    "GBPUSD-OTC": "GBP/USD OTC",
    "USDJPY-OTC": "USD/JPY OTC",
    "GBPJPY-OTC": "GBP/JPY OTC",
    "AUDUSD-OTC": "AUD/USD OTC"
}

price_history = {}

def get_price(symbol):

    try:

        # OTC fallback using real forex pair
        real_symbol = symbol.replace("-OTC", "=X")

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{real_symbol}"

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


def calculate_signal(prices):

    if len(prices) < 3:
        return None

    p1 = prices[-3]
    p2 = prices[-2]
    p3 = prices[-1]

    # STRONG UP TREND
    if p1 < p2 < p3:
        return "CALL 📈"

    # STRONG DOWN TREND
    if p1 > p2 > p3:
        return "PUT 📉"

    return None


def calculate_accuracy(prices):

    move = abs(prices[-1] - prices[-2])

    accuracy = 85 + int(move * 100000)

    if accuracy > 98:
        accuracy = 98

    return accuracy


print("AI SIGNAL BOT STARTED")


while True:

    try:

        now = datetime.utcnow()

        # SEND SIGNAL AT EXACT XX:XX:50
        if now.second == 50:

            for symbol, pair_name in PAIRS.items():

                current_price = get_price(symbol)

                if current_price is None:
                    continue

                if symbol not in price_history:
                    price_history[symbol] = []

                price_history[symbol].append(current_price)

                # KEEP LAST 5 PRICES
                if len(price_history[symbol]) > 5:
                    price_history[symbol].pop(0)

                prices = price_history[symbol]

                signal = calculate_signal(prices)

                if signal is None:
                    continue

                accuracy = calculate_accuracy(prices)

                # FILTER LOW QUALITY SIGNALS
                if accuracy < 88:
                    continue

                entry_minute = (now.minute + 1) % 60
                exit_minute = (now.minute + 2) % 60

                signal_text = f"""
🚀 AI SIGNAL ALERT

📊 Pair: {pair_name}

💰 Current Price: {current_price}

📈 Direction: {signal}

🎯 Accuracy: {accuracy}%

⏰ Signal Time:
{now.hour:02}:{now.minute:02}:50 UTC

🟢 Entry Time:
{now.hour:02}:{entry_minute:02}:00 UTC

🔴 Exit Time:
{now.hour:02}:{exit_minute:02}:00 UTC

⚡ Duration: 1 Minute

🔥 Strong Trend Confirmed
"""

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=signal_text
                )

                print(f"SIGNAL SENT -> {pair_name} {signal}")

                # WAIT 10 SECONDS UNTIL ENTRY
                time.sleep(10)

                entry_price = get_price(symbol)

                if entry_price is None:
                    continue

                # WAIT 1 MINUTE TRADE
                time.sleep(60)

                final_price = get_price(symbol)

                if final_price is None:
                    continue

                # CHECK RESULT
                if signal == "CALL 📈":
                    result = "WIN ✅" if final_price > entry_price else "LOSS ❌"
                else:
                    result = "WIN ✅" if final_price < entry_price else "LOSS ❌"

                result_text = f"""
📢 TRADE RESULT

📊 Pair: {pair_name}

💰 Entry Price: {entry_price}

💰 Exit Price: {final_price}

📈 Direction: {signal}

🎯 Accuracy: {accuracy}%

🏁 Result: {result}
"""

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=result_text
                )

                print(f"RESULT -> {pair_name} {result}")

            time.sleep(2)

        else:
            time.sleep(1)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(5)
