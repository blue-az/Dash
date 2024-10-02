import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
import WatchWrangle
import UZeppWrangle
from scipy.signal import find_peaks

# Initialize Dash app
app = dash.Dash(__name__)

# Define available signals
zepp_sensor_signals = [
    'dbg_acc_1', 'dbg_acc_2', 'dbg_acc_3', 'dbg_gyro_1', 
    'dbg_gyro_2', 'dbg_var_1', 'dbg_var_2', 'dbg_var_3', 
    'dbg_var_4', 'dbg_sum_gx', 'dbg_sum_gy', 'dbg_sv_ax', 
    'dbg_sv_ay', 'dbg_max_ax', 'dbg_max_ay', 'dbg_min_az', 
    'dbg_max_az'
]
zepp_calc_signals = [
    'backswing_time', 'power', 'ball_spin', 'impact_position_x', 
    'impact_position_y', 'racket_speed', 'impact_region'
]
available_signals = [
    'rotationRateX', 'rotationRateY', 'rotationRateZ',
    'gravityX', 'gravityY', 'gravityZ',
    'accelerationX', 'accelerationY', 'accelerationZ',
    'quaternionW', 'quaternionX', 'quaternionY', 'quaternionZ',
    'timestamp'
]

# Combine sensor signals and calculation signals
all_signals = zepp_sensor_signals + zepp_calc_signals + available_signals

# Load and process data
Apple_path = "/home/blueaz/Downloads/SensorDownload/Compare/WristMotion.csv"
UZepp_path = "/home/blueaz/Downloads/SensorDownload/Compare/ztennis.db"
start_date = '2024-06-12'
end_date = '2024-06-14'

dfa = WatchWrangle.WatchWrangle(Apple_path, start_date, end_date) 
dfu = UZeppWrangle.UZeppWrangle(UZepp_path, start_date, end_date) 
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 300)

# General normalization function - written by GPT-4o
# Normalizes a column based on limits from another dataframe
def normalize_column(dfa, dfb, ref_col, norm_col, new_col_name):
    min_A = dfa[ref_col].min()
    max_A = dfa[ref_col].max()
    min_B = dfb[norm_col].min()
    max_B = dfb[norm_col].max()
    def normalize(x, min_B, max_B, min_A, max_A):
        return ((x - min_B) * (max_A - min_A) / (max_B - min_B)) + min_A
    dfb[new_col_name] = dfb[norm_col].apply(normalize,
                                            args=(min_B, max_B, min_A, max_A))

# Penalty function for center contact. Using Absolute value
absx = 0 - dfu['impact_position_x'].abs()
absy = 0 - dfu['impact_position_y'].abs()
dfu['abs_imp'] = 0 + (absx + absy)
#Normalize data based on inspection values chosen previously
# Remove outliers found during data visualization
dfu = dfu[dfu["dbg_acc_1"] < 10000]
dfu = dfu[dfu["dbg_acc_3"] < 10000]

# Zepp U sensor has raw sensor signals and calculated fields
# create session and calc dataframes
sensor = ['time', 'dbg_acc_1', 'dbg_acc_2', 'dbg_acc_3', 'dbg_gyro_1',
       'dbg_gyro_2', 'dbg_var_1', 'dbg_var_2', 'dbg_var_3', 'dbg_var_4',
       'dbg_sum_gx', 'dbg_sum_gy', 'dbg_sv_ax', 'dbg_sv_ay', 'dbg_max_ax',
       'dbg_max_ay', 'dbg_min_az', 'dbg_max_az', 'timestamp']
calc = [ 'backswing_time', 'power', 'ball_spin',
        'impact_position_x', 'impact_position_y',
       'racket_speed', 'impact_region']
df_sensor = dfu[sensor]
df_calc = dfu[calc]

# Estimated by inspection
tolerance = pd.Timedelta('5s')
shift = -1 

# Ensure the timestamps are in the same format
pd.options.mode.chained_assignment = None  # default='warn'
dfa['timestamp'] = pd.to_datetime(dfa['timestamp'], format='%m-%d-%Y %I:%M:%S.%f %p', errors='coerce')
df_sensor['timestamp'] = pd.to_datetime(df_sensor['timestamp'], format='%m-%d-%Y %I:%M:%S.%f %p', errors='coerce')
dfa['timestamp'] = dfa['timestamp'] - pd.Timedelta(seconds=shift) 

