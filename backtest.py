import yfinance as yf
import argparse
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# -------------------------
# Telegram Function
# -------------------------
def telegram_message(text):
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Telegram not configured (BOT_TOKEN or CHAT_ID missing).")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}

    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print("❌ Telegram send error:", r.text)
        else:
            print("✔ Telegram message sent")
    except Exception as e:
        print("❌ Telegram exception:", e)


# -------------------------
# Pattern Functions
# -------------------------
def is_bullish_engulfing(prev, curr):
    return (
        prev['Close'] < prev['Open'] and
        curr['Close'] > curr['Open'] and
        curr['Open'] < prev['Close'] and
        curr['Close'] > prev['Open']
    )

def is_bearish_engulfing(prev, curr):
    return (
        prev['Close'] > prev['Open'] and
        curr['Close'] < curr['Open'] and
        curr['Open'] > prev['Close'] and
        curr['Close'] < prev['Open']
    )

def is_spinning_top(candle):
    body = abs(candle['Close'] - candle['Open'])
    high_tail = candle['High'] - max(candle['Close'], candle['Open'])
    low_tail = min(candle['Close'], candle['Open']) - candle['Low']
    return body < (high_tail + low_tail) * 0.3


# -------------------------
# Fetch Candle
# -------------------------
def fetch_daily_candle(symbol, date):
    start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")

    data = yf.download(symbol, start=start, end=end, progress=False)

    if data.empty:
        print("No data received.")
        return None, None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    data.index = data.index.strftime("%Y-%m-%d")

    if date not in data.index:
        print(f"No candle found for {date}")
        return None, None

    curr = data.loc[date]
    idx = list(data.index).index(date)

    if idx == 0:
        print("No previous candle available")
        return None, None

    prev = data.loc[list(data.index)[idx - 1]]

    return prev, curr


# -------------------------
# Main
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    prev, curr = fetch_daily_candle(args.stock, args.date)

    if prev is None or curr is None:
        return

    print("\n--- Candle Data ---")
    print("Previous:", prev.to_dict())
    print("Current:", curr.to_dict())
    print("-------------------\n")

    # --- Pattern Checks ---
    if is_bearish_engulfing(prev, curr):
        msg = f"🔥 *BEARISH ENGULFING detected*\n\nStock: {args.stock}\nDate: {args.date}"
        telegram_message(msg)
        print(msg)
        return

    if is_bullish_engulfing(prev, curr):
        msg = f"🔥 *BULLISH ENGULFING detected*\n\nStock: {args.stock}\nDate: {args.date}"
        telegram_message(msg)
        print(msg)
        return

    if is_spinning_top(curr):
        msg = f"🌀 *SPINNING TOP detected*\n\nStock: {args.stock}\nDate: {args.date}"
        telegram_message(msg)
        print(msg)
        return

    print("No pattern detected for this date.")


if __name__ == "__main__":
    main()
