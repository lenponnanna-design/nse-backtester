import yfinance as yf
import argparse
from datetime import datetime, timedelta

# -------------------------
# Pattern detection helpers
# -------------------------

def is_bullish_engulfing(prev, curr):
    return (
        prev["Close"] < prev["Open"] and
        curr["Close"] > curr["Open"] and
        curr["Open"] < prev["Close"] and
        curr["Close"] > prev["Open"]
    )

def is_bearish_engulfing(prev, curr):
    return (
        prev["Close"] > prev["Open"] and
        curr["Close"] < curr["Open"] and
        curr["Open"] > prev["Close"] and
        curr["Close"] < prev["Open"]
    )

def is_spinning_top(candle):
    body = abs(candle["Close"] - candle["Open"])
    high_tail = candle["High"] - max(candle["Close"], candle["Open"])
    low_tail = min(candle["Close"], candle["Open"]) - candle["Low"]
    return body < (high_tail + low_tail) * 0.3

# -------------------------
# Fetch candle data
# -------------------------

def fetch_daily_candle(symbol, date):
    dt = datetime.strptime(date, "%Y-%m-%d")

    start = (dt - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=5)).strftime("%Y-%m-%d")

    df = yf.download(symbol, start=start, end=end, progress=False)

    if df.empty:
        print("No data found for this stock/date.")
        return None, None

    df.index = df.index.strftime("%Y-%m-%d")

    if date not in df.index:
        print("No candle found on that date (market holiday or invalid date).")
        return None, None

    idx = list(df.index).index(date)

    if idx == 0:
        print("No previous candle available.")
        return None, None

    prev = df.iloc[idx - 1]
    curr = df.loc[date]

    return prev, curr

# -------------------------
# Main
# -------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", required=True, help="Stock symbol e.g. IOC.NS")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    prev, curr = fetch_daily_candle(args.stock, args.date)

    if prev is None or curr is None:
        return

    print("\n--- Candle Data ---")
    print("Previous:", prev.to_dict())
    print("Current :", curr.to_dict())
    print("-------------------\n")

    # Pattern Detection
    if is_bearish_engulfing(prev, curr):
        print(f"🔥 BEARISH ENGULFING detected for {args.stock} on {args.date}")
        return

    if is_bullish_engulfing(prev, curr):
        print(f"🔥 BULLISH ENGULFING detected for {args.stock} on {args.date}")
        return

    if is_spinning_top(curr):
        print(f"🌀 SPINNING TOP detected for {args.stock} on {args.date}")
        return

    print(f"No pattern found for {args.stock} on {args.date}")

if __name__ == "__main__":
    main()
