import warnings
import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import wrangle

# Suppress warnings
warnings.simplefilter("ignore", UserWarning)

# Input data path
file_path = "../data/synthetic_data.db"

# Wrangle the data
df = wrangle.wrangle(file_path)

# Session and calculation fields for axis selection (update with your relevant columns)
calc = ['StyleScore', 'StyleValue', 'EffectScore', 'EffectValue', 'SpeedScore', 'SpeedValue', 'time']

# Pre-process the time column to datetime format (for faster filtering)
df['time'] = pd.to_datetime(df['time'])

# App setup
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Tennis Sensor Data Dashboard"),

    # Date picker for selecting range
    dcc.DatePickerRange(
        id='date-picker',
        min_date_allowed=df['time'].min().date(),
        max_date_allowed=df['time'].max().date(),
        start_date=df['time'].min().date(),
        end_date=df['time'].max().date(),
    ),

    # Dropdown for x-axis selection
    html.Label("X-axis metric"),
    dcc.Dropdown(
        id='x-axis-dropdown',
        options=[{'label': col, 'value': col} for col in calc],
        value='StyleScore',  # Default selection
        clearable=False
    ),

    # Dropdown for y-axis selection
    html.Label("Y-axis metric"),
    dcc.Dropdown(
        id='y-axis-dropdown',
        options=[{'label': col, 'value': col} for col in calc],
        value='EffectScore',  # Default selection
        clearable=False
    ),

    # Checklist for type selection
    html.Label("Type"),
    dcc.Checklist(
        id='type-checklist',
        options=[{'label': t, 'value': t} for t in df['type'].unique()],
        value=df['type'].unique(),  # Default to all selected
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
     Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value'),
     Input('type-checklist', 'value'),
     Input('bin-slider', 'value')]
)
def update_output(start_date, end_date, x_axis, y_axis, selected_types, num_bins):
    # Convert start_date and end_date to datetime format
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter by date range and type (optimized filtering)
    filtered_df = df[
        (df['time'] >= start_date) &
        (df['time'] <= end_date) &
        (df['type'].isin(selected_types))
    ]

    # Scatter plot with dynamic x-axis and y-axis
    scatter_fig = px.scatter(
        filtered_df,
        x=x_axis,
        y=y_axis,
        color="type",
        title=f"Scatter plot of {x_axis} vs {y_axis}"
    )

    # Histogram plot with adjustable number of bins and color by type
    histogram_fig = px.histogram(
        filtered_df,
        x=x_axis,  # Use x-axis for histogram x-axis
        nbins=num_bins,
        color="type",  # Color by 'type'
        title=f"Histogram of {y_axis} with {num_bins} bins"
    )

    # Summary stats (updated with relevant columns)
    summary_stats = filtered_df[["time", "type", "spin", "StyleScore", "StyleValue", "EffectScore", "EffectValue", "SpeedScore", "SpeedValue", "stroke_counter"]].describe()

    # Dash DataTable for summary stats
    summary_table = dash_table.DataTable(
        data=summary_stats.reset_index().to_dict('records'),
        columns=[{"name": i, "id": i} for i in summary_stats.reset_index().columns],
        style_table={'overflowX': 'scroll'}
    )

    return scatter_fig, histogram_fig, summary_table

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

