# Library
import matplotlib
matplotlib.use('TkAgg')

import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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

def sma_signals(symbols, rolls=(20, 50, 200)):

    rolls = sorted(rolls)
    fast,medium,slow = rolls[0],rolls[-2],rolls[-1]
    result = {}
    for symbol in symbols:
        df = get_data(symbol)
        df = df[['timestamp','close','symbol']]
        for roll in rolls:
            df = add_sma(df, roll)

        # Entry Timing
        df['signal_fast_medium'] = (df[f'sma{fast}'] > df[f'sma{medium}']).astype(int)
        df['cross_fast_medium'] = df['signal_fast_medium'].diff()

        # Golden/Death Cross
        df['signal_medium_slow'] = (df[f'sma{medium}'] > df[f'sma{slow}']).astype(int)
        df['cross_medium_slow'] = df['signal_medium_slow'].diff()

        result[symbol] = df

    return result

def rsi_signals(symbols):

    n = 14

    result = {}
    for symbol in symbols:
        df = get_data(symbol)
        df = df[['timestamp','close','symbol']]
        df['change'] = df['close'].diff()
        df['gain'] = df['change'].clip(lower=0)
        df['loss'] = -df['change'].clip(upper=0)

        avg_gain = [None] * len(df)
        avg_loss = [None] * len(df)

        # Initialize first n candle with simple adverage
        avg_gain[n] = df['gain'].iloc[1:n + 1].mean()
        avg_loss[n] = df['loss'].iloc[1:n + 1].mean()

        # Recursive Wilder's smoothing
        for i in range(n+1, len(df)):
            avg_gain[i] = ((avg_gain[i-1]) * (n-1) + df['gain'].iloc[i]) / n
            avg_loss[i] = (avg_loss[i-1] * (n-1) + df['loss'].iloc[i]) / n

        df['avg_gain'] = avg_gain
        df['avg_loss'] = avg_loss

        rs = df['avg_gain'] / df['avg_loss']
        df['rsi'] = 100 - (100 / (1 + rs))

        result[symbol] = df
    return result

def bb_signals(symbols, k=2, rolls=20):
    result = {}
    for symbol in symbols:
        df = get_data(symbol)
        df = df[['timestamp', 'close', 'symbol']]

        df['bb_mid'] = df['close'].rolling(rolls).mean()
        df['bb_std'] = df['close'].rolling(rolls).std()
        df['bb_upper'] = df['bb_mid'] + k * df['bb_std']
        df['bb_lower'] = df['bb_mid'] - k * df['bb_std']

        # Signal Result
        df['signal_bb'] = 0
        df.loc[df['close'] < df['bb_lower'], 'signal_bb'] = 1  # oversold (up rebound potential)
        df.loc[df['close'] > df['bb_upper'], 'signal_bb'] = -1  # overbought (down rebound potential)

        result[symbol] = df
    return result

def vsa(symbols, rolls=20):
    result = {}
    for symbol in symbols:
        df = get_data(symbol)



symbol = "BTCUSDT"
fast, medium, slow = 20, 50, 200

df_sma = sma_signals([symbol])[symbol]
df_rsi = rsi_signals([symbol])[symbol]
df_bb = bb_signals([symbol])[symbol]

golden = df_sma[df_sma['cross_medium_slow'] == 1]
death = df_sma[df_sma['cross_medium_slow'] == -1]

# SMA Visualisation
plt.figure(figsize=(16, 6))
plt.plot(df_sma['timestamp'], df_sma['close'], label='Close', color='black', linewidth=0.8, alpha=0.6)
plt.plot(df_sma['timestamp'], df_sma[f'sma{fast}'], label=f'SMA {fast}')
plt.plot(df_sma['timestamp'], df_sma[f'sma{medium}'], label=f'SMA {medium}')
plt.plot(df_sma['timestamp'], df_sma[f'sma{slow}'], label=f'SMA {slow}')
plt.scatter(golden['timestamp'], golden[f'sma{medium}'], marker='^', color='green', s=100, zorder=5, label='Golden Cross')
plt.scatter(death['timestamp'], death[f'sma{medium}'], marker='v', color='red', s=100, zorder=5, label='Death Cross')
plt.legend()
plt.title(f'{symbol} - SMA')
plt.tight_layout()

# Bolinger Band Visualisation
plt.figure(figsize=(16, 6))
plt.plot(df_bb['timestamp'], df_bb['close'], label='Close', color='black', linewidth=0.8)
plt.plot(df_bb['timestamp'], df_bb['bb_mid'], label='Mid (SMA20)', color='orange')
plt.plot(df_bb['timestamp'], df_bb['bb_upper'], label='Upper', color='gray', linestyle='--')
plt.plot(df_bb['timestamp'], df_bb['bb_lower'], label='Lower', color='gray', linestyle='--')
plt.fill_between(df_bb['timestamp'], df_bb['bb_lower'], df_bb['bb_upper'], alpha=0.15, color='blue')
plt.legend()
plt.title(f'{symbol} - Bollinger Bands')
plt.tight_layout()


# RSI Visualisation
plt.figure(figsize=(16, 6))
plt.plot(df_rsi['timestamp'], df_rsi['rsi'], label='RSI 14', color='purple')
plt.axhline(70, color='red', linestyle='--', linewidth=1, label='Overbought (70)')
plt.axhline(30, color='green', linestyle='--', linewidth=1, label='Oversold (30)')
plt.ylim(0, 100)
plt.xlabel('Date')
plt.legend()
plt.title(f'{symbol} - RSI')
plt.tight_layout()
plt.show()