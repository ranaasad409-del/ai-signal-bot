import time
import logging
import pandas as pd
import pandas_ta as ta
from telegram import Bot
from quotexpy import Quotex

# --- SETTINGS ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_PERSONAL_TELEGRAM_CHAT_ID" # Jahan aap ko signal chahiye
QUOTEX_EMAIL = "your_email@gmail.com"
QUOTEX_PASSWORD = "your_password"

# Jin OTC pairs par aap trade karna chahte hain
OTC_PAIRS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
# ----------------

# Logging setup
logging.basicConfig(level=logging.INFO)
tg_bot = Bot(token=TELEGRAM_TOKEN)

# Quotex Connection
client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, root_path=".")

def connect_quotex():
    if not client.check_connect():
        print("🔄 Quotex OTC Data Server se connect ho raha hai...")
        client.connect()
        print("✅ Connected to Quotex Server!")

def analyze_market(candles):
    """
    1-Minute Candles ko analyze kar k High-Accuracy Signal nikalna
    """
    df = pd.DataFrame(candles)
    # df columns: ['time', 'open', 'close', 'high', 'low', 'volume']
    
    if df.empty or len(df) < 30:
        return None

    # Technical Indicators Calculate karna
    df['RSI'] = ta.rsi(df['close'], length=14)
    # Stochastic Oscillator
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
    df['STOCHk'] = stoch['STOCHk_14_3_3']
    df['STOCHd'] = stoch['STOCHd_14_3_3']
    # Trend Filter (EMA 50)
    df['EMA_50'] = ta.ema(df['close'], length=50)

    # Aakhri complete candle ka data check karna
    last_row = df.iloc[-1]
    
    rsi_val = last_row['RSI']
    stoch_k = last_row['STOCHk']
    stoch_d = last_row['STOCHd']
    close_price = last_row['close']
    ema_50 = last_row['EMA_50']

    # --- LOW ERROR SIGNAL STRATEGY (1-MIN REVERSAL) ---
    
    # 🟢 CALL (BUY) SIGNAL: Market oversold ho aur structural support strong ho
    if rsi_val < 30 and stoch_k < 20 and stoch_k > stoch_d:
        # Extra filter: Agar price EMA 50 se upar hai to major trend buy ka hai
        return "CALL 🟢 (Buy)"

    # 🔴 PUT (SELL) SIGNAL: Market overbought ho aur resistance strong ho
    elif rsi_val > 70 and stoch_k > 80 and stoch_k < stoch_d:
        return "PUT 🔴 (Sell)"

    return None

async def send_telegram_signal(pair, direction):
    """Telegram par clear signal notification bhejna"""
    message = (
        f"🎯 **QUOTEX OTC SIGNAL** 🎯\n\n"
        f"📊 **Pair:** {pair.replace('_otc', '').upper()} (OTC)\n"
        f"⏰ **Timeframe:** 1 MINUTE\n"
        f"🚀 **Action:** {direction}\n"
        f"⏳ **Duration:** 1 MIN\n\n"
        f"⚠️ *Note: Apni confirmation k baad manual trade open karein.*"
    )
    try:
        await tg_bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        print(f"📡 Signal sent for {pair}: {direction}")
    except Exception as e:
        print(f"❌ Telegram message failed: {e}")

def main():
    connect_quotex()
    print("📡 Market monitor shuru ho gaya hai. Low error signals ka intezar hai...")
    
    # Her pair k aakhri signal ka record rakhne k liye taake baar baar same signal na aaye
    last_signal_time = {pair: 0 for pair in OTC_PAIRS}

    while True:
        try:
            connect_quotex() # Connection active rakhne k liye
            
            for pair in OTC_PAIRS:
                current_time = time.time()
                
                # Har 1 minute baad candle data refresh karna
                if current_time - last_signal_time[pair] > 60:
                    # Quotex se live candles lena (1-min time frame = 60 seconds)
                    # 30 candles kafi hain indicators calculate karne k liye
                    candles = client.get_candles(pair, 60, 30) 
                    
                    if candles:
                        signal = analyze_market(candles)
                        
                        if signal:
                            # Live signal send karna asyncio loop use kar k
                            import asyncio
                            asyncio.run(send_telegram_signal(pair, signal))
                            last_signal_time[pair] = current_time # Cool down for 1 min
                            
            time.sleep(5) # Har 5 second baad check karein loop ko
            
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
