import os
import time
import logging
import requests

# 1. Grab environment variables from your Railway dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_live_gold_data():
    """
    Fetches the last 5 periods of 15-minute Gold data from Yahoo Finance API.
    Returns the current price and a list of recent closing prices for trend calculation.
    """
    try:
        # XAU/USD is tracked on Yahoo Finance under ticker 'GC=F' (Gold Futures)
        url = "https://query1.financeapi.com/v8/finance/chart/GC=F?interval=15m&range=2d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.get(url, headers=headers, timeout=15).json()
        result = response["chart"]["result"][0]
        
        current_price = round(result["meta"]["regularMarketPrice"], 2)
        closes = result["indicators"]["quote"][0]["close"]
        
        # Filter out any accidental null values from the data feed
        clean_closes = [c for c in closes if c is not None]
        
        return current_price, clean_closes[-5:]
    except Exception as e:
        logger.error(f"Error fetching live gold price: {e}")
        return None, []

def broadcast_signal(pair, direction, entry, tp1, tp2, tp3, sl):
    """Formats and sends the signal straight to your Telegram channel."""
    final_message = (
        f"🔔 **{pair}** 🔔\n\n"
        f"Direction: **{direction}**\n"
        f"Entry Price:  `{entry:.2f}`\n\n"
        f"TP1     `{tp1:.2f}`\n"
        f"TP2     `{tp2:.2f}`\n"
        f"TP3     `{tp3:.2f}`\n\n"
        f"SL       `{sl:.2f}`"
    )
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
        logger.info(f"Automated {direction} signal successfully dispatched for {pair}.")
    except Exception as e:
        logger.error(f"Failed to transmit Telegram message: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.critical("Missing core deployment environment variables in Railway!")
        exit(1)
        
    logger.info("Fully Automated Gold AI Signal Bot is active...")
    
    last_signal_direction = None
    
    while True:
        current_price, recent_closes = get_live_gold_data()
        
        if current_price and len(recent_closes) >= 3:
            # Simple Trend Strategy: Calculate short-term moving average
            avg_price = sum(recent_closes) / len(recent_closes)
            
            # Determine the market direction based on price action
            if current_price > avg_price:
                direction = "BUY"
            else:
                direction = "SELL"
                
            # Only send a signal when the trend switches directions (prevents spamming)
            if direction != last_signal_direction:
                last_signal_direction = direction
                entry_price = current_price
                
                # Dynamic targets based on average Gold volatility metrics ($3, $6, $9 spreads)
                if direction == "BUY":
                    tp1 = entry_price + 3.0
                    tp2 = entry_price + 6.0
                    tp3 = entry_price + 9.0
                    sl  = entry_price - 5.0
                else:
                    tp1 = entry_price - 3.0
                    tp2 = entry_price - 6.0
                    tp3 = entry_price - 9.0
                    sl  = entry_price + 5.0
                    
                # Broadcast the completely hands-free signal package
                broadcast_signal("XAU/USD (GOLD)", direction, entry_price, tp1, tp2, tp3, sl)
                
        # Scans the market data feed once every 5 minutes
        time.sleep(300)
