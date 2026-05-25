import os
import time
import logging
import requests

# Grab environment variables from your Railway dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tracks historical price arrays for trend filtering across multiple assets
market_history = {
    "XAU/USD": [],
    "EUR/USD": [],
    "GBP/USD": [],
    "USD/JPY": []
}

# Saves the last traded states to avoid duplicate message spamming
last_signal_direction = {
    "XAU/USD": None,
    "EUR/USD": None,
    "GBP/USD": None,
    "USD/JPY": None
}

def get_live_prices():
    """
    Fetches live market data for Gold and Major Forex Pairs.
    Utilizes high-speed, cloud-friendly public data nodes.
    """
    prices = {}
    
    # 1. Gather Gold Spot Price
    try:
        gold_url = "https://data-asb.goldprice.org/GetData/USD-XAU/1"
        headers = {"User-Agent": "Mozilla/5.0"}
        gold_res = requests.get(gold_url, headers=headers, timeout=10).json()
        prices["XAU/USD"] = round(float(gold_res[0].split(',')[1]), 2)
    except Exception as e:
        logger.error(f"Failed to fetch live Gold: {e}")

    # 2. Gather Forex Majors via Frankfurter Central Bank Nodes
    try:
        fx_url = "https://api.frankfurter.dev/v2/rates?quotes=USD,GBP,JPY"
        fx_res = requests.get(fx_url, timeout=10).json()
        
        # Base conversion calculations since rates are relative to EUR
        rates = fx_res[0]["rates"] if isinstance(fx_res, list) else fx_res["rates"]
        eur_usd = rates["USD"]
        eur_gbp = rates["GBP"]
        eur_jpy = rates["JPY"]

        prices["EUR/USD"] = round(eur_usd, 5)
        prices["GBP/USD"] = round(eur_usd / eur_gbp, 5)
        prices["USD/JPY"] = round(eur_jpy / eur_usd, 3)
    except Exception as e:
        logger.error(f"Failed to fetch live Forex rates: {e}")

    return prices

def calculate_targets(pair, direction, entry):
    """
    Generates precision pip-spread metrics tailored uniquely 
    to each specific asset's average volatility profile.
    """
    if pair == "XAU/USD":
        pip_unit = 1.0  # Gold movements measured directly in Points
        tp1_dist, tp2_dist, tp3_dist, sl_dist = 2.5, 5.0, 8.0, 4.0
    elif pair == "USD/JPY":
        pip_unit = 0.01 # JPY measured via second decimal point
        tp1_dist, tp2_dist, tp3_dist, sl_dist = 15, 30, 50, 20
    else:
        pip_unit = 0.0001 # Standard 4-Decimal Pip Structure
        tp1_dist, tp2_dist, tp3_dist, sl_dist = 12, 25, 40, 15

    if direction == "BUY":
        return (entry + (tp1_dist * pip_unit), 
                entry + (tp2_dist * pip_unit), 
                entry + (tp3_dist * pip_unit), 
                entry - (sl_dist * pip_unit))
    else:
        return (entry - (tp1_dist * pip_unit), 
                entry - (tp2_dist * pip_unit), 
                entry - (tp3_dist * pip_unit), 
                entry + (sl_dist * pip_unit))

def broadcast_signal(pair, direction, entry, tp1, tp2, tp3, sl):
    """Broadcasts a stylized signal box with tap-to-copy code layout parameters."""
    # Format floating positions explicitly based on pair pricing precision
    decimals = 2 if pair in ["XAU/USD", "USD/JPY"] else 5
    
    final_message = (
        f"🔔 **{pair}** 🔔\n\n"
        f"Direction: **{direction}**\n"
        f"Entry Price:  `{entry:.{decimals}f}`\n\n"
        f"TP1     `{tp1:.{decimals}f}`\n"
        f"TP2     `{tp2:.{decimals}f}`\n"
        f"TP3     `{tp3:.{decimals}f}`\n\n"
        f"SL       `{sl:.{decimals}f}`"
    )
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHANNEL_ID, "text": final_message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
        logger.info(f"Broadcast complete for {pair} {direction}")
    except Exception as e:
        logger.error(f"Telegram communication failure: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.critical("Railway dashboard variables are incomplete!")
        exit(1)
        
    logger.info("Upgraded Multi-Asset Forex/Gold Engine Running...")
    first_run = True

    while True:
        current_prices = get_live_prices()
        
        for pair, current_price in current_prices.items():
            if not current_price:
                continue
                
            history = market_history[pair]
            history.append(current_price)
            if len(history) > 6:
                history.pop(0)

            # High-Accuracy Scalping Engine: Fast momentum vs Slow baseline filter
            if len(history) >= 3:
                fast_ma = sum(history[-2:]) / 2
                slow_ma = sum(history) / len(history)
                
                direction = "BUY" if fast_ma >= slow_ma else "SELL"
                
                # Active signal dispatch rule logic
                if direction != last_signal_direction[pair] or first_run:
                    last_signal_direction[pair] = direction
                    
                    tp1, tp2, tp3, sl = calculate_targets(pair, direction, current_price)
                    broadcast_signal(pair, direction, current_price, tp1, tp2, tp3, sl)

        # Signal loop override flag deactivated after first comprehensive check
        first_run = False
        
        # Scans the global markets continuously every 60 seconds for higher activity
        time.sleep(60)
