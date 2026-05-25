import os
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

# Matches your exact Railway settings from screenshot 1000197704.jpg
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID") 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Webhook Server running successfully!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        logger.info(f"Alert data received: {data}")

        if not data:
            return "Payload empty", 400

        # Expecting text format: EUR/USD, SELL, 1.1601, 1.1581, 1.1561, 1.1541, 1.1661
        parts = [p.strip() for p in data.split(',')]

        if len(parts) < 7:
            final_message = data
        else:
            pair, direction, entry, tp1, tp2, tp3, sl = parts
            
            # Format perfectly to match your original screenshot
            final_message = (
                f"🔔 **{pair.upper()}** 🔔\n\n"
                f"Direction: **{direction.upper()}**\n"
                f"Entry Price:  {entry}\n\n"
                f"TP1     {tp1}\n"
                f"TP2     {tp2}\n"
                f"TP3     {tp3}\n\n"
                f"SL       {sl}"
            )

        # Broadcast text payload straight to Telegram API channel
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(telegram_url, json=payload)
        return "Dispatched to Telegram!", 200

    except Exception as e:
        logger.error(f"Webhook execution failure: {e}")
        return "Internal Error", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
