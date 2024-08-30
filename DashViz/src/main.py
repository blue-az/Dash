import warnings
import base64
import io
from datetime import date
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from dash import Dash, Input, Output, dcc, html, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go

# Build your `wrangle` function here
def wrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
    SELECT _id, date, TYPE, TRACKID, ENDTIME, CAL, AVGHR, MAX_HR from TRACKRECORD
    """

    # Read query results into DataFrame
    df = pd.read_sql(query, conn, index_col="_id")
    # Remove HR outliers
    df = df[df["AVGHR"] > 50]
    df = df[df["MAX_HR"] > 50]
    # Create duration column from timestamps
    # Convert Unix timestamps to datetime objects
    df['TRACKID'] = pd.to_datetime(df['TRACKID'], unit='s')
    df['ENDTIME'] = pd.to_datetime(df['ENDTIME'], unit='s')
    
    # Calculate the duration in minutes
    df['duration_minutes'] = (df['ENDTIME'] - df['TRACKID']).dt.total_seconds() / 60
    df['duration_minutes'] = df['duration_minutes'].round()
    # Remove duration outliers
    df = df[df["duration_minutes"] > 10]

    # Replace type with sport 
    new_type = {16: "Free", 10: "IndCyc", 9: "OutCyc", 12: "Elliptical", 60: "Yoga", 14: "Swim" }
    df['TYPE'] = df['TYPE'].replace(new_type)

    return df

# PC path
file_path = "/home/blueaz/Downloads/SensorDownload/Sep14/MiiFit.db"
warnings.simplefilter("ignore", UserWarning)

df = wrangle(file_path)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Choose Date Range"),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=date(2020, 1, 1),
        max_date_allowed=date.today(),
        initial_visible_month=date.today(),
        end_date=date.today(),
    ),
    html.Div(id='output-container-date-picker-range'),
    html.H1("Separate by activity?"),
    dcc.RadioItems(
        options=[
            {"label": "hue", "value": True},
            {"label": "no hue", "value": False}
        ],
        value=True,
        id="hue-button"
    ),
    html.H1("Pairs plot"),
    dcc.Graph(id="pairs-plot", style={'width': '80vh', 'height': '80vh'}),
    html.H1("New element"),
])

# Initialize the start_date_object and end_date_object
start_date_object = date.today()
end_date_object = date.today()

# Callback for updating the text output
@app.callback(
    Output('output-container-date-picker-range', 'children'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def update_date_text_output(start_date, end_date):
    global start_date_object, end_date_object  # Use the global variables
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string
    if len(string_prefix) == len('You have selected: '):
        return 'Select a date to see it displayed here'
    else:
        return string_prefix

# Callback for updating the chart
@app.callback(
    Output("pairs-plot", "figure"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'),
    Input("hue-button", "value"),
    prevent_initial_call=True
)
def serve_scatter(start_date, end_date, hue):
    if isinstance(hue, bool):
        if start_date is not None and end_date is not None:
            start_date_object = date.fromisoformat(start_date)
            end_date_object = date.fromisoformat(end_date)
            df_subset = sub_date(start_date_object, end_date_object)
        else:
            df_subset = df  # Use the entire DataFrame when no date range is selected

        # Create a Seaborn PairGrid
        pair_grid = sns.pairplot(df_subset, hue="TYPE" if hue else None)
        
        # Save the PairGrid as an image
        buf = io.BytesIO()
        pair_grid.savefig(buf, format="png")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")

        # Display the image using a dcc.Graph
        return {
            "data": [{"x": [], "y": []}],  # Empty data
            "layout": {
                "images": [{
                    "source": f"data:image/png;base64,{img_base64}",
                    "x": 0,
                    "y": 1,
                    "sizex": 1,
                    "sizey": 1,
                    "xref": "paper",
                    "yref": "paper",
                }],
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "autosize": False  # Disable autosize to have control over the layout size
            }
        }

def sub_date(start_date, end_date):
    # Convert the 'DATE' column to datetime.date
    df['DATE'] = pd.to_datetime(df['DATE']).dt.date
    # Subset dates
    df_subset = df[df['DATE'].between(start_date, end_date)]
    return df_subset

if __name__ == '__main__':
    app.run(debug=True)
