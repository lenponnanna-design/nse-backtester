import argparse
import pandas as pd
import yfinance as yf
import requests
import os

# Detect Engulfing
def is_engulfing(c_prev, c_now):
    return (
        c_prev['Open'] > c_prev['Close'] and c_now['Open'] < c_now['Close'] and
        c_now['Open'] <= c_prev['Close'] and c_now['Close'] >= c_prev['Open']
    ) or (
        c_prev['Open'] < c_prev['Close'] and c_now['Open'] > c_now['Close'] and
        c_now['Open'] >= c_prev['Close'] and c_now['Close'] <= c_prev['Open']
    )

# Detect Spinning Top
def is_spinning(c):
    body = abs(c['Close'] - c['Open'])
    high_wick = c['High'] - max(c['Open'], c['Close'])
    low_wick = min(c['Open'], c['Close']) - c['Low']
    return body <= (high_wick + low_wick) * 0.3


def telegram_send(message):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    df = yf.download(args.stock, start=args.date, end=args.date)
    if df.empty:
        telegram_send(f"[ERROR] No data for {args.stock} on {args.date}")
        return

    df2 = yf.download(args.stock, period="5d")
    df2 = df2.reset_index()

    target_idx = df2[df2['Date'] == pd.to_datetime(args.date)].index
    if len(target_idx) == 0:
        telegram_send(f"No trading data for {args.stock} on {args.date}")
        return

    i = target_idx[0]
    if i == 0:
        telegram_send("Not enough previous data for pattern check")
        return

    prev_c = df2.iloc[i - 1]
    now_c = df2.iloc[i]

    patterns = []
    if is_engulfing(prev_c, now_c):
        patterns.append("Engulfing")
    if is_spinning(now_c):
        patterns.append("Spinning Top")

    if patterns:
        telegram_send(f"Backtest Result for {args.stock} on {args.date}: {', '.join(patterns)}")
    else:
        telegram_send(f"No pattern detected for {args.stock} on {args.date}")


if __name__ == "__main__":
    main()
