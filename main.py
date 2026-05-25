import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1. Read the secret token from Railway's environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 2. Configure logging to monitor the bot's health in Railway logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the admin or user."""
    await update.message.reply_text(
        "⚡ Forex Signal Bot is Active!\n\n"
        "Use this format to send a signal:\n"
        "`/send_signal EUR/USD SELL 1.1601 1.1581 1.1561 1.1541 1.1661`",
        parse_mode="Markdown"
    )

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Parses arguments and broadcasts the beautifully formatted Forex signal.
    """
    try:
        args = context.args
        # Validate that we have exactly 7 required arguments
        if len(args) != 7:
            await update.message.reply_text(
                "❌ **Incorrect Arguments!**\n\n"
                "**Expected Format:**\n"
                "`/send_signal [Pair] [Direction] [Entry] [TP1] [TP2] [TP3] [SL]`\n\n"
                "**Example:**\n"
                "`/send_signal EUR/USD SELL 1.1601 1.1581 1.1561 1.1541 1.1661`",
                parse_mode="Markdown"
            )
            return

        # Extract parameters
        pair = args[0].upper()          # e.g., EUR/USD
        direction = args[1].upper()     # e.g., SELL
        entry = args[2]                 # e.g., 1.1601
        tp1 = args[3]                   # e.g., 1.1581
        tp2 = args[4]                   # e.g., 1.1561
        tp3 = args[5]                   # e.g., 1.1541
        sl = args[6]                    # e.g., 1.1661

        # Match the visual layout from your screenshot perfectly
        signal_message = (
            f"🔔 **{pair}** 🔔\n\n"
            f"Direction: **{direction}**\n"
            f"Entry Price:  {entry}\n\n"
            f"TP1     {tp1}\n"
            f"TP2     {tp2}\n"
            f"TP3     {tp3}\n\n"
            f"SL       {sl}"
        )

        # Send the clean layout back to the channel or chat
        await update.message.reply_text(signal_message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing signal: {e}")
        await update.message.reply_text("⚠️ An internal error occurred while formatting the signal.")

def main():
    """Main execution point."""
    if not BOT_TOKEN:
        logger.critical("FATAL: TELEGRAM_TOKEN environment variable is missing!")
        return

    # Build the application
    app = Application.builder().token(BOT_TOKEN).build()

    # Link Telegram commands to functions
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_signal", send_signal))

    # Start the bot engine (Keeps running 24/7 on Railway)
    logger.info("Starting bot deployment script...")
    app.run_polling()

if __name__ == "__main__":
    main()
