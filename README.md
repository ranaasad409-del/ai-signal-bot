# Quotex OTC Sniper Bot

## Features
- Real-time 1-minute OTC prices
- Sniper signals 20 seconds before candle
- Telegram notifications
- WIN/LOSS results after candle
- Headless and Railway deployable

## Deployment
1. Replace placeholders in `main.py`:
   - `BOT_TOKEN`
   - `CHAT_ID`
   - `QUOTEX_EMAIL` / `QUOTEX_PASSWORD`
2. Push all files to GitHub
3. Deploy on Railway
4. Add build command: `playwright install chromium`
5. Start bot → live OTC sniper signals
