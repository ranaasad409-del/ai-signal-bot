import time
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Bot

# =======================
# TELEGRAM SETTINGS
# =======================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"
bot = Bot(token=BOT_TOKEN)

# =======================
# QUOTEX LOGIN
# =======================
QUOTEX_EMAIL = "supportquotex97@gmail.com"
QUOTEX_PASSWORD = "Allahbadsha409@"

# =======================
# OTC PAIRS (as displayed on chart)
# =======================
pairs = {
    "USD/PKR OTC": "USD/PKR",
    "USD/MXN OTC": "USD/MXN",
    "USD/BRL OTC": "USD/BRL"
}

# EMA SETTINGS
FAST_EMA = 5
SLOW_EMA = 20
SIGNAL_LEAD_TIME = 20
SLEEP_INTERVAL = 1

# Storage
active_trades = {}
price_history = {pair: [] for pair in pairs}

# Logging
def log_trade(message):
    print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {message}")
    with open("trade_log.txt", "a") as f:
        f.write(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {message}\n")

# EMA Calculation
def calculate_ema(prices, span):
    ema = []
    for i, price in enumerate(prices):
        if i == 0:
            ema.append(price)
        else:
            ema.append((price * (2 / (span + 1))) + (ema[-1] * (1 - 2 / (span + 1))))
    return ema

def generate_signal(prices):
    ema_fast = calculate_ema(prices, FAST_EMA)
    ema_slow = calculate_ema(prices, SLOW_EMA)
    if ema_fast[-2] < ema_slow[-2] and ema_fast[-1] > ema_slow[-1]:
        return "BUY"
    elif ema_fast[-2] > ema_slow[-2] and ema_fast[-1] < ema_slow[-1]:
        return "SELL"
    return None

# =======================
# Initialize Selenium WebDriver
# =======================
chrome_options = Options()
chrome_options.add_argument("--headless")  # run headless for cloud
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# Log in to Quotex
driver.get("https://quotex.io/")
time.sleep(5)
# Add your login automation here if needed

log_trade("🚀 Selenium initialized, Quotex page opened")

# =======================
# Fetch latest price from chart
# =======================
def fetch_latest_price(pair_name):
    try:
        # Locate the price element for the pair (you need to inspect actual chart element)
        price_element = driver.find_element(By.XPATH, f"//div[contains(text(), '{pairs[pair_name]}')]/following-sibling::div")
        price_text = price_element.text.replace(",", "")
        return float(price_text)
    except Exception as e:
        log_trade(f"Error fetching price for {pair_name}: {e}")
        # fallback to last price or dummy
        if price_history[pair_name]:
            return price_history[pair_name][-1]
        return 100.0

# =======================
# Main Loop
# =======================
log_trade("🚀 OTC Sniper Bot Started")

while True:
    now = datetime.utcnow()
    seconds_to_next_candle = 60 - now.second

    for pair_name in pairs:
        price = fetch_latest_price(pair_name)
        price_history[pair_name].append(price)
        if len(price_history[pair_name]) > 50:
            price_history[pair_name] = price_history[pair_name][-50:]

        # Send sniper signal 20 sec before candle
        if seconds_to_next_candle <= SIGNAL_LEAD_TIME:
            if pair_name not in active_trades:
                signal = generate_signal(price_history[pair_name])
                if signal:
                    candle_open_time = (now + timedelta(seconds=seconds_to_next_candle)).replace(microsecond=0)
                    entry_price = price
                    active_trades[pair_name] = {"signal": signal, "candle_open_time": candle_open_time, "entry": entry_price}

                    msg = f"📊 {pair_name} OTC Signal\nSignal: {signal}\nCandle Opens: {candle_open_time.strftime('%H:%M:%S')} UTC\nEntry Price: {entry_price:.4f}"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    log_trade(msg)

        # Check result after 1 minute
        if pair_name in active_trades:
            trade = active_trades[pair_name]
            if now >= trade["candle_open_time"] + timedelta(seconds=60):
                close_price = price
                win = (trade["signal"]=="BUY" and close_price > trade["entry"]) or (trade["signal"]=="SELL" and close_price < trade["entry"])
                result = "WIN ✅" if win else "LOSS ❌"

                msg = f"📈 {pair_name} Trade Result\nSignal: {trade['signal']}\nEntry: {trade['entry']:.4f}\nClose: {close_price:.4f}\nResult: {result}\nTime: {now.strftime('%H:%M:%S')} UTC"
                bot.send_message(chat_id=CHAT_ID, text=msg)
                log_trade(msg)

                del active_trades[pair_name]

    time.sleep(SLEEP_INTERVAL)
