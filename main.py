import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import pandas as pd
from playwright.async_api import async_playwright
import random

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
# OTC PAIRS
# =======================
pairs = {
    "USD/PKR OTC": "USD/PKR",
    "USD/MXN OTC": "USD/MXN",
    "USD/BRL OTC": "USD/BRL"
}

FAST_EMA = 5
SLOW_EMA = 20
SIGNAL_LEAD_TIME = 20
SLEEP_INTERVAL = 1

active_trades = {}
price_history = {pair: [] for pair in pairs}

# =======================
# EMA Calculation
# =======================
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
# Logging
# =======================
def log_trade(msg):
    print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {msg}")
    with open("trade_log.txt", "a") as f:
        f.write(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {msg}\n")

# =======================
# Fetch latest price from Quotex chart
# =======================
async def fetch_latest_price(page, pair_name):
    try:
        # Replace this selector with the actual chart price element
        selector = f"div:has-text('{pairs[pair_name]}') + div"
        element = await page.query_selector(selector)
        text = await element.text_content()
        price = float(text.replace(",", ""))
        return price
    except:
        # fallback
        if price_history[pair_name]:
            last = price_history[pair_name][-1]
            return last + random.uniform(-0.1,0.1)
        return 100.0

# =======================
# Main Bot
# =======================
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://quotex.io/")
        await asyncio.sleep(5)
        # Add login automation if needed
        log_trade("🚀 Playwright initialized, Quotex page opened")

        while True:
            now = datetime.utcnow()
            seconds_to_next_candle = 60 - now.second
            for pair_name in pairs:
                price = await fetch_latest_price(page, pair_name)
                price_history[pair_name].append(price)
                if len(price_history[pair_name]) > 50:
                    price_history[pair_name] = price_history[pair_name][-50:]

                # Send sniper signal
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

                # Check trade result after candle closes
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

            await asyncio.sleep(SLEEP_INTERVAL)

asyncio.run(main())
