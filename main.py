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

SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 150

# =========================
# TELEGRAM FUNCTION
# =========================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)

    except Exception as e:
        print("Telegram Error:", e)

# =========================
# GET MARKET DATA
# =========================

def get_data():

    url = (
        f"https://api.binance.com/api/v3/klines"
        f"?symbol={SYMBOL}"
        f"&interval={INTERVAL}"
        f"&limit={LIMIT}"
    )

    response = requests.get(url)

    data = response.json()

    # CHECK API RESPONSE

    if not isinstance(data, list):
        print("Invalid API response")
        return None

    # CREATE DATAFRAME

    df = pd.DataFrame(data, columns=[
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore"
    ])

    # CONVERT TO NUMBERS

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])

    return df

# =========================
# ANALYZE MARKET
# =========================

def analyze_market():

    df = get_data()

    if df is None:
        return

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

    macd = ta.trend.MACD(close=df["close"])

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
    # FINAL SIGNAL
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

        entry = round(close, 2)

        stop_loss = round(entry - 150, 2)

        take_profit = round(entry + 300, 2)

    elif signal == "SELL":

        entry = round(close, 2)

        stop_loss = round(entry + 150, 2)

        take_profit = round(entry - 300, 2)

    # =========================
    # SEND SIGNAL
    # =========================

    if signal:

        message = f"""
🔥 AI SNIPER SIGNAL 🔥

📊 Symbol: {SYMBOL}
📈 Signal: {signal}

🎯 Entry: {entry}

🛑 Stop Loss: {stop_loss}

💰 Take Profit: {take_profit}

📉 RSI: {round(rsi, 2)}

🕒 Time:
{datetime.now()}
"""

        print(message)

        send_telegram(message)

    else:

        print("No strong setup found")

# =========================
# MAIN LOOP
# =========================

print("AI SIGNAL BOT STARTED")

while True:

    try:

        analyze_market()

    except Exception as e:

        print("ERROR:", e)

    # CHECK EVERY 60 SECONDS

    time.sleep(60)
