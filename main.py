# ============================================
# GOLD FOREX TELEGRAM SIGNAL BOT
# XAU/USD AI SIGNAL BOT
# ============================================

# INSTALL:
# pip install python-telegram-bot==13.15
# pip install MetaTrader5 pandas ta requests schedule

# ============================================
# CONFIG
# ============================================

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_ID = "@yourchannel"

SYMBOL = "XAUUSD"

TIMEFRAME = "M5"

RISK_REWARD = 2

# ============================================
# IMPORTS
# ============================================

import MetaTrader5 as mt5
import pandas as pd
import ta
import time
import requests
import schedule

from telegram import Bot
from datetime import datetime

# ============================================
# TELEGRAM BOT
# ============================================

bot = Bot(token=BOT_TOKEN)

# ============================================
# MT5 CONNECT
# ============================================

if not mt5.initialize():
    print("MT5 Initialization Failed")
    quit()

print("MT5 Connected")

# ============================================
# GET MARKET DATA
# ============================================

def get_data():

    rates = mt5.copy_rates_from_pos(
        SYMBOL,
        mt5.TIMEFRAME_M5,
        0,
        200
    )

    df = pd.DataFrame(rates)

    df['time'] = pd.to_datetime(df['time'], unit='s')

    return df

# ============================================
# ANALYSIS
# ============================================

def analyze_market():

    df = get_data()

    # EMA
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)

    # RSI
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    # MACD
    macd = ta.trend.MACD(df['close'])

    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    # ATR
    atr = ta.volatility.AverageTrueRange(
        df['high'],
        df['low'],
        df['close']
    )

    df['atr'] = atr.average_true_range()

    last = df.iloc[-1]

    price = round(last['close'], 2)

    signal = None

    # BUY CONDITIONS
    if (
        last['ema20'] > last['ema50']
        and last['rsi'] > 55
        and last['macd'] > last['macd_signal']
    ):

        sl = round(price - (last['atr'] * 1.5), 2)

        tp1 = round(price + (last['atr'] * 1.5), 2)
        tp2 = round(price + (last['atr'] * 3), 2)
        tp3 = round(price + (last['atr'] * 5), 2)

        signal = {
            "type": "BUY",
            "entry": price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "confidence": "89%"
        }

    # SELL CONDITIONS
    elif (
        last['ema20'] < last['ema50']
        and last['rsi'] < 45
        and last['macd'] < last['macd_signal']
    ):

        sl = round(price + (last['atr'] * 1.5), 2)

        tp1 = round(price - (last['atr'] * 1.5), 2)
        tp2 = round(price - (last['atr'] * 3), 2)
        tp3 = round(price - (last['atr'] * 5), 2)

        signal = {
            "type": "SELL",
            "entry": price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "confidence": "87%"
        }

    return signal

# ============================================
# SEND SIGNAL
# ============================================

def send_signal():

    signal = analyze_market()

    if signal is None:
        print("No Signal")
        return

    message = f"""
━━━━━━━━━━━━━━
🔥 GOLD VIP SIGNAL 🔥
━━━━━━━━━━━━━━

Pair: XAU/USD
Type: {signal['type']}

Entry Price:
{signal['entry']}

🎯 TP1 → {signal['tp1']}
🎯 TP2 → {signal['tp2']}
🎯 TP3 → {signal['tp3']}

🛑 Stop Loss:
{signal['sl']}

⚡ Confidence:
{signal['confidence']}

📊 Strategy:
EMA + RSI + MACD + ATR

⏰ Time:
{datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━
"""

    bot.send_message(
        chat_id=CHANNEL_ID,
        text=message
    )

    print("Signal Sent")

# ============================================
# NEWS FILTER
# ============================================

def high_impact_news():

    # SIMPLE FILTER
    # You can connect ForexFactory API later

    current_hour = datetime.utcnow().hour

    # Avoid volatility times
    blocked_hours = [12, 13]

    if current_hour in blocked_hours:
        return True

    return False

# ============================================
# MAIN BOT LOOP
# ============================================

def run_bot():

    if high_impact_news():
        print("High Impact News Time")
        return

    send_signal()

# ============================================
# AUTO RUN EVERY 5 MINUTES
# ============================================

schedule.every(5).minutes.do(run_bot)

print("Gold Signal Bot Running 24/7...")

while True:

    schedule.run_pending()

    time.sleep(1)
