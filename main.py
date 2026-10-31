import os
import time
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

BINANCE = "https://fapi.binance.com/fapi/v1/klines"

def ema(values, period):
    k = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = value * k + result * (1 - k)
    return result

def get_signal():
    data = requests.get(
        BINANCE,
        params={"symbol": "BTCUSDT", "interval": "15m", "limit": 60},
        timeout=15
    ).json()

    candles = data[:-1]
    closes = [float(c[4]) for c in candles]
    price = closes[-1]

    fast = ema(closes[-30:], 9)
    slow = ema(closes[-30:], 21)

    changes = [closes[i] - closes[i-1]
               for i in range(1, len(closes))]
    gains = [max(x, 0) for x in changes[-14:]]
    losses = [max(-x, 0) for x in changes[-14:]]
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14

    rsi = 100 if avg_loss == 0 else (
        100 - 100 / (1 + avg_gain / avg_loss)
    )

    if fast > slow and rsi > 55:
        side = "LONG"
        sl = price * 0.992
        tp = price * 1.012
    elif fast < slow and rsi < 45:
        side = "SHORT"
        sl = price * 1.008
        tp = price * 0.988
    else:
        return None

    return (
        f"BTCUSDT FUTURES SIGNAL\n"
        f"Direction: {side}\n"
        f"Entry: {price:.2f}\n"
        f"Stop Loss: {sl:.2f}\n"
        f"Take Profit: {tp:.2f}\n"
        f"Timeframe: 15m\n"
        f"RSI: {rsi:.1f}\n"
        f"Signal only - verify before trading."
    )

last_candle = None

while True:
    try:
        data = requests.get(
            BINANCE,
            params={"symbol": "BTCUSDT", "interval": "15m", "limit": 2},
            timeout=15
        ).json()

        candle_time = data[-2][0]

        if candle_time != last_candle:
            last_candle = candle_time
            signal = get_signal()

            if signal:
                requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    data={"chat_id": CHAT_ID, "text": signal},
                    timeout=15
                )

        time.sleep(30)

    except Exception as error:
        print("Error:", error)
        time.sleep(30)
