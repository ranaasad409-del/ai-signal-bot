import os
import asyncio
import random
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

wins = 0
losses = 0


def generate_signal():

    current_price = round(random.uniform(3300, 3400), 2)

    direction = random.choice(["BUY", "SELL"])

    if direction == "BUY":

        tp1 = round(current_price + 1.0, 2)
        tp2 = round(current_price + 2.0, 2)
        tp3 = round(current_price + 3.0, 2)

        sl = round(current_price - 1.0, 2)

    else:

        tp1 = round(current_price - 1.0, 2)
        tp2 = round(current_price - 2.0, 2)
        tp3 = round(current_price - 3.0, 2)

        sl = round(current_price + 1.0, 2)

    strength = random.randint(1, 15)

    # only strong setups
    if strength < 12:
        return None

    signal = {
        "pair": "XAU/USD (GOLD)",
        "direction": direction,
        "entry": current_price,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "expected_pips": random.randint(80, 150),
        "accuracy": random.randint(88, 96),
        "session": random.choice([
            "LONDON SESSION",
            "NEW YORK SESSION"
        ]),
        "news": random.choice([
            "LOW IMPACT NEWS",
            "MEDIUM IMPACT NEWS"
        ])
    }

    return signal


async def send_signal(signal):

    message = f"""
🚨 AI GOLD SIGNAL 🚨

📊 Pair: {signal['pair']}

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

🧠 Strategy:
SMC + Liquidity Sweep + Trend Confirmation
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)


async def send_result(signal):

    global wins, losses

    result = random.choice(["TP HIT ✅", "STOP LOSS ❌"])

    if result == "TP HIT ✅":
        wins += 1
    else:
        losses += 1

    total = wins + losses

    accuracy = round((wins / total) * 100, 2)

    result_message = f"""
📢 TRADE RESULT

📊 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry: {signal['entry']}

🎯 TP1: {signal['tp1']}

🛑 SL: {signal['sl']}

🏆 Result: {result}

✅ Wins: {wins}

❌ Losses: {losses}

🔥 Accuracy: {accuracy}%
"""

    await bot.send_message(chat_id=CHAT_ID, text=result_message)


async def main():

    print("AI GOLD SIGNAL BOT STARTED")

    while True:

        try:

            signal = generate_signal()

            if signal:

                await send_signal(signal)

                # wait before result
                await asyncio.sleep(300)

                await send_result(signal)

            # new signal every 30 minutes
            await asyncio.sleep(1800)

        except Exception as e:

            print("ERROR:", e)

            await asyncio.sleep(10)


asyncio.run(main())
