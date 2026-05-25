import os
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

# Reads the exactly named variables from your Railway dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID")

# Configure logging so you can watch alerts arrive in the Railway logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Forex Signal Webhook is Active!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receives alerts from TradingView and parses them into a clean Telegram format.
    """
    try:
        # Decode the incoming raw text payload from TradingView
        data = request.data.decode('utf-8').strip()
        logger.info(f"Incoming alert data received: {data}")

        if not data:
            return "Payload is completely empty", 400

        # Split comma-separated text: EUR/USD, SELL, 1.1601, 1.1581, 1.1561, 1.1541, 1.1661
        parts = [p.strip() for p in data.split(',')]

        # If it doesn't have 7 parts, fallback and send the text exactly as TradingView wrote it
        if len(parts) < 7:
            logger.warning("Alert didn't contain 7 parts. Sending as raw text fallback.")
            final_message = data
        else:
            pair, direction, entry, tp1, tp2, tp3, sl = parts
            
            # Replicates the exact visual design and spacing from your original screenshot
            final_message = (
                f"🔔 **{pair.upper()}** 🔔\n\n"
                f"Direction: **{direction.upper()}**\n"
                f"Entry Price:  {entry}\n\n"
                f"TP1     {tp1}\n"
                f"TP2     {tp2}\n"
                f"TP3     {tp3}\n\n"
                f"SL       {sl}"
            )

        # Ship the constructed alert to the Telegram Bot API
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(telegram_url, json=payload)
        logger.info(f"Telegram API response: {response.text}")

        return "Signal successfully dispatched to Telegram Channel", 200

    except Exception as e:
        logger.error(f"Critical error processing the webhook alert: {e}")
        return "Internal Webhook Processing Error", 500

if __name__ == '__main__':
    # Railway automatically supplies a dynamic PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
