import pandas as pd
import pytz
from datetime import datetime

def WatchWrangle(file_path, start_date=None, end_date=None):
    # Read into DataFrame
    df = pd.read_csv(file_path)
    
    # Convert Unix timestamps to datetime objects
    df["timestamp"] = pd.to_datetime(df['time'], unit='ns')
    
    # Convert to desired timezone (America/Phoenix)
    az_timezone = pytz.timezone('America/Phoenix')
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(az_timezone)
    
    # Filter the DataFrame based on the date range if provided
    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    # Format timestamp with fractional seconds
    df['timestamp'] = df['timestamp'].dt.strftime('%m-%d-%Y %I:%M:%S.%f %p')
    
    return df
