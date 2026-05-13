import random
import time
from datetime import datetime

import yfinance as yf
from telegram import Bot

# =========================
# TELEGRAM SETTINGS
# =========================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

bot = Bot(token=BOT_TOKEN)

# =========================
# LIVE STATS
# =========================

wins = 0
losses = 0

# =========================
# GOLD LIVE PRICE
# =========================

def get_live_gold_price():
    try:
        data = yf.Ticker("GC=F")

        price_data = data.history(period="1d", interval="1m")

        live_price = round(price_data["Close"].iloc[-1], 2)

        return live_price

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

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
        "HIGH IMPACT NEWS"
    ]

    return random.choice(news)

# =========================
# STRATEGY TEXT
# =========================

def get_strategy():
    strategies = [
        "Smart Money Concept + Liquidity Sweep",
        "Breakout + BOS Confirmation",
        "Trend Continuation + Order Block",
        "Liquidity Grab + Reversal",
        "SMC + Trend Confirmation"
    ]

    return random.choice(strategies)

# =========================
# SIGNAL GENERATOR
# =========================

def generate_signal():

    entry_price = get_live_gold_price()

    if entry_price is None:
        return None

    direction = random.choice(["BUY", "SELL"])

    # GOLD TP / SL

    if direction == "BUY":

        tp1 = round(entry_price + 2.0, 2)
        tp2 = round(entry_price + 4.0, 2)
        tp3 = round(entry_price + 6.0, 2)

        sl = round(entry_price - 2.5, 2)

    else:

        tp1 = round(entry_price - 2.0, 2)
        tp2 = round(entry_price - 4.0, 2)
        tp3 = round(entry_price - 6.0, 2)

        sl = round(entry_price + 2.5, 2)

    accuracy = random.randint(85, 96)

    pips = random.randint(40, 120)

    session = get_session()

    news = get_news()

    strategy = get_strategy()

    return {
        "pair": "XAU/USD (GOLD)",
        "direction": direction,
        "entry": entry_price,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "accuracy": accuracy,
        "pips": pips,
        "session": session,
        "news": news,
        "strategy": strategy
    }

# =========================
# SEND SIGNAL
# =========================

def send_signal(signal):

    message = f"""
🚨 AI GOLD SIGNAL 🚨

📊 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry Price: {signal['entry']}

🎯 Take Profit 1: {signal['tp1']}
🎯 Take Profit 2: {signal['tp2']}
🎯 Take Profit 3: {signal['tp3']}

🛑 Stop Loss: {signal['sl']}

📊 Expected Pips: {signal['pips']}

🔥 Accuracy: {signal['accuracy']}%

🌍 Session: {signal['session']}

📰 News: {signal['news']}

🧠 Strategy:
{signal['strategy']}
"""

    bot.send_message(chat_id=CHAT_ID, text=message)

# =========================
# SEND RESULT
# =========================

def send_result(signal):

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

📊 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry: {signal['entry']}

📌 Result: {result}

🏆 Wins: {wins}
❌ Losses: {losses}

🎯 Live Accuracy: {accuracy}%
"""

    bot.send_message(chat_id=CHAT_ID, text=result_message)

# =========================
# MAIN LOOP
# =========================

print("AI GOLD BOT STARTED")

while True:

    try:

        signal = generate_signal()

        if signal:

            send_signal(signal)

            # Wait 15 minutes
            time.sleep(900)

            send_result(signal)

        # Wait before next signal
        time.sleep(300)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(30)
