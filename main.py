import os
import time
import logging
import requests

# 1. Grab environment variables from your Railway dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep track of recent closing prices globally for our trend calculation
recent_closes = []

def get_live_gold_price():
    """
    Fetches the live Spot Gold price (XAU/USD) directly from the global spot feed.
    This public route is reliable and doesn't block cloud server IPs.
    """
    try:
        url = "https://data-asb.goldprice.org/GetData/USD-XAU/1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10).json()
        
        # Parse out the current spot price string (e.g., "2345.67") and convert to float
        price_str = response[0].split(',')[1]
        return round(float(price_str), 2)
    except Exception as e:
        logger.error(f"Error fetching live gold price: {e}")
        return None

def broadcast_signal(pair, direction, entry, tp1, tp2, tp3, sl):
    """Formats the signal and pushes it cleanly to your channel."""
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
        res = requests.post(url, json=payload).json()
        if res.get("ok"):
            logger.info(f"Automated {direction} signal posted for {pair}.")
        else:
            logger.error(f"Telegram API rejected message: {res.get('description')}")
    except Exception as e:
        logger.error(f"Failed to transmit message: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.critical("Core environment variables are completely missing in Railway settings!")
        exit(1)
        
    logger.info("Fully Automated Gold AI Signal Bot is active...")
    
    last_signal_direction = None
    
    while True:
        current_price = get_live_gold_price()
        
        if current_price:
            logger.info(f"Current Gold Spot Price checked: ${current_price}")
            
            # Record the current price into our short-term historical tracker
            recent_closes.append(current_price)
            if len(recent_closes) > 5:
                recent_closes.pop(0) # Keep only the last 5 checks to monitor momentum
            
            # Once we have enough baseline data points, calculate the direction
            if len(recent_closes) >= 3:
                avg_price = sum(recent_closes) / len(recent_closes)
                
                if current_price > avg_price:
                    direction = "BUY"
                else:
                    direction = "SELL"
                
                # Triggers automatically only when the market structural trend reverses
                if direction != last_signal_direction:
                    last_signal_direction = direction
                    entry_price = current_price
                    
                    # Generates structured risk-reward setups automatically ($3, $6, $9 parameters)
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
                        
                    broadcast_signal("XAU/USD (GOLD)", direction, entry_price, tp1, tp2, tp3, sl)
                    
        # Check market price once every 3 minutes (180 seconds)
        time.sleep(180)
