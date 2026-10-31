import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def ema(values, period):
    result = values[0]
    k = 2 / (period + 1)
    for value in values[1:]:
        result = value * k + result * (1 - k)
    return result

def send_message(message):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=15
    ).raise_for_status()

def main():
    url = "https://fapi.binance.com/fapi/v1/klines"
    data = requests.get(
        url,
        params={"symbol": "BTCUSDT", "interval": "15m", "limit": 60},
        timeout=15
    ).json()

    # Last candle is still forming; ignore it.
    closes = [float(c[4]) for c in data[:-1]]
    price = closes[-1]

    fast = ema(closes[-30:], 9)
    slow = ema(closes[-30:], 21)

    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(x, 0) for x in changes[-14:]]
    losses = [max(-x, 0) for x in changes[-14:]]
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    rsi = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)

    if fast > slow and rsi > 55:
        side = "LONG"
        sl, tp = price * 0.992, price * 1.012
    elif fast < slow and rsi < 45:
        side = "SHORT"
        sl, tp = price * 1.008, price * 0.988
    else:
        send_message(f"BTCUSDT 15m: No clear signal. RSI: {rsi:.1f}")
        return

    send_message(
        f"BTCUSDT FUTURES SIGNAL\n"
        f"Direction: {side}\n"
        f"Entry: {price:.2f}\n"
        f"Stop Loss: {sl:.2f}\n"
        f"Take Profit: {tp:.2f}\n"
        f"RSI: {rsi:.1f}\n"
        f"Timeframe: 15m\n"
        f"Signal only. Verify before trading."
    )

if __name__ == "__main__":
    main()
