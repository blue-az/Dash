import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import WatchWrangle  # Assuming this module processes Apple Watch data

# Load and process Apple Watch data
Apple_path = "/home/blueaz/Downloads/SensorDownload/Compare/WristMotion.csv"
start_date = '2024-06-11'
end_date = '2024-06-15'
dfa = WatchWrangle.WatchWrangle(Apple_path, start_date, end_date)

# Ensure the timestamp column is in datetime format
dfa['timestamp'] = pd.to_datetime(dfa['timestamp'], format='%m-%d-%Y %I:%M:%S.%f %p')

# Define available signals based on the provided columns
available_signals = [
    'rotationRateX', 'rotationRateY', 'rotationRateZ',
    'gravityX', 'gravityY', 'gravityZ',
    'accelerationX', 'accelerationY', 'accelerationZ',
    'quaternionW', 'quaternionX', 'quaternionY', 'quaternionZ',
    'timestamp'
]

# Function to normalize data using min-max scaling
def normalize_data(series):
    return (series - series.min()) / (series.max() - series.min())

# Initialize Dash app
app = dash.Dash(__name__)

# Layout for the Dash app
app.layout = html.Div([
    html.H1("Apple Watch Sensor Dashboard"),
    dcc.DatePickerRange(
        id='date-picker',
        start_date='2024-06-12',  # Adjust as needed
        end_date='2024-06-14',    # Adjust as needed
        display_format='YYYY-MM-DD'
    ),
    html.Div([
        html.Label("Select X-axis Signal"),
        dcc.Dropdown(
            id='x-axis-signal',
            options=[{'label': 'Timestamp', 'value': 'timestamp'}],
            value='timestamp'  # Default x-axis is timestamp
        ),
    ]),
    html.Div([
        html.Label("Select Y-axis Signal"),
        dcc.Dropdown(
            id='y-axis-signal',
            options=[{'label': signal, 'value': signal} for signal in available_signals],
            value='accelerationX'  # Default Y-axis signal
        ),
    ]),
    html.Div([
        html.Label("Add Additional Signals"),
        dcc.Dropdown(
            id='additional-signals',
            options=[{'label': signal, 'value': signal} for signal in available_signals],
            multi=True
        ),
    ]),
    dcc.Graph(id='sensor-graph'),
])

# Update the graph when the user selects signals
@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('x-axis-signal', 'value'),
     Input('y-axis-signal', 'value'),
     Input('additional-signals', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_graph(x_signal, y_signal, additional_signals, start_date, end_date):
    # Filter data based on date range and ensure timestamp filtering works
    dfa_filtered = dfa[(dfa['timestamp'] >= pd.to_datetime(start_date)) & (dfa['timestamp'] <= pd.to_datetime(end_date))]

    # Initialize the figure
    fig = go.Figure()

    # X-axis data (use timestamp)
    x_data = dfa_filtered['timestamp']

    # Normalize and plot the selected y-axis signal
    if y_signal in dfa_filtered.columns:
        y_data = normalize_data(dfa_filtered[y_signal])
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            name=y_signal
        ))

    # Normalize and add additional signals
    if additional_signals:
        for signal in additional_signals:
            if signal in dfa_filtered.columns:
                normalized_signal = normalize_data(dfa_filtered[signal])
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=normalized_signal,
                    mode='lines+markers',
                    name=signal
                ))

    # Update layout of the figure
    fig.update_layout(
        title='Apple Watch Sensor Data Plot (Normalized)',
        xaxis_title='Timestamp',
        yaxis_title=f'Normalized {y_signal}',
        template='plotly'
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

