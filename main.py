from tools import fetch

if __name__ == "__main__":

     symbols = ["BTCUSDT", "ETHUSDT", "LTCUSDT"]

     raw_json = fetch.fetch(symbols=symbols, interval="1h")

     dfs = {}

     for symbol in symbols:
         dfs[symbol] = fetch.json_to_df(raw_json[symbol], symbol)