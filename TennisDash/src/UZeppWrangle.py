import sqlite3
import pandas as pd
import pytz

def UZeppWrangle(db_path, start_date=None, end_date=None):
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Construct query
    query = "SELECT * FROM swings"
    
    # Read query results into DataFrame
    df = pd.read_sql(query, conn)
    df = df.sort_index()  
    
    # Convert l_id to datetime with explicit format
    df['l_id'] = pd.to_datetime(df['l_id'], unit='ms')
    
    # Set timezone
    az_timezone = pytz.timezone('America/Phoenix')
    df['l_id'] = df['l_id'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    
    # Format datetime
    df['l_id'] = df['l_id'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')
    
    # Convert back to datetime (now with consistent format)
    df['l_id'] = pd.to_datetime(df['l_id'], format='%m-%d-%Y %I:%M:%S.%f %p')
    
    df.dropna(inplace=True)
    df = df.sort_values("l_id")
    
    # Replace # with descriptions
    hand_type = {1: "BH", 0: "FH"}
    swing_type = {4: "VOLLEY", 3: "SERVE", 2: "TOPSPIN", 0: "SLICE", 1: "FLAT", 5: "SMASH"}
    df['swing_type'] = df['swing_type'].replace(swing_type)
    df['hand_type'] = df['swing_side'].replace(hand_type)
    df['stroke'] = df['swing_type'] + df['hand_type']
    
    # add new impact column
    df['diffxy'] = 0.5 * df['impact_position_x'] - df['impact_position_y']
    
    # Rename l_id to time
    df.rename(columns={'l_id': 'time'}, inplace=True)
    
    # Filter the DataFrame based on the date range if provided
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
    else:
        # If no date range provided, use the default range
        df = df[(df['time'] > pd.to_datetime('2024-06-12')) & (df['time'] < pd.to_datetime('2024-06-14'))]
    
    # Format with fractional seconds to match Apple Watch
    df['timestamp'] = df['time'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')
    
    conn.close()
    
    return df
