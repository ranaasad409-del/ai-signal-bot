import time
import logging
import asyncio
import pandas as pd
import pandas_ta as ta
from telegram import Bot
from quotexpy import Quotex

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"      # Apna Token lagayein
CHAT_ID = "YOUR_PERSONAL_TELEGRAM_CHAT_ID"    # Apni Chat ID lagayein
QUOTEX_EMAIL = "your_email@gmail.com"          # Quotex Email
QUOTEX_PASSWORD = "your_password"              # Quotex Password

OTC_PAIRS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
# ---------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

tg_bot = Bot(token=TELEGRAM_TOKEN)
client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, root_path=".")

def connect_quotex():
    if not client.check_connect():
        logging.info("🔄 Quotex OTC Server se connect ho raha hai...")
        client.connect()
        logging.info("✅ Connected to Quotex Successfully!")

def analyze_market(candles):
    df = pd.DataFrame(candles)
    if df.empty or len(df) < 30:
        return None

    df['RSI'] = ta.rsi(df['close'], length=14)
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
    df['STOCHk'] = stoch['STOCHk_14_3_3']
    df['STOCHd'] = stoch['STOCHd_14_3_3']

    last_row = df.iloc[-1]
    rsi_val = last_row['RSI']
    stoch_k = last_row['STOCHk']
    stoch_d = last_row['STOCHd']

    if rsi_val < 30 and stoch_k < 20 and stoch_k > stoch_d:
        return "CALL 🟢 (Buy)"
    elif rsi_val > 70 and stoch_k > 80 and stoch_k < stoch_d:
        return "PUT 🔴 (Sell)"
    return None

async def send_telegram_signal(pair, direction):
    clean_pair_name = pair.replace('_otc', '').upper() + " (OTC)"
    message = (
        f"🎯 **QUOTEX OTC SIGNAL ALERT** 🎯\n\n"
        f"📊 **Market Pair:** {clean_pair_name}\n"
        f"⏰ **Timeframe:** 1 MINUTE\n"
        f"🚀 **Action Order:** {direction}\n"
        f"⏳ **Expiry Duration:** 1 MIN\n\n"
        f"⚠️ *Confirmation check kar k manual click karein.*"
    )
    try:
        await tg_bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logging.info(f"📡 Signal bhej diya: {pair} -> {direction}")
    except Exception as e:
        logging.error(f"❌ Telegram send failed: {e}")

def main():
    connect_quotex()
    logging.info("🤖 Bot active ho gaya hai. Waiting for signals...")
    
    last_signal_time = {pair: 0 for pair in OTC_PAIRS}

    while True:
        try:
            connect_quotex()
            for pair in OTC_PAIRS:
                current_time = time.time()
                if current_time - last_signal_time[pair] > 60:
                    candles = client.get_candles(pair, 60, 30) 
                    if candles:
                        signal = analyze_market(candles)
                        if signal:
                            asyncio.run(send_telegram_signal(pair, signal))
                            last_signal_time[pair] = current_time
            time.sleep(5)
        except Exception as e:
            logging.error(f"⚠️ Loop Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
