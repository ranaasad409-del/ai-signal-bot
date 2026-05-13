import requests
import time
import traceback

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

# =========================
# SEND TELEGRAM MESSAGE
# =========================
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(url, data=payload)

        print("Telegram Response:")
        print(response.text)

    except Exception as e:
        print("Telegram Error:", e)
        traceback.print_exc()

# =========================
# GENERATE SIGNAL
# =========================
def generate_signal():

    # Example dummy signal
    signal = "BUY"
    entry = 3360
    tp = 3365
    sl = 3355

    message = f"""
🔥 AI GOLD SIGNAL

📈 {signal} XAUUSD

💰 Entry : {entry}
🎯 TP     : {tp}
🛑 SL     : {sl}
"""

    send_telegram_message(message)

# =========================
# MAIN LOOP
# =========================
print("AI GOLD SIGNAL BOT STARTED")

while True:
    try:
        print("Checking market...")

        generate_signal()

        print("Signal sent successfully")

    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        traceback.print_exc()

    # wait 5 minutes
    time.sleep(300)
