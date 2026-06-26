import requests
import pandas as pd
import sqlite3 as sql
import os


def fetch(symbols,interval, start=None, end=None):
    '''
    Fetch data from API, may pick more than one symbols to fetch
    '''
    folder = os.path.join(os.path.dirname(__file__), '../../simple-sma', 'data')
    url = f'https://data-api.binance.vision/api/v3/klines'

    result = {}



    for symbol in symbols:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit' : 1000,
        }

        if start is not None:
            params['startTime'] = start
        if end is not None:
            params['endTime'] = end

        # Request API
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()

        result[symbol] = r.json()

    return result

def json_to_df(data, symbol):
    df = pd.DataFrame(data)
    df["symbol"] = symbol
    return df
