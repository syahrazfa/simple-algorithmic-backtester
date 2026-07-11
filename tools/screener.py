# Library
import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), ".." ,"data", "data.db")

# Loading database
def get_data(symbol, interval=None):
    with sql.connect(DB_PATH) as conn:
        df = pd.read_sql(
            """
            SELECT * FROM bronze_candles
            WHERE symbol = ?
            ORDER BY timestamp
            """,
            conn,
            params=(symbol,),
        )
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Convert object to numeric

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

df = get_data("BTCUSDT")

# Manually add SMA
def add_sma(df, roll):
    df = df.copy()
    df[f'sma{roll}'] = df['close'].rolling(roll).mean()
    return df

df = get_data("BTCUSDT")
df = add_sma(df, roll=20)
df = add_sma(df, roll=50)

print(df['close'].describe())
print(df['close'].min(), df['close'].max())
print(df.duplicated(subset=['timestamp', 'symbol']).sum())  # cek duplikat juga

plt.figure(figsize=(14, 6))
plt.plot(df['timestamp'], df['close'], label='close', alpha=0.6)
plt.plot(df['timestamp'], df['sma20'], label='SMA 20')
plt.plot(df['timestamp'], df['sma50'], label='SMA 50')
plt.legend()
plt.title('BTCUSDT')
plt.show()