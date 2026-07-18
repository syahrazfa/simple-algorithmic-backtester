import pandas as pd

# Importing Local File
from tools import screener


def backtest(symbols, capital=10000):
    cash = capital
    position = 0        # 0 = flat, 1 = long, -1 = short
    trades = []          # realized pnl per closed trade
    returns = []         # pnl / capital per closed trade
    portfolio_value = []
    trade_log = []
    buy_price = 0        # entry price of the currently open position
    qty = 0               # size of the currently open position

    for symbol in symbols:
        sma = screener.sma_signals([symbol])[symbol]
        rsi = screener.rsi_signals([symbol])[symbol]
        bb = screener.bb_signals([symbol])[symbol]
        vsa = screener.vsa([symbol])[symbol]

        df = sma.merge(rsi[['timestamp', 'rsi']], on='timestamp') \
                .merge(bb[['timestamp', 'signal_bb']], on='timestamp') \
                .merge(vsa[['timestamp', 'vsa_momentum']], on='timestamp')

        for i, row in df.iterrows():
            # Layer 1 — Regime: persistent trend state from medium/slow SMA
            regime = 1 if row['signal_medium_slow'] == 1 else -1

            # Layer 2 — Trigger: fast/medium SMA cross event
            trigger_long = row['cross_fast_medium'] == 1
            trigger_short = row['cross_fast_medium'] == -1

            # Layer 3 — Timing filter: RSI + Bollinger Band extremes
            timing_ok_long = row['rsi'] < 70 or row['signal_bb'] == 1    # not overbought
            timing_ok_short = row['rsi'] > 30 or row['signal_bb'] == -1  # not oversold

            # Layer 4 — Conviction: VSA momentum must agree with direction
            conviction_long = row['vsa_momentum'] > 0
            conviction_short = row['vsa_momentum'] < 0

            if position == 0:
                # Entry
                if regime == 1 and trigger_long and timing_ok_long and conviction_long:
                    position = 1
                    buy_price = row['close']
                    qty = capital / buy_price
                    trade_log.append({
                        'symbol': symbol,
                        'timestamp': row['timestamp'],
                        'action': 'buy',
                        'price': buy_price,
                        'qty': qty,
                    })
                elif regime == -1 and trigger_short and timing_ok_short and conviction_short:
                    position = -1
                    buy_price = row['close']
                    qty = capital / buy_price
                    trade_log.append({
                        'symbol': symbol,
                        'timestamp': row['timestamp'],
                        'action': 'short',
                        'price': buy_price,
                        'qty': qty,
                    })

            else:
                exit_long = position == 1 and regime == -1
                exit_short = position == -1 and regime == 1

                if exit_long or exit_short:
                    sell_price = row['close']
                    pnl = (sell_price - buy_price) * qty * position  # qty scales it, position sets sign
                    cash += pnl

                    trades.append(pnl)
                    returns.append(pnl / capital)
                    trade_log.append({
                        'symbol': symbol,
                        'timestamp': row['timestamp'],
                        'action': 'sell' if position == 1 else 'cover',
                        'price': sell_price,
                        'pnl': pnl,
                    })

                    position = 0
                    buy_price = 0
                    qty = 0

            # Mark-to-market equity curve, every bar
            unrealized = (row['close'] - buy_price) * qty * position if position != 0 else 0
            portfolio_value.append({
                'symbol': symbol,
                'timestamp': row['timestamp'],
                'value': cash + unrealized,
            })

    return {
        'final_cash': cash,
        'trades': trades,
        'returns': returns,
        'portfolio_value': portfolio_value,
        'trade_log': trade_log,
    }


if __name__ == '__main__':
    symbols = ["BTCUSDT", "ETHUSDT", "LTCUSDT"]
    result = backtest(symbols)

    trades = result['trades']

    print(f"Final cash: {result['final_cash']:.2f}")
    print(f"Total trades: {len(trades)}")

    if trades:
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]

        win_rate = len(wins) / len(trades)
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0
        rr = avg_win / avg_loss if avg_loss > 0 else float('inf')

        print(f"Win rate: {win_rate:.1%}")
        print(f"Avg win: {avg_win:.2f}")
        print(f"Avg loss: {avg_loss:.2f}")
        print(f"Risk-reward ratio: {rr:.2f}")

        # Expectancy: what a win-rate + RR alone can't tell you —
        # whether the strategy is profitable per trade on average
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        print(f"Expectancy per trade: {expectancy:.2f}")