import time
import requests
import pandas as pd
import ta
from datetime import datetime

# =========================
# TELEGRAM SETTINGS
# =========================

BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =========================
# MARKET SETTINGS
# =========================

SYMBOL = "XAUUSD"
TIMEFRAME = "1m"

# =========================
# TELEGRAM FUNCTION
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# =========================
# GET MARKET DATA
# =========================

def get_data():

    # Example Binance Gold Proxy
    url = "https://api.binance.com/api/v3/klines?symbol=XAUUSDT&interval=1m&limit=150"

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    df = df.iloc[:, :6]

    df.columns = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

# =========================
# MAIN STRATEGY
# =========================

def analyze_market():

    df = get_data()

    # =========================
    # INDICATORS
    # =========================

    df["ema20"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    df["rsi"] = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    macd = ta.trend.MACD(df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    # =========================
    # LATEST CANDLE
    # =========================

    latest = df.iloc[-1]

    close = latest["close"]

    ema20 = latest["ema20"]
    ema50 = latest["ema50"]

    rsi = latest["rsi"]

    macd_value = latest["macd"]
    macd_signal = latest["macd_signal"]

    # =========================
    # BUY SCORE
    # =========================

    buy_score = 0

    if ema20 > ema50:
        buy_score += 1

    if rsi > 50:
        buy_score += 1

    if macd_value > macd_signal:
        buy_score += 1

    if close > ema20:
        buy_score += 1

    # =========================
    # SELL SCORE
    # =========================

    sell_score = 0

    if ema20 < ema50:
        sell_score += 1

    if rsi < 50:
        sell_score += 1

    if macd_value < macd_signal:
        sell_score += 1

    if close < ema20:
        sell_score += 1

    # =========================
    # SIGNAL GENERATION
    # =========================

    signal = None

    if buy_score >= 3:
        signal = "BUY"

    elif sell_score >= 3:
        signal = "SELL"

    # =========================
    # TP & SL
    # =========================

    if signal == "BUY":

        entry = close
        stop_loss = round(entry - 5, 2)
        take_profit = round(entry + 10, 2)

    elif signal == "SELL":

        entry = close
        stop_loss = round(entry + 5, 2)
        take_profit = round(entry - 10, 2)

    # =========================
    # SEND SIGNAL
    # =========================

    if signal:

        message = f"""
🔥 AI GOLD SNIPER SIGNAL 🔥

📊 Symbol: {SYMBOL}
📈 Signal: {signal}

🎯 Entry: {entry}
🛑 Stop Loss: {stop_loss}
💰 Take Profit: {take_profit}

📉 RSI: {round(rsi,2)}

🕒 Time:
{datetime.now()}
"""

        print(message)

        send_telegram(message)

    else:
        print("No strong setup found")

# =========================
# BOT LOOP
# =========================

print("AI GOLD BOT STARTED")

while True:

    try:

        analyze_market()

    except Exception as e:

        print("ERROR:", e)

    time.sleep(60)
