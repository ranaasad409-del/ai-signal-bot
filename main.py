import os
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

# 1. Grab environment variables from Railway settings
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Note: You can find your Channel ID by forwarding a message from it to @userinfobot
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID") 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Forex Webhook Server is Alive!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receives alerts from TradingView and forwards formatted text to Telegram.
    """
    try:
        # Accept text/plain data natively sent by TradingView alerts
        data = request.data.decode('utf-8')
        logger.info(f"Received raw text alert: {data}")

        if not data:
            return "Empty request payload", 400

        # Expected incoming text structure from your TradingView Alert text box:
        # EUR/USD, SELL, 1.1601, 1.1581, 1.1561, 1.1541, 1.1661
        parts = [p.strip() for p in data.split(',')]

        if len(parts) < 7:
            logger.warning("Received invalid text format. Sending raw text fallback.")
            # If the text format doesn't match, just forward whatever TradingView sent natively
            final_message = data
        else:
            pair, direction, entry, tp1, tp2, tp3, sl = parts
            
            # Replicate the exact visual layout from the user screenshot
            final_message = (
                f"🔔 **{pair.upper()}** 🔔\n\n"
                f"Direction: **{direction.upper()}**\n"
                f"Entry Price:  {entry}\n\n"
                f"TP1     {tp1}\n"
                f"TP2     {tp2}\n"
                f"TP3     {tp3}\n\n"
                f"SL       {sl}"
            )

        # Broadcast message via Telegram Bot API
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(telegram_url, json=payload)
        logger.info(f"Telegram API Response: {response.text}")

        return "Alert sent to Telegram successfully!", 200

    except Exception as e:
        logger.error(f"Error handling webhook alert request: {e}")
        return "Internal server webhook error", 500

if __name__ == '__main__':
    # Railway passes a target PORT variable automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
