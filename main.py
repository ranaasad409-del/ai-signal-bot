# =========================
# MAIN LOOP
# =========================

import time

LAST_SIGNAL_TIME = 0

COOLDOWN = 900   # 15 minutes


while True:

    try:

        current_time = time.time()

        # WAIT FOR NEXT SIGNAL WINDOW
        if current_time - LAST_SIGNAL_TIME < COOLDOWN:

            remaining = int(
                COOLDOWN - (current_time - LAST_SIGNAL_TIME)
            )

            print(f"Waiting {remaining} sec...")

            time.sleep(5)

            continue

        # GENERATE SIGNAL
        signal = generate_signal()

        # ONLY SEND STRONG SIGNAL
        if signal is not None:

            text = f"""
🚨 AI GOLD SIGNAL 🚨

📊 Pair: {signal['pair']}

📈 Direction: {signal['direction']}

💰 Entry Price: {signal['entry']}

🎯 TP1: {signal['tp1']}
🎯 TP2: {signal['tp2']}
🎯 TP3: {signal['tp3']}

🛑 Stop Loss: {signal['sl']}

📊 Expected Pips: {signal['expected_pips']}

🔥 Accuracy: {signal['accuracy']}%

🌍 Session: {signal['session']}

📰 News: {signal['news']}

🧠 Strategy:
SMC + Liquidity Sweep + Trend Confirmation
"""

            bot.send_message(
                chat_id=CHAT_ID,
                text=text
            )

            print("SIGNAL SENT")

            # SAVE LAST SIGNAL TIME
            LAST_SIGNAL_TIME = time.time()

            # RESULT CHECK
            send_result(signal)

        else:

            print("Weak setup skipped")

        # SAFE WAIT
        time.sleep(30)

    except Exception as e:

        print(f"ERROR: {e}")

        time.sleep(30)
