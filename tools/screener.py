# Library
import matplotlib
matplotlib.use('TkAgg')
from mpl_toolkits.mplot3d import Axes3D
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

        df['spread'] = df['high'] - df['low']
        df['close_loc'] = (df['close'] - df['low']) / df['spread']
        df['direction'] = (2 * df['close_loc']) - 1

        # Z-score
        df['spread_z'] = (df['spread'] - df['spread'].rolling(rolls).mean()) / df['spread'].rolling(rolls).std()
        df['volume_z'] = (df['volume'] - df['volume'].rolling(rolls).mean()) / df['volume'].rolling(rolls).std()

        # Vector Decomposition
        df['intensity'] = np.sqrt(df['spread_z']**2 + df['volume_z']**2)
        df['health'] = (df['spread_z'] + df['volume_z']) / np.sqrt(2)
        df['churn'] = (df['volume_z'] - df['spread_z']) / np.sqrt(2)

        # Smoothed Momentum
        df['health_smooth'] = df['health'].ewm(span=rolls, adjust=False).mean()
        df['trend_direction'] = np.sign(df['close'].ewm(span=rolls * 2, adjust=False).mean().diff())
        df['vsa_momentum'] = df['health_smooth'] * df['trend_direction']

        result[symbol] = df

    return result

symbol = "BTCUSDT"
fast, medium, slow = 20, 50, 200

df_sma = sma_signals([symbol])[symbol]
df_rsi = rsi_signals([symbol])[symbol]
df_bb = bb_signals([symbol])[symbol]
df_vsa = vsa([symbol])[symbol]

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


# VSA Visualisation - 3D Vector Space
d = df_vsa.dropna(subset=['spread_z', 'volume_z', 'close_loc'])

fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(d['spread_z'], d['volume_z'], d['close_loc'],
                 c=d['close_loc'], cmap='RdYlGn', s=14, alpha=0.7)
ax.set_xlabel('spread_z (result)')
ax.set_ylabel('volume_z (effort)')
ax.set_zlabel('close_loc (0=low, 1=high)')
ax.set_title(f'{symbol} - VSA Vector Space')
fig.colorbar(sc, label='close_loc', shrink=0.6)
plt.tight_layout()

# VSA Visualisation - Last N bars as vectors from origin
n = 60
d_recent = df_vsa.dropna(subset=['spread_z', 'volume_z', 'close_loc']).tail(n)
origin = np.zeros(len(d_recent))
colors = plt.cm.RdYlGn(d_recent['close_loc'])

fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection='3d')
ax.quiver(origin, origin, origin,
          d_recent['spread_z'], d_recent['volume_z'], d_recent['close_loc'],
          color=colors, arrow_length_ratio=0.08, linewidth=1)

# Force limits to actually contain the vectors
ax.set_xlim(d_recent['spread_z'].min(), d_recent['spread_z'].max())
ax.set_ylim(d_recent['volume_z'].min(), d_recent['volume_z'].max())
ax.set_zlim(0, 1)  # close_loc is always 0-1 by definition

ax.set_xlabel('spread_z (result)')
ax.set_ylabel('volume_z (effort)')
ax.set_zlabel('close_loc')
ax.set_title(f'{symbol} - Last {n} Bars as VSA Vectors')
plt.tight_layout()

# Show all plot
plt.show()