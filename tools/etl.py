# Library
import sqlite3 as sql
import pandas as pd

# Importing Local File
import fetch


def cleaning(df):
    """
    cleanng() is a function to clean before uploaded to the database
    """
    df = df.copy()

    col_name = {
        '0' : 'timestamp',
        '1' : 'open',
        '2' : 'high',
        '3' : 'low',
        '4' : 'close',
        '5' : 'volume',
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
        'volume'
    ]]

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.sort_values("timestamp")

    return df



def to_database(df):
    # Connecting the database
    with sql.connect('../data/data.db') as conn:
        conn.cursor()

    df.to_sql(
        name="bronze_candles",
        con=conn,
        if_exists="append",
        index=False,
    )

    conn.close()

def incremental_update(df):
    """
    Updating the start time parameter for fetching data
    """
    with sql.connect('../data/data.db') as conn:
        conn.cursor()

    # Take timestamp data from database
    (conn.execute(
    """
    SELECT timestamp from bronze_candles
        
    """))


def backfill(symbols, interval):
        """
        Backfill historical data
        """
        INTERVAL_MS = {
            "1m": 60_000,
            "5m": 300_000,
            "15m": 900_000,
            "1h": 3_600_000,
            "4h": 14_400_000,
            "1d": 86_400_000,
        }
        end = None

        # Loop
        while True:

            # Fetch
            raw_json = fetch.fetch(
                symbols=symbols,
                interval=interval,
                end=end,
            )

            # Checking if there's no more data
            if len(raw_json[symbols[0]]) == 0:
                break

            # Save first_open of all symbols
            first_opens = []

        for symbol in symbols:
            df = fetch.json_to_df(raw_json[symbol], symbol)
            df = cleaning(df) # is this count as variable abuse?


