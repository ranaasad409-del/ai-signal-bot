import json
import time
import asyncio
import websockets
from datetime import datetime, timedelta
from telegram import Bot

# =======================
# TELEGRAM SETTINGS
# =======================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"
bot = Bot(token=BOT_TOKEN)

# =======================
# QUOTEX LOGIN SETTINGS
# =======================
QUOTEX_EMAIL = "supportquotex97@gmail.com"
QUOTEX_PASSWORD = "Allahbadsha409@"

# =======================
# OTC PAIRS TO TRACK
# =======================
pairs = ["USDPKR", "USDMXN", "USDBRL"]

# EMA Settings for signal
FAST_EMA = 5
SLOW_EMA = 20
SIGNAL_LEAD_TIME = 20  # seconds before candle
SLEEP_INTERVAL = 0.5

# Storage
active_trades = {}
price_history = {pair: [] for pair in pairs}

# Logging
def log_trade(message):
    print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {message}")
    with open("trade_log.txt", "a") as f:
        f.write(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {message}\n")

# EMA calculation
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
# WebSocket handler
# =======================
async def quotex_sniper():
    uri = "wss://quotex.io/ws"  # placeholder, actual WS URL may vary
    async with websockets.connect(uri) as websocket:
        # Login payload (simplified)
        login_payload = json.dumps({
            "type": "auth",
            "email": QUOTEX_EMAIL,
            "password": QUOTEX_PASSWORD
        })
        await websocket.send(login_payload)

        log_trade("🚀 Connected to Quotex WebSocket")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                # Example structure for a candle
                # You will need to adjust based on actual WS feed
                for pair in pairs:
                    candle = data.get(pair)
                    if not candle:
                        continue

                    close_price = float(candle['close'])
                    price_history[pair].append(close_price)
                    if len(price_history[pair]) > 50:
                        price_history[pair] = price_history[pair][-50:]

                    now = datetime.utcnow()
                    seconds_to_next_candle = 60 - now.second

                    # Send sniper signal
                    if seconds_to_next_candle <= SIGNAL_LEAD_TIME:
                        if pair not in active_trades:
                            signal = generate_signal(price_history[pair])
                            if signal:
                                candle_open_time = (now + timedelta(seconds=seconds_to_next_candle)).replace(microsecond=0)
                                entry_price = close_price
                                active_trades[pair] = {"signal": signal, "candle_open_time": candle_open_time, "entry": entry_price}

                                msg = f"📊 {pair} OTC Signal\nSignal: {signal}\nCandle Opens: {candle_open_time.strftime('%H:%M:%S')} UTC\nEntry Price: {entry_price:.4f}"
                                bot.send_message(chat_id=CHAT_ID, text=msg)
                                log_trade(msg)

                    # Check candle close result
                    if pair in active_trades:
                        trade = active_trades[pair]
                        if now >= trade["candle_open_time"] + timedelta(seconds=60):
                            close = close_price
                            win = (trade["signal"]=="BUY" and close > trade["entry"]) or (trade["signal"]=="SELL" and close < trade["entry"])
                            result = "WIN ✅" if win else "LOSS ❌"
                            msg = f"📈 {pair} Trade Result\nSignal: {trade['signal']}\nEntry: {trade['entry']:.4f}\nClose: {close:.4f}\nResult: {result}\nTime: {now.strftime('%H:%M:%S')} UTC"
                            bot.send_message(chat_id=CHAT_ID, text=msg)
                            log_trade(msg)
                            del active_trades[pair]

            except Exception as e:
                log_trade(f"Error processing WebSocket message: {e}")
                await asyncio.sleep(1)

# =======================
# Run the bot
# =======================
log_trade("🚀 OTC Sniper Bot Started")
asyncio.get_event_loop().run_until_complete(quotex_sniper())
