# main.py
# AI Futures Scalping Telegram Bot
# KuCoin Futures + Railway + Telegram

import os
import asyncio
import ccxt
import pandas as pd
import ta

from telegram import Bot

# =====================================
# CONFIG
# =====================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LEVERAGE = 20
TIMEFRAME = "1m"
SCAN_INTERVAL = 30

SYMBOLS = [

    # Major
    "XBTUSDTM",
    "ETHUSDTM",
    "SOLUSDTM",
    "BNBUSDTM",

    # Trending
    "XRPUSDTM",
    "DOGEUSDTM",
    "ADAUSDTM",
    "AVAXUSDTM",
    "LINKUSDTM",

    # Volatile
    "WIFUSDTM",
    "NEARUSDTM",
    "APTUSDTM",

    # Momentum
    "ARBUSDTM",
    "OPUSDTM",
    "INJUSDTM"
]

# =====================================
# TELEGRAM
# =====================================

bot = Bot(token=BOT_TOKEN)

# =====================================
# EXCHANGE
# =====================================

exchange = ccxt.kucoinfutures({
    "enableRateLimit": True
})

# =====================================
# ACTIVE SIGNALS
# =====================================

active_signals = {}

# =====================================
# FETCH MARKET DATA
# =====================================

def fetch_data(symbol):

    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=TIMEFRAME,
        limit=200
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    # EMA
    df["ema9"] = ta.trend.ema_indicator(
        df["close"],
        window=9
    )

    df["ema21"] = ta.trend.ema_indicator(
        df["close"],
        window=21
    )

    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(
        df["close"],
        window=14
    ).rsi()

    # MACD
    macd = ta.trend.MACD(df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    return df

# =====================================
# AI SIGNAL GENERATOR
# =====================================

def generate_signal(df):

    latest = df.iloc[-1]

    recent_high = df["high"].tail(15).max()
    recent_low = df["low"].tail(15).min()

    # Tight range detection
    range_percent = (
        (recent_high - recent_low)
        / recent_low
    ) * 100

    in_range = range_percent < 0.5

    # Volume spike
    avg_volume = df["volume"].tail(20).mean()

    volume_spike = (
        latest["volume"]
        > avg_volume * 1.5
    )

    # Bullish trend
    bullish = (
        latest["ema9"] > latest["ema21"]
        and latest["macd"] > latest["macd_signal"]
        and latest["rsi"] > 55
    )

    # Bearish trend
    bearish = (
        latest["ema9"] < latest["ema21"]
        and latest["macd"] < latest["macd_signal"]
        and latest["rsi"] < 45
    )

    # =====================================
    # LONG SIGNAL
    # =====================================

    if (
        in_range
        and latest["close"] > recent_high
        and volume_spike
        and bullish
    ):

        entry = latest["close"]

        return {

            "side": "LONG",

            "entry1": round(entry, 4),
            "entry2": round(entry * 1.0005, 4),

            "tp1": round(entry * 1.003, 4),
            "tp2": round(entry * 1.006, 4),
            "tp3": round(entry * 1.01, 4),

            "sl": round(entry * 0.995, 4)
        }

    # =====================================
    # SHORT SIGNAL
    # =====================================

    if (
        in_range
        and latest["close"] < recent_low
        and volume_spike
        and bearish
    ):

        entry = latest["close"]

        return {

            "side": "SHORT",

            "entry1": round(entry, 4),
            "entry2": round(entry * 0.9995, 4),

            "tp1": round(entry * 0.997, 4),
            "tp2": round(entry * 0.994, 4),
            "tp3": round(entry * 0.99, 4),

            "sl": round(entry * 1.005, 4)
        }

    return None

# =====================================
# SEND SIGNAL
# =====================================

async def send_signal(symbol, signal):

    pair = symbol.replace("USDTM", "")

    text = f"""
🚨 {pair} | {signal['side']} | {LEVERAGE}x

Entry:
{signal['entry1']} - {signal['entry2']}

TP1: {signal['tp1']}
TP2: {signal['tp2']}
TP3: {signal['tp3']}

SL: {signal['sl']}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

# =====================================
# SEND UPDATE
# =====================================

async def send_update(message):

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

# =====================================
# MONITOR ACTIVE SIGNALS
# =====================================

async def monitor_signals():

    while True:

        try:

            remove_list = []

            for pair in list(active_signals.keys()):

                signal = active_signals[pair]

                ticker = exchange.fetch_ticker(pair)

                price = ticker["last"]

                side = signal["side"]

                clean_pair = pair.replace("USDTM", "")

                # =====================================
                # LONG
                # =====================================

                if side == "LONG":

                    if (
                        not signal["tp1_hit"]
                        and price >= signal["tp1"]
                    ):

                        signal["tp1_hit"] = True

                        await send_update(
                            f"✅ {clean_pair} TP1 HIT"
                        )

                    if (
                        not signal["tp2_hit"]
                        and price >= signal["tp2"]
                    ):

                        signal["tp2_hit"] = True

                        await send_update(
                            f"🔥 {clean_pair} TP2 HIT"
                        )

                    if price >= signal["tp3"]:

                        await send_update(
                            f"🏆 {clean_pair} TP3 HIT"
                        )

                        remove_list.append(pair)

                    elif price <= signal["sl"]:

                        await send_update(
                            f"❌ {clean_pair} STOP LOSS HIT"
                        )

                        remove_list.append(pair)

                # =====================================
                # SHORT
                # =====================================

                else:

                    if (
                        not signal["tp1_hit"]
                        and price <= signal["tp1"]
                    ):

                        signal["tp1_hit"] = True

                        await send_update(
                            f"✅ {clean_pair} TP1 HIT"
                        )

                    if (
                        not signal["tp2_hit"]
                        and price <= signal["tp2"]
                    ):

                        signal["tp2_hit"] = True

                        await send_update(
                            f"🔥 {clean_pair} TP2 HIT"
                        )

                    if price <= signal["tp3"]:

                        await send_update(
                            f"🏆 {clean_pair} TP3 HIT"
                        )

                        remove_list.append(pair)

                    elif price >= signal["sl"]:

                        await send_update(
                            f"❌ {clean_pair} STOP LOSS HIT"
                        )

                        remove_list.append(pair)

            # Remove completed trades
            for pair in remove_list:

                del active_signals[pair]

            await asyncio.sleep(5)

        except Exception as e:

            print("Monitor Error:", e)

            await asyncio.sleep(5)

# =====================================
# MARKET SCANNER
# =====================================

async def scanner():

    while True:

        try:

            for symbol in SYMBOLS:

                # Skip active trades
                if symbol in active_signals:
                    continue

                df = fetch_data(symbol)

                signal = generate_signal(df)

                if signal:

                    signal["tp1_hit"] = False
                    signal["tp2_hit"] = False

                    active_signals[symbol] = signal

                    await send_signal(
                        symbol,
                        signal
                    )

            await asyncio.sleep(SCAN_INTERVAL)

        except Exception as e:

            print("Scanner Error:", e)

            await asyncio.sleep(10)

# =====================================
# MAIN
# =====================================

async def main():

    print("AI Futures Bot Running...")

    await asyncio.gather(
        scanner(),
        monitor_signals()
    )

# =====================================
# START
# =====================================

asyncio.run(main())
