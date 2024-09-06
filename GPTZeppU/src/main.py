import warnings
import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import wrangle

# Suppress warnings
warnings.simplefilter("ignore", UserWarning)

# Input data path
file_path = "/home/blueaz/Downloads/SensorDownload/May2024/ztennis.db" 

# Wrangle the data
df = wrangle.wrangle(file_path)

# Convert client_created to datetime if it's not already
df['client_created'] = pd.to_datetime(df['client_created'], unit='ms')  # Adjust 'unit' accordingly

# Session and calc fields
calc = ['backswing_time', 'power', 'ball_spin', 'impact_position_x', 'impact_position_y', 'racket_speed', 'impact_region']

# App setup
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Tennis Sensor Data Dashboard"),

    # Date picker for selecting range
    dcc.DatePickerRange(
        id='date-picker',
        min_date_allowed=df['client_created'].min().date(),
        max_date_allowed=df['client_created'].max().date(),
        start_date=df['client_created'].min().date(),
        end_date=df['client_created'].max().date(),
    ),

    # Dropdown for y-axis selection
    html.Label("Y-axis metric"),
    dcc.Dropdown(
        id='y-axis-dropdown',
        options=[{'label': col, 'value': col} for col in calc],
        value='power',  # Default selection
        clearable=False
    ),

    # Checklist for swing type selection
    html.Label("Swing Type"),
    dcc.Checklist(
        id='swing-type-checklist',
        options=[{'label': s, 'value': s} for s in df['swing_type'].unique()],
        value=df['swing_type'].unique(),  # Default to all selected
        inline=True
    ),

    # Scatter plot
    dcc.Graph(id='scatter-plot'),

    # Histogram bin slider
    html.Label("Number of Bins for Histogram"),
    dcc.Slider(
        id='bin-slider',
        min=5,
        max=100,
        step=1,
        value=20,  # Default bin value
        marks={i: str(i) for i in range(5, 101, 10)}
    ),

    # Histogram plot
    dcc.Graph(id='histogram-plot'),

    # Summary stats table
    html.Div(id='summary-stats', style={'margin-top': '20px'})
])

# Callback for updating scatter plot, histogram, and stats
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('histogram-plot', 'figure'),
     Output('summary-stats', 'children')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('y-axis-dropdown', 'value'),
     Input('swing-type-checklist', 'value'),
     Input('bin-slider', 'value')]
)
def update_output(start_date, end_date, y_axis, selected_swing_types, num_bins):
    # Convert start_date and end_date to datetime format
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter by date range and swing types
    filtered_df = df[(df['client_created'] >= start_date) & (df['client_created'] <= end_date)]
    filtered_df = filtered_df[filtered_df['swing_type'].isin(selected_swing_types)]

    # Scatter plot
    scatter_fig = px.scatter(
        filtered_df,
        x="l_id",
        y=y_axis,
        color="swing_type",
        title=f"Scatter plot of l_id vs {y_axis}"
    )

    # Histogram plot with adjustable number of bins and color by swing_type
    histogram_fig = px.histogram(
        filtered_df,
        x=y_axis,
        nbins=num_bins,
        color="swing_type",  # Add this to color by swing_type
        title=f"Histogram of {y_axis} with {num_bins} bins"
    )
    

    # Summary stats
    summary_stats = filtered_df[y_axis].describe().to_frame().reset_index()
    summary_table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in summary_stats.columns])),
        html.Tbody([
            html.Tr([html.Td(summary_stats.iloc[i][col]) for col in summary_stats.columns])
            for i in range(len(summary_stats))
        ])
    ])

    return scatter_fig, histogram_fig, summary_table

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

