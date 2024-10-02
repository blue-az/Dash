import warnings
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
from dash import Dash, Input, Output, dcc, html, dash_table

# Build your `wrangle` function here
def wrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
    SELECT _id, DATE, TYPE, TRACKID, ENDTIME, CAL, AVGHR, MAX_HR from TRACKRECORD
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

    # New section for summary statistics
    html.H1("Summary Statistics"),
    dash_table.DataTable(id='summary-table', style_table={'width': '50vh'}),
])

# Callback for updating the text output
@app.callback(
    Output('output-container-date-picker-range', 'children'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def update_date_text_output(start_date, end_date):
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

# Callback for updating the chart and summary statistics
@app.callback(
    [Output("pairs-plot", "figure"),
     Output("summary-table", "data"),
     Output("summary-table", "columns")],
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'),
    Input("hue-button", "value"),
    prevent_initial_call=True
)
def serve_scatter(start_date, end_date, hue):
    if start_date is not None and end_date is not None:
        start_date_object = date.fromisoformat(start_date)
        end_date_object = date.fromisoformat(end_date)
        df_subset = sub_date(start_date_object, end_date_object)
    else:
        df_subset = df  # Use the entire DataFrame when no date range is selected

    # Scatter matrix plot
    fig = px.scatter_matrix(
        df_subset,
        dimensions=["AVGHR", "MAX_HR", "CAL", "duration_minutes"],
        color="TYPE" if hue else None,
        title="Pairs Plot"
    )
    fig.update_layout(
        autosize=False,
        width=800,
        height=800,
    )

    # Calculate summary statistics
    summary_stats = df_subset[["AVGHR", "MAX_HR", "CAL"]].describe()

    # Convert summary statistics to a format suitable for Dash DataTable
    data = summary_stats.reset_index().to_dict('records')
    columns = [{"name": i, "id": i} for i in summary_stats.columns.insert(0, "index")]

    return fig, data, columns

def sub_date(start_date, end_date):
    # Check if 'DATE' column exists
    if 'DATE' not in df.columns:
        raise ValueError("'DATE' column is missing from the DataFrame")

    # Convert the 'DATE' column to datetime, handling errors
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')

    # Drop rows where conversion failed
    df.dropna(subset=['DATE'], inplace=True)

    # Convert datetime to date
    df['DATE'] = df['DATE'].dt.date

    # Subset dates
    df_subset = df[df['DATE'].between(start_date, end_date)]
    return df_subset

if __name__ == '__main__':
    app.run(debug=True)

