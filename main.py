import asyncio
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from telegram import Bot
from datetime import datetime

TOKEN = "8689634513:AAFm5KBhu2pPnwcwPnTyvS8C1BAUS9YIK7Q"
CHAT_ID = "5974354691"

bot = Bot(token=TOKEN)

PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X"
}


def bullish_engulfing(df):
    if len(df) < 3:
        return False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    return (
        prev['Close'] < prev['Open'] and
        curr['Close'] > curr['Open'] and
        curr['Close'] > prev['Open'] and
        curr['Open'] < prev['Close']
    )


def bearish_engulfing(df):
    if len(df) < 3:
        return False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    return (
        prev['Close'] > prev['Open'] and
        curr['Close'] < curr['Open'] and
        curr['Open'] > prev['Close'] and
        curr['Close'] < prev['Open']
    )


def get_data(symbol):
    df = yf.download(
        tickers=symbol,
        interval="1m",
        period="1d",
        progress=False
    )

    df.dropna(inplace=True)

    df['ema9'] = EMAIndicator(df['Close'], window=9).ema_indicator()
    df['ema21'] = EMAIndicator(df['Close'], window=21).ema_indicator()
    df['rsi'] = RSIIndicator(df['Close'], window=14).rsi()

    return df


def analyze(df):
    last = df.iloc[-1]

    buy_condition = (
        last['ema9'] > last['ema21'] and
        45 < last['rsi'] < 70 and
        bullish_engulfing(df)
    )

    sell_condition = (
        last['ema9'] < last['ema21'] and
        30 < last['rsi'] < 55 and
        bearish_engulfing(df)
    )

    if buy_condition:
        return "BUY"

    if sell_condition:
        return "SELL"

    return None


async def send_signal(pair, signal):
    current_time = datetime.now().strftime("%H:%M:%S")

    msg = f"""
📊 SIGNAL ALERT

PAIR: {pair}
TIMEFRAME: 1 MINUTE
SIGNAL: {signal}
ENTRY: NEXT CANDLE
TIME: {current_time}

Strategy:
EMA9 + EMA21 + RSI + Engulfing Candle
"""

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def scanner():
    last_signals = {}

    while True:
        try:
            for pair_name, symbol in PAIRS.items():
                df = get_data(symbol)

                signal = analyze(df)

                if signal:
                    previous = last_signals.get(pair_name)

                    if previous != signal:
                        await send_signal(pair_name, signal)
                        last_signals[pair_name] = signal

                        print(f"{pair_name}: {signal}")

        except Exception as e:
            print(e)

        await asyncio.sleep(60)


asyncio.run(scanner())
