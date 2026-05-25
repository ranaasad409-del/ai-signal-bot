import subprocess
import sys
import time
import logging
import asyncio
import pandas as pd

# --- SERVER BREAKOUT JUGAR ---
# Agar Railway server requirements file se library nahi utha pa raha, 
# to ye code script chalte hi khud background me library install kar lega.
try:
    from quotexpy import Quotex
except ImportError:
    print("📦 Installing Quotexpy background me...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/nand0st/quotexpy.git"])
    from quotexpy import Quotex

try:
    import pandas_ta as ta
except ImportError:
    print("📦 Installing Pandas-TA background me...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas-ta"])
    import pandas_ta as ta

from telegram import Bot

# --- CONFIGURATION (Apne Data Se Badlein) ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"      # Apne bot ka Token yahan dalein
CHAT_ID = "YOUR_PERSONAL_TELEGRAM_CHAT_ID"    # Apni numeric Telegram Chat ID dalein
QUOTEX_EMAIL = "your_email@gmail.com"          # Quotex ka Email
QUOTEX_PASSWORD = "your_password"              # Quotex ka Password

# Jin pairs par aap signals chahte hain (OTC Markets)
OTC_PAIRS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
# ---------------------------------------------

# Logging configuration (Errors track karne k liye)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram Bot aur Quotex Connection setup
tg_bot = Bot(token=TELEGRAM_TOKEN)
client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, root_path=".")

def connect_quotex():
    """Quotex server se secure connection banana"""
    if not client.check_connect():
        logging.info("🔄 Quotex OTC Live Chart Server se connect ho raha hai...")
        client.connect()
        logging.info("✅ Connected to Quotex Successfully!")

def analyze_market(candles):
    """
    1-Minute Candles ko analyze kar k Low-Error Signal nikalna
    """
    df = pd.DataFrame(candles)
    
    if df.empty or len(df) < 30:
        return None

    # Technical Indicators Calculations
    df['RSI'] = ta.rsi(df['close'], length=14)
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
    df['STOCHk'] = stoch['STOCHk_14_3_3']
    df['STOCHd'] = stoch['STOCHd_14_3_3']

    # Aakhri completed candle ki values
    last_row = df.iloc[-1]
    rsi_val = last_row['RSI']
    stoch_k = last_row['STOCHk']
    stoch_d = last_row['STOCHd']

    # --- 1-MIN REVERSAL STRATEGY (LOW ERROR) ---
    # 🟢 CALL (BUY) SIGNAL: Market oversold ho chuki ho aur bounce back kare
    if rsi_val < 30 and stoch_k < 20 and stoch_k > stoch_d:
        return "CALL 🟢 (Buy)"

    # 🔴 PUT (SELL) SIGNAL: Market overbought ho chuki ho aur niche mure
    elif rsi_val > 70 and stoch_k > 80 and stoch_k < stoch_d:
        return "PUT 🔴 (Sell)"

    return None

async def send_telegram_signal(pair, direction):
    """Telegram par clean signal notification alert bhejna"""
    clean_pair_name = pair.replace('_otc', '').upper() + " (OTC)"
    message = (
        f"🎯 **QUOTEX OTC SIGNAL ALERT** 🎯\n\n"
        f"📊 **Market Pair:** {clean_pair_name}\n"
        f"⏰ **Timeframe:** 1 MINUTE\n"
        f"🚀 **Action Order:** {direction}\n"
        f"⏳ **Expiry Duration:** 1 MIN\n\n"
        f"⚠️ *Ankh band kar k trade na lagayein, Quotex screen par confirmation check kar k manual click karein.*"
    )
    try:
        await tg_bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logging.info(f"📡 Signal sent for {pair}: {direction}")
    except Exception as e:
        logging.error(f"❌ Telegram notification failed: {e}")

def main():
    connect_quotex()
    logging.info("🤖 Bot active ho gaya hai. Market analysis start... Waiting for signals.")
    
    # Her pair k aakhri signal ka record takay baar baar message spam na ho
    last_signal_time = {pair: 0 for pair in OTC_PAIRS}

    while True:
        try:
            connect_quotex() # Connection active rakhne k liye loop me check
            
            for pair in OTC_PAIRS:
                current_time = time.time()
                
                # Har 1 minute (60 seconds) k baad candle refresh hogi
                if current_time - last_signal_time[pair] > 60:
                    # Quotex se live 1-min candles data fetch karna (Timeframe 60s, Candles 30)
                    candles = client.get_candles(pair, 60, 30) 
                    
                    if candles:
                        signal = analyze_market(candles)
                        
                        if signal:
                            # Asyncio event loop k zariye telegram message bhejna
                            asyncio.run(send_telegram_signal(pair, signal))
                            last_signal_time[pair] = current_time # Cool-down multiplier
                            
            time.sleep(5) # Har 5 second baad pairs rotation check
            
        except Exception as e:
            logging.error(f"⚠️ Main Loop Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
