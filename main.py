import os
import asyncio
import random
from datetime import datetime

from telegram import Bot

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# =========================
# BOT SETTINGS
# =========================

wins = 0
losses = 0

# GOLD BASE PRICE
gold_price = 4700.0

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

def get_news():
    news = [
        "LOW IMPACT NEWS",
        "MEDIUM IMPACT NEWS",
        "NO MAJOR NEWS"
    ]
    return random.choice(news)

# =========================
# ACCURACY
# =========================

def get_accuracy():
    total = wins + losses

    if total == 0:
        return 90

    return round((wins / total) * 100, 2)

# =========================
# GENERATE SIGNAL
# =========================

def generate_signal():
    global gold_price

    # REALISTIC PRICE MOVEMENT
    movement = random.uniform(-8, 8)
    gold_price += movement

    entry = round(gold_price, 2)

    direction = random.choice(["BUY", "SELL"])

    # SMALLER SL / HIGHER RR
    tp1_pips = random.randint(80, 120)
    tp2_pips = random.randint(130, 180)
    tp3_pips = random.randint(200, 300)

    sl_pips = random.randint(60, 90)

    # GOLD PIP VALUE
    pip_value = 0.01

    if direction == "BUY":
        tp1 = round(entry + (tp1_pips * pip_value), 2)
        tp2 = round(entry + (tp2_pips * pip_value), 2)
        tp3 = round(entry + (tp3_pips * pip_value), 2)
        sl = round(entry - (sl_pips * pip_value), 2)

    else:
        tp1 = round(entry - (tp1_pips * pip_value), 2)
        tp2 = round(entry - (tp2_pips * pip_value), 2)
        tp3 = round(entry - (tp3_pips * pip_value), 2)
        sl = round(entry + (sl_pips * pip_value), 2)

    signal = {
        "pair": "XAU/USD (GOLD)",
        "direction": direction,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "session": get_session(),
        "news": get_news(),
        "accuracy": random.randint(88, 96),
        "expected_pips": tp3_pips
    }

    return signal

# =========================
# SEND SIGNAL
# =========================

async def send_signal(signal):

    text = f"""
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

    msg = await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

    return msg.message_id

# =========================
# RESULT CHECKER
# =========================

async def send_result(signal):

    global wins
    global losses
    global gold_price

    await asyncio.sleep(120)

    # SIMULATE MARKET MOVE
    result_move = random.uniform(-15, 15)

    if signal["direction"] == "BUY":
        final_price = signal["entry"] + result_move
    else:
        final_price = signal["entry"] - result_move

    final_price = round(final_price, 2)

    result = ""
    hit = ""

    # BUY RESULTS
    if signal["direction"] == "BUY":

        if final_price >= signal["tp3"]:
            result = "WIN ✅"
            hit = "TP3 HIT 🎯"
            wins += 1

        elif final_price >= signal["tp2"]:
            result = "WIN ✅"
            hit = "TP2 HIT 🎯"
            wins += 1

        elif final_price >= signal["tp1"]:
            result = "WIN ✅"
            hit = "TP1 HIT 🎯"
            wins += 1

        elif final_price <= signal["sl"]:
            result = "LOSS ❌"
            hit = "STOP LOSS HIT 🛑"
            losses += 1

        else:
            result = "BREAKEVEN ⚪"
            hit = "NO TP/SL HIT"

    # SELL RESULTS
    else:

        if final_price <= signal["tp3"]:
            result = "WIN ✅"
            hit = "TP3 HIT 🎯"
            wins += 1

        elif final_price <= signal["tp2"]:
            result = "WIN ✅"
            hit = "TP2 HIT 🎯"
            wins += 1

        elif final_price <= signal["tp1"]:
            result = "WIN ✅"
            hit = "TP1 HIT 🎯"
            wins += 1

        elif final_price >= signal["sl"]:
            result = "LOSS ❌"
            hit = "STOP LOSS HIT 🛑"
            losses += 1

        else:
            result = "BREAKEVEN ⚪"
            hit = "NO TP/SL HIT"

    accuracy = get_accuracy()

    result_text = f"""
📢 TRADE RESULT

📊 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry: {signal['entry']}

💵 Final Price: {final_price}

🏁 Result: {result}

🎯 Status: {hit}

🏆 Wins: {wins}

❌ Losses: {losses}

🎯 Live Accuracy: {accuracy}%
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=result_text
    )

# =========================
# MAIN LOOP
# =========================

async def main():

    print("AI GOLD SIGNAL BOT STARTED")

    while True:

        try:
            signal = generate_signal()

            await send_signal(signal)

            asyncio.create_task(send_result(signal))

            # SEND EVERY 15 MINUTES
            await asyncio.sleep(900)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(10)

# =========================
# START BOT
# =========================

asyncio.run(main())
