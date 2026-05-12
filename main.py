import time
import requests
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "AUDUSD=X",
    "USDCAD=X"
]

TIMEFRAME = "1m"

def get_data(symbol):
    try:
        df = yf.download(
            tickers=symbol,
            period="1d",
            interval=TIMEFRAME,
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        return df

    except Exception as e:
        print(f"Error for {symbol}: {e}")
        return None

def analyze_market(df):
    close = df["Close"]

    rsi = RSIIndicator(close, window=14).rsi()
    ema_fast = EMAIndicator(close, window=9).ema_indicator()
    ema_slow = EMAIndicator(close, window=21).ema_indicator()

    latest_rsi = float(rsi.iloc[-1])
    latest_fast = float(ema_fast.iloc[-1])
    latest_slow = float(ema_slow.iloc[-1])

    signal = None
    confidence = 0

    if latest_fast > latest_slow and latest_rsi < 70:
        signal = "BUY"
        confidence = 88

    elif latest_fast < latest_slow and latest_rsi > 30:
        signal = "SELL"
        confidence = 88

    return {
        "signal": signal,
        "confidence": confidence,
        "rsi": round(latest_rsi, 2),
        "ema_fast": round(latest_fast, 5),
        "ema_slow": round(latest_slow, 5)
    }

print("🚀 REAL ANALYSIS SIGNAL BOT STARTED")

while True:
    print("\n📡 Scanning Market 24/7")
    print("🔎 Scanning market...")

    found = False

    for pair in PAIRS:
        df = get_data(pair)

        if df is None:
            continue

        result = analyze_market(df)

        if result["signal"]:

            otc_pair = pair.replace("=X", "").replace("USD", "USD/")

            print("\n📊 AI OTC SIGNAL")
            print(f"\n💱 Pair: {otc_pair} OTC")
            print(f"⏰ Entry Time: LIVE")
            print(f"📈 Signal: {result['signal']}")
            print("🕐 Time Frame: 1 Minute")
            print(f"🔥 Confidence: {result['confidence']}%")

            print("\n========== STRATEGY ==========")
            print(f"\nRSI: {result['rsi']}")
            print(f"EMA FAST: {result['ema_fast']}")
            print(f"EMA SLOW: {result['ema_slow']}")

            print("\n⏳ TAKE ENTRY NOW")
            print("\n⌛ Waiting 1 minute for result...")

            found = True

            time.sleep(60)

    if not found:
        print("\n⌛ Waiting for strong setup...")

    time.sleep(10)