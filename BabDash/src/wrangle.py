import sqlite3
import pandas as pd
import pytz

# Build your `wrangle` function here
def wrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query (You can modify the query as needed for your data)
    query = """
    SELECT time, type, spin, 
    StyleScore, StyleValue, 
    EffectScore, EffectValue,
    SpeedScore, SpeedValue,
    stroke_counter 
    FROM SyntheticData
    """

    # Read query results into DataFrame
    df = pd.read_sql(query, conn)
    
    # Convert Unix timestamps to datetime objects and format
    df['time'] = pd.to_datetime(df['time']/10000, unit='s')
    az_timezone = pytz.timezone('America/Phoenix')
    df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    df['time'] = df['time'].dt.strftime('%m-%d-%Y %I:%M:%S %p')

    conn.close()
    
    return df

