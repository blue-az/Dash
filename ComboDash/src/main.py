import warnings
import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import UZeppWrangle
import WatchWrangle
import BabWrangle
import pytz
import numpy as np

# Suppress warnings
warnings.simplefilter("ignore", UserWarning)

# Path for all three sensors
Apple_path = "/home/blueaz/Downloads/SensorDownload/Compare/WristMotion.csv"
Bab_path = "/home/blueaz/Python/Sensors/Bab/BabWrangle/src/BabPopExt.db"
UZepp_path = "/home/blueaz/Downloads/SensorDownload/Compare/ztennis.db"

# Data wrangling functions
def normalize_column(dfa, dfb, ref_col, norm_col, new_col_name):
    min_A = dfa[ref_col].min()
    max_A = dfa[ref_col].max()
    min_B = dfb[norm_col].min()
    max_B = dfb[norm_col].max()
    def normalize(x, min_B, max_B, min_A, max_A):
        return ((x - min_B) * (max_A - min_A) / (max_B - min_B)) + min_A
    dfb[new_col_name] = dfb[norm_col].apply(normalize, args=(min_B, max_B, min_A, max_A))

# Load and process data
dfa = WatchWrangle.WatchWrangle(Apple_path) 
dfb = BabWrangle.BabWrangle(Bab_path) 
dfu = UZeppWrangle.UZeppWrangle(UZepp_path)

# Process Zepp U sensor data
normalize_column(dfb, dfu, 'EffectScore', 'ball_spin', 'ZIQspin')
normalize_column(dfb, dfu, 'SpeedScore', 'racket_speed', 'ZIQspeed')
absx = 0 - dfu['impact_position_x'].abs()
absy = 0 - dfu['impact_position_y'].abs()
dfu['abs_imp'] = 0 + (absx + absy)
normalize_column(dfb, dfu, 'StyleScore', 'abs_imp', 'ZIQpos')
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspin'] = dfu['ZIQspin'] * 2
dfu.loc[dfu['stroke'] != 'SERVEFH', 'ZIQspeed'] = dfu['ZIQspeed'] * 1.6 
dfu['ZIQ'] = dfu['ZIQspeed'] + dfu['ZIQspin'] + dfu['ZIQpos']
dfu.loc[dfu['stroke'] == 'SERVEFH', 'ZIQ'] = dfu['ZIQ'] * .9 
dfu = dfu[dfu["dbg_acc_1"] < 10000]
dfu = dfu[dfu["dbg_acc_3"] < 10000]
dfu = dfu[dfu["ZIQ"] < 10000]

# Merge datasets
tolerance = pd.Timedelta('5s')
shift = 5 
dfb['time'] = dfb['time'] - pd.Timedelta(seconds=shift) 
dfu_dba_merge = pd.merge_asof(dfu, dfb, left_on='time', right_on='time', tolerance=tolerance, direction='nearest')

shift = -1 
dfa['timestamp'] = pd.to_datetime(dfa['timestamp'])
dfu['timestamp'] = pd.to_datetime(dfu['timestamp'])
dfa['timestamp'] = dfa['timestamp'] - pd.Timedelta(seconds=shift) 
df_merged = pd.merge_asof(dfa, dfu, left_on='timestamp', right_on='timestamp', tolerance=tolerance, direction='nearest')

# Normalize columns
normalize_column(dfu, df_merged, 'dbg_acc_1', 'accelerationX', 'AccXNorm1')
normalize_column(dfu, df_merged, 'dbg_gyro_1', 'accelerationX', 'Gyro1Norm1')

# App setup
app = dash.Dash(__name__)

# Define available metrics for dropdowns
metrics = ['AccXNorm1', 'Gyro1Norm1', 'ZIQ', 'ZIQspeed', 'ZIQspin', 'ZIQpos', 'ball_spin', 'racket_speed']

# Layout
app.layout = html.Div([
    html.H1("Multi-Sensor Tennis Data Dashboard"),
    html.H1("Choose Date Range"),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=date(2020, 1, 1),
        max_date_allowed=date.today(),
        initial_visible_month=date.today(),
        end_date=date.today(),
    ),
    html.Div(id='output-container-date-picker-range'),
    html.Div([
        html.Div([
            html.Label("X-axis metric"),
            dcc.Dropdown(
                id='x-axis-dropdown',
                options=[{'label': col, 'value': col} for col in metrics],
                value='AccXNorm1',
                clearable=False
            ),
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Y-axis metric"),
            dcc.Dropdown(
                id='y-axis-dropdown',
                options=[{'label': col, 'value': col} for col in metrics],
                value='Gyro1Norm1',
                clearable=False
            ),
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='sensor-plot'),

    html.Label("Number of Bins for Histogram"),
    dcc.Slider(
        id='bin-slider',
        min=5,
        max=100,
        step=1,
        value=20,
        marks={i: str(i) for i in range(5, 101, 10)}
    ),

    dcc.Graph(id='histogram-plot'),

    html.Div(id='summary-stats', style={'margin-top': '20px'})
])

# Correcting the input ID in the callback
@app.callback(
    [Output('sensor-plot', 'figure'),
     Output('histogram-plot', 'figure'),
     Output('summary-stats', 'children')],
    [Input('my-date-picker-range', 'start_date'),  # Update this ID
     Input('my-date-picker-range', 'end_date'),    # Update this ID
     Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value'),
     Input('bin-slider', 'value')]
)
def update_output(start_date, end_date, x_axis, y_axis, num_bins):
    # Convert start_date and end_date from strings to datetime objects
    if start_date:
        start_date = pd.to_datetime(start_date)
    else:
        start_date = df_merged['timestamp'].min()  # Default to min timestamp if no start date is provided
    
    if end_date:
        end_date = pd.to_datetime(end_date)
    else:
        end_date = df_merged['timestamp'].max()  # Default to max timestamp if no end date is provided

    # Filter the data based on selected date range
    filtered_df = df_merged[
        (df_merged['timestamp'] >= start_date) &
        (df_merged['timestamp'] <= end_date)
    ]

    # Generate sensor plot
    sensor_fig = go.Figure()
    sensor_fig.add_trace(go.Scatter(x=filtered_df[x_axis], y=filtered_df[y_axis], mode='markers', name='Sensor Data'))
    sensor_fig.update_layout(title=f"{x_axis} vs {y_axis}", xaxis_title=x_axis, yaxis_title=y_axis)

    # Generate histogram plot
    histogram_fig = px.histogram(filtered_df, x=x_axis, nbins=num_bins, title=f"Histogram of {x_axis}")

    # Generate summary statistics
    summary_stats = filtered_df[[x_axis, y_axis, 'ZIQ', 'ball_spin', 'racket_speed']].describe()
    summary_table = dash_table.DataTable(
        data=summary_stats.reset_index().to_dict('records'),
        columns=[{"name": i, "id": i} for i in summary_stats.reset_index().columns],
        style_table={'overflowX': 'scroll'}
    )

    return sensor_fig, histogram_fig, summary_table

if __name__ == '__main__':
    app.run_server(debug=True)

