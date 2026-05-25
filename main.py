import os
import time
import logging
import requests

# 1. Grab environment variables from your Railway dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OFFSET = 0

def check_for_commands():
    """Polls Telegram for new messages sent directly to the bot."""
    global OFFSET
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={OFFSET}&timeout=20"
        response = requests.get(url, timeout=25).json()
        
        if not response.get("ok"):
            return

        for update in response.get("result", []):
            OFFSET = update["update_id"] + 1
            
            # Check if the update contains a text message
            if "message" in update and "text" in update["message"]:
                text = update["message"]["text"]
                chat_id = update["message"]["chat"]["id"]
                
                # Check if it's our target command
                if text.startswith("/send_signal"):
                    handle_signal_command(text, chat_id)
                    
    except Exception as e:
        logger.error(f"Error polling updates: {e}")

def handle_signal_command(text, chat_id):
    """Parses the command inputs and posts the clean block to the channel."""
    try:
        # Expected input: /send_signal EUR/USD SELL 1.1601 1.1581 1.1561 1.1541 1.1661
        parts = text.split()
        
        # Validation: command + 7 arguments = 8 items total
        if len(parts) < 8:
            error_msg = (
                "❌ **Missing variables!**\n\n"
                "**Use exactly this format:**\n"
                "`/send_signal [Pair] [Direction] [Entry] [TP1] [TP2] [TP3] [SL]`"
            )
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": error_msg, "parse_mode": "Markdown"})
            return

        pair = parts[1].upper()
        direction = parts[2].upper()
        entry = parts[3]
        tp1 = parts[4]
        tp2 = parts[5]
        tp3 = parts[6]
        sl = parts[7]

        # Structure the exact layout matching your original screenshot layout
        final_signal_layout = (
            f"🔔 **{pair}** 🔔\n\n"
            f"Direction: **{direction}**\n"
            f"Entry Price:  {entry}\n\n"
            f"TP1     {tp1}\n"
            f"TP2     {tp2}\n"
            f"TP3     {tp3}\n\n"
            f"SL       {sl}"
        )

        # Broadcast the beautiful message box to your channel destination
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": final_signal_layout,
            "parse_mode": "Markdown"
        }
        
        res = requests.post(send_url, json=payload).json()
        
        # Confirm back to you in your private chat that it posted successfully
        if res.get("ok"):
            requests.post(send_url, json={"chat_id": chat_id, "text": "✅ Signal posted to channel successfully!"})
        else:
            requests.post(send_url, json={"chat_id": chat_id, "text": f"❌ Failed to post. API Error: {res.get('description')}"})

    except Exception as e:
        logger.error(f"Error handling command: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.critical("Variables missing inside Railway panel!")
        exit(1)
        
    logger.info("Manual Telegram Signal Bot is running online 24/7...")
    
    # An infinite loop that stays alive waiting for your inputs
    while True:
        check_for_commands()
        time.sleep(1)
