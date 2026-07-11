# Library
import sqlite3 as sql
import pandas as pd

# Importing Local File
from tools import fetch

import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "data.db"
)

def cleaning(df):
    """
    cleanng() is a function to clean before uploaded to the database
    """
    df = df.copy()

    col_name = {
        0 : 'timestamp',
        1 : 'open',
        2 : 'high',
        3 : 'low',
        4 : 'close',
        5 : 'volume',
    }

    # Renaming each columns that we only need
    df = df.rename(columns = col_name)

    # Filtering the dataframe to only columns that we need
    df = df[[
        'timestamp',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'symbol'
    ]]

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df



def to_database(df):
    # Connecting the database

    import os

    DB_PATH = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "data.db"
    )

    with sql.connect(DB_PATH) as conn:
        df.to_sql(
            name="bronze_candles",
            con=conn,
            if_exists="append",
            index=False,
        )

def incremental_update(symbols, interval, end=None):
    """
    Updating the start time parameter for fetching data
    """

    with sql.connect(DB_PATH) as conn:
        last_timestamp = conn.execute(
            "SELECT MAX(timestamp) FROM bronze_candles"
        ).fetchone()[0]

    start = pd.Timestamp(last_timestamp).value // 1_000_000 + 1

    raw_json = fetch.fetch(
        symbols=symbols,
        interval=interval,
        start=start,
        end=end,
    )

    dfs = {}
    for symbol in symbols:
        if len(raw_json[symbol]) == 0:
            continue
        df = fetch.json_to_df(raw_json[symbol], symbol)
        df = cleaning(df)
        to_database(df)
        dfs[symbol] = df

    return dfs