import requests
import time
import traceback
import re

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"   # <-- manually write your bot token
CHAT_ID   = "5974354691"     # <-- manually write your chat id

# =========================
# SETTINGS
# =========================
SIGNAL_INTERVAL = 300  # seconds (5 min)
TP_OFFSET = 5          # USD
SL_OFFSET = 5          # USD
MOVING_AVERAGE_PERIOD = 5  # short-term SMA for trend
PRICE_THRESHOLD = 2        # minimum price change to send new signal

# =========================
# STORAGE
# =========================
last_signal = None
price_history = []

# =========================
# SEND TELEGRAM MESSAGE
# =========================
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        response = requests.post(url, data=payload)
        print("Telegram Response:", response.text)
    except Exception as e:
        print("Telegram Error:", e)
        traceback.print_exc()

# =========================
# GET LIVE GOLD PRICE (TradingView)
# =========================
def get_gold_price():
    try:
        url = "https://www.tradingview.com/symbols/XAUUSD/?exchange=FOREX"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        data = response.text
        match = re.search(r'"price":([\d.]+),', data)
        if match:
            price = float(match.group(1))
            print("Live Gold Price:", price)
            return price
        else:
            return 3360.0  # fallback
    except Exception as e:
        print("Error fetching gold price:", e)
        return 3360.0

# =========================
# DETERMINE TREND
# =========================
def determine_trend():
    if len(price_history) < MOVING_AVERAGE_PERIOD:
        return None
    sma = sum(price_history[-MOVING_AVERAGE_PERIOD:]) / MOVING_AVERAGE_PERIOD
    current_price = price_history[-1]
    if current_price > sma:
        return "BUY"
    elif current_price < sma:
        return "SELL"
    return None

# =========================
# GENERATE SIGNAL
# =========================
def generate_signal():
    global last_signal

    price = get_gold_price()
    price_history.append(price)

    signal = determine_trend()
    if signal is None:
        print("Trend unclear, no signal.")
        return None

    entry = round(price, 2)
    tp = round(entry + TP_OFFSET, 2) if signal == "BUY" else round(entry - TP_OFFSET, 2)
    sl = round(entry - SL_OFFSET, 2) if signal == "BUY" else round(entry + SL_OFFSET, 2)

    current_signal = (signal, entry, tp, sl)

    # Prevent redundant signals
    if last_signal:
        last_signal_signal, last_entry, _, _ = last_signal
        if signal == last_signal_signal and abs(entry - last_entry) < PRICE_THRESHOLD:
            print("Signal too similar to last, skipping...")
            return last_signal

    # Send new signal
    message = f"""
🔥 AI GOLD SIGNAL

📈 {signal} XAUUSD

💰 Entry : {entry}
🎯 TP     : {tp}
🛑 SL     : {sl}
"""
    send_telegram_message(message)
    last_signal = current_signal
    return current_signal

# =========================
# CHECK TP / SL HIT
# =========================
def check_tp_sl_hit(signal_info):
    if signal_info is None:
        return False
    signal, entry, tp, sl = signal_info
    price = get_gold_price()

    if signal == "BUY":
        if price >= tp:
            send_telegram_message(f"✅ BUY TP HIT at {price}")
            return True
        elif price <= sl:
            send_telegram_message(f"❌ BUY SL HIT at {price}")
            return True
    elif signal == "SELL":
        if price <= tp:
            send_telegram_message(f"✅ SELL TP HIT at {price}")
            return True
        elif price >= sl:
            send_telegram_message(f"❌ SELL SL HIT at {price}")
            return True
    return False

# =========================
# MAIN LOOP
# =========================
print("AI GOLD SIGNAL BOT STARTED")

current_signal_info = None

while True:
    try:
        print("Checking market and generating signal...")
        current_signal_info = generate_signal() or current_signal_info
        if current_signal_info:
            hit = check_tp_sl_hit(current_signal_info)
            if hit:
                current_signal_info = None  # reset after TP/SL
    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        traceback.print_exc()

    time.sleep(SIGNAL_INTERVAL)
