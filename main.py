import pandas as pd
from tools import fetch
from tools import etl

if __name__ == "__main__":

    symbols = ["BTCUSDT", "ETHUSDT", "LTCUSDT"]
    interval = "1h"

    # Manual range test
    start = pd.Timestamp("2026-01-01").value // 1_000_000
    end   = pd.Timestamp("2026-04-01").value // 1_000_000

    raw_json = fetch.fetch(symbols=symbols, interval=interval, start=start, end=end)

    dfs = {}
    for symbol in symbols:
        df = fetch.json_to_df(raw_json[symbol], symbol)
        df = etl.cleaning(df)
        etl.to_database(df)

        dfs[symbol] = df

    end_ts = pd.Timestamp(end, unit="ms")

    while True:
        result = etl.incremental_update(symbols=symbols, interval=interval ,end=end)

        if not result:
            print('No new data')
            break

        reached_end = True
        for symbol, df in result.items():
            dfs[symbol] = df
            print(f'[Incremenetal] {symbol}: till {df["timestamp"].max()}')
            if df['timestamp'].max() < end_ts:
                reached_end = False

        if reached_end:
            print('Reached end')
            break

    print(f"{symbol}: {len(df)} rows, from {df['timestamp'].min()} to {df['timestamp'].max()}")