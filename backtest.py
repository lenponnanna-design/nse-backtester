import yfinance as yf
import argparse
from datetime import datetime, timedelta

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

def fetch_daily_candle(symbol, date):
    start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")

    data = yf.download(symbol, start=start, end=end, progress=False)

    if data.empty:
        print("No data received.")
        return None, None

    # FIX MULTI-INDEX COLUMNS
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    data.index = data.index.strftime("%Y-%m-%d")

    if date not in data.index:
        print(f"No candle for {date}.")
        return None, None

    curr = data.loc[date]
    idx = list(data.index).index(date)

    if idx == 0:
        print("No previous candle.")
        return None, None

    prev = data.loc[list(data.index)[idx - 1]]

    return prev, curr

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

    if is_bearish_engulfing(prev, curr):
        print(f"🔥 BEARISH ENGULFING detected in {args.stock} on {args.date}")
        return

    if is_bullish_engulfing(prev, curr):
        print(f"🔥 BULLISH ENGULFING detected in {args.stock} on {args.date}")
        return

    if is_spinning_top(curr):
        print(f"🌀 SPINNING TOP detected in {args.stock} on {args.date}")
        return

    print("No pattern detected.")

if __name__ == "__main__":
    main()
