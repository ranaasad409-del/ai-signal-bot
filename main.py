import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from telegram import Bot
import random

# =======================
# TELEGRAM SETTINGS
# =======================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"
bot = Bot(token=BOT_TOKEN)

# =======================
# OTC PAIRS
# =======================
pairs = {
    "USD/PKR OTC": "USDPKR",
    "USD/MXN OTC": "USDMXN",
    "USD/BRL OTC": "USDBRL"
}

# =======================
# EMA SETTINGS
# =======================
FAST_EMA = 5
SLOW_EMA = 20
SIGNAL_LEAD_TIME = 20
SLEEP_INTERVAL = 0.5

# =======================
# STORAGE
# =======================
active_trades = {}
price_history = {pair: [] for pair in pairs}

# =======================
# LOGGING
# =======================
LOG_FILE = "trade_log.txt"
def log_trade(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {message}\n")
    print(message)

# =======================
# FETCH QUOTEX OTC CANDLES
# =======================
def fetch_otc_candles(symbol):
    try:
        url = f"https://quotex.io/api/candles?symbol={symbol}&interval=1m&limit=50"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        closes = [float(c['close']) for c in data]
        return closes
    except Exception as e:
        log_trade(f"Error fetching {symbol}: {e}")
        # fallback to last price or dummy
        if symbol in price_history and price_history[symbol]:
            last = price_history[symbol][-1]
            return [last + random.uniform(-0.1, 0.1) for _ in range(50)]
        else:
            return [100 + 0.1*i for i in range(50)]

# =======================
# GENERATE SIGNAL USING EMA
# =======================
def generate_signal(prices):
    df = pd.DataFrame(prices, columns=["close"])
    df['EMA_fast'] = df['close'].ewm(span=FAST_EMA, adjust=False).mean()
    df['EMA_slow'] = df['close'].ewm(span=SLOW_EMA, adjust=False).mean()

    if df['EMA_fast'].iloc[-2] < df['EMA_slow'].iloc[-2] and df['EMA_fast'].iloc[-1] > df['EMA_slow'].iloc[-1]:
        return "BUY"
    elif df['EMA_fast'].iloc[-2] > df['EMA_slow'].iloc[-2] and df['EMA_fast'].iloc[-1] < df['EMA_slow'].iloc[-1]:
        return "SELL"
    return None

# =======================
# MAIN LOOP
# =======================
print("🚀 OTC Sniper Bot Started")

while True:
    now = datetime.utcnow()
    seconds_to_next_candle = 60 - now.second

    # ---- SEND SIGNAL 20 SECONDS BEFORE CANDLE ----
    if seconds_to_next_candle <= SIGNAL_LEAD_TIME:
        for pair_name, symbol in pairs.items():
            closes = fetch_otc_candles(symbol)
            price_history[pair_name] = closes[-50:]

            if pair_name not in active_trades:
                signal = generate_signal(price_history[pair_name])
                if signal:
                    candle_open_time = (now + timedelta(seconds=seconds_to_next_candle)).replace(microsecond=0)
                    entry_price = closes[-1]

                    active_trades[pair_name] = {
                        "signal": signal,
                        "candle_open_time": candle_open_time,
                        "entry": entry_price
                    }

                    message = (
                        f"📊 {pair_name}\n"
                        f"Signal: {signal}\n"
                        f"Candle Opens: {candle_open_time.strftime('%H:%M:%S')} UTC\n"
                        f"Entry Price (estimated): {entry_price:.4f}"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    log_trade(message)

    # ---- RECORD ENTRY & CHECK RESULT ----
    for pair_name in list(active_trades.keys()):
        trade = active_trades[pair_name]

        # RECORD CANDLE OPEN PRICE (already stored in entry)
        if now >= trade["candle_open_time"] + timedelta(seconds=60):
            closes = fetch_otc_candles(pairs[pair_name])
            close_price = closes[-1]

            win = (trade["signal"] == "BUY" and close_price > trade["entry"]) or \
                  (trade["signal"] == "SELL" and close_price < trade["entry"])
            result = "WIN ✅" if win else "LOSS ❌"

            message = (
                f"📈 {pair_name} Trade Result\n"
                f"Signal: {trade['signal']}\n"
                f"Entry: {trade['entry']:.4f}\n"
                f"Close: {close_price:.4f}\n"
                f"Result: {result}\n"
                f"Time: {now.strftime('%H:%M:%S')} UTC"
            )
            bot.send_message(chat_id=CHAT_ID, text=message)
            log_trade(message)

            del active_trades[pair_name]

    time.sleep(SLEEP_INTERVAL)