df_merged = pd.merge_asof(dfa, df_sensor,
                          left_on='timestamp',
                          right_on='timestamp',
                          tolerance=tolerance,
                          direction='nearest')


# Layout for the Dash app
app.layout = html.Div([
    html.H1("Zepp Sensor Signal Dashboard with Peak Detection"),
    dcc.DatePickerRange(
        id='date-picker',
        start_date=start_date,
        end_date=end_date,
        display_format='YYYY-MM-DD'
    ),
    html.Div([
        html.Label("Select X-axis Signal"),
        dcc.Dropdown(
            id='x-axis-signal',
            options=[{'label': 'Timestamp', 'value': 'timestamp'}],
            value='timestamp'
        ),
    ]),
    html.Div([
        html.Label("Select Y-axis Signal"),
        dcc.Dropdown(
            id='y-axis-signal',
            options=[{'label': signal, 'value': signal} for signal in all_signals],
            value='dbg_acc_1'
        ),
    ]),
    html.Div([
        html.Label("Add Additional Zepp Signals"),
        dcc.Dropdown(
            id='additional-signals',
            options=[{'label': signal, 'value': signal} for signal in all_signals],
            multi=True
        ),
    ]),
    html.Div([
        html.Label("Peak Detection Signal"),
        dcc.Dropdown(
            id='peak-detection-signal',
            options=[{'label': signal, 'value': signal} for signal in all_signals],
            value='accelerationX'
        ),
    ]),
    html.Div([
        html.Label("Min Distance"),
        dcc.Input(id='min-distance', type='number', value=25),
    ]),
    html.Div([
        html.Label("Threshold"),
        dcc.Input(id='threshold', type='number', value=0.8),
    ]),
    dcc.Graph(id='sensor-graph'),
])

@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('x-axis-signal', 'value'),
     Input('y-axis-signal', 'value'),
     Input('additional-signals', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('peak-detection-signal', 'value'),
     Input('min-distance', 'value'),
     Input('threshold', 'value')]
)
def update_graph(x_signal, y_signal, additional_signals, start_date, end_date, peak_signal, min_distance, threshold):
    # Filter data based on date range
    dfm_filtered = df_merged[(df_merged['timestamp'] >= start_date) & (df_merged['timestamp'] <= end_date)]

    # Initialize the figure
    fig = go.Figure()

    # X-axis data (use Zepp timestamp)
    x_data = dfm_filtered['timestamp']

    # Normalize the selected y-axis signal
    y_data = dfm_filtered.get(y_signal, None)
    if y_data is not None:
        y_data_normalized = (y_data - y_data.min()) / (y_data.max() - y_data.min())
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data_normalized,
            mode='lines+markers',
            name=f'Zepp {y_signal} (Normalized)'
        ))

    # Add additional Zepp signals
    if additional_signals:
        for signal in additional_signals:
            if signal in dfm_filtered.columns:
                additional_y_data = dfm_filtered[signal]
                additional_y_normalized = (additional_y_data - additional_y_data.min()) / (additional_y_data.max() - additional_y_data.min())
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=additional_y_normalized,
                    mode='lines+markers',
                    name=f'Zepp {signal} (Normalized)'
                ))

    # Peak detection
    if peak_signal in dfm_filtered.columns:
        signal = dfm_filtered[peak_signal]
        signal_normalized = (signal - signal.min()) / (signal.max() - signal.min())
        peaks, _ = find_peaks(signal_normalized, threshold=threshold, distance=min_distance)
        fig.add_trace(go.Scatter(
            x=x_data[peaks],
            y=signal_normalized[peaks],
            mode='markers',
            marker=dict(color='purple', size=10, symbol='star'),
            name=f'Peaks ({peak_signal})'
        ))

    # Update layout of the figure
    fig.update_layout(
        title=f'Zepp Sensor Data Plot (Normalized) with Peak Detection',
        xaxis_title='Timestamp',
        yaxis_title='Normalized Value',
        template='plotly'
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
