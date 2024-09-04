import warnings
import base64
import io
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.linear_model import Ridge
from category_encoders import OneHotEncoder
from sklearn.impute import SimpleImputer
import wrangle

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Wrangle function from wrangle module
file_path = "/home/blueaz/Downloads/SensorDownload/May2024/ztennis.db" 
df = wrangle.wrangle(file_path)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Interactive Dashboard")),
        dbc.Col(dcc.Upload(id="upload-data", children=html.Button('Upload File')))
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='target-column',
                options=[{'label': col, 'value': col} for col in df.columns],
                value='swing_side',
                clearable=False,
                style={'width': '100%'}
            ),
        ]),
        dbc.Col(dcc.Slider(id="n_clusters", min=2, max=12, step=1, value=3,
                           marks={i: str(i) for i in range(2, 13)},)),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-importance")),
        dbc.Col(dcc.Graph(id="kmeans-line")),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="pca-scatter")),
    ]),
    dbc.Row([
        dbc.Col(html.H1("Summary Statistics")),
        dbc.Col(dash_table.DataTable(id='summary-table', style_table={'width': '50vh'})),
    ])
])

# Callbacks
@app.callback(
    [Output('bar-importance', 'figure'),
     Output('kmeans-line', 'figure'),
     Output('pca-scatter', 'figure'),
     Output('summary-table', 'data')],
    [Input('upload-data', 'contents'),
     Input('target-column', 'value'),
     Input('n_clusters', 'value')]
)
def update_graph(contents, target_col, n_clusters):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    else:
        df = wrangle.wrangle(file_path)

    # Split data
    sensor_cols = df.select_dtypes(include='number').columns
    X_data = df[sensor_cols]
    y_data = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.2, random_state=42)

    model = make_pipeline(
        OneHotEncoder(use_cat_names=True),
        SimpleImputer(),
        Ridge()
    )

    # Fit model and calculate feature importance
    model.fit(X_train, y_train)
    coefficients = model.named_steps["ridge"].coef_
    features = model.named_steps["onehotencoder"].get_feature_names()
    feat_imp = pd.Series(coefficients, index=features)
    top5 = feat_imp.sort_values(key=abs).tail(5).index.to_list()

    # Plot feature importance
    bar_fig = px.bar(feat_imp.sort_values(key=abs).tail(15),
                     x=feat_imp.sort_values(key=abs).tail(15),
                     labels={'x': 'Importance', 'y': 'Feature'},
                     title="Top 15 Important Features")

    # KMeans clustering
    X = df[top5]
    inertia_errors = []
    silhouette_scores = []

    for k in range(2, n_clusters + 1):
        kmeans_model = make_pipeline(StandardScaler(), KMeans(n_clusters=k, random_state=42))
        kmeans_model.fit(X)
        inertia_errors.append(kmeans_model.named_steps["kmeans"].inertia_)
        silhouette_scores.append(
            silhouette_score(X, kmeans_model.named_steps["kmeans"].labels_)
        )

    # Plot Inertia and Silhouette Scores
    kmeans_fig = px.line(x=list(range(2, n_clusters + 1)),
                         y=inertia_errors, title="KMeans Inertia",
                         labels={'x': 'Clusters', 'y': 'Inertia'})

    # PCA Scatterplot
    pca_model = make_pipeline(StandardScaler(), KMeans(n_clusters=2, random_state=42))
    pca_model.fit(X)
    labels = pca_model.named_steps["kmeans"].labels_

    pca = PCA(n_components=2)
    X_pca = pd.DataFrame(pca.fit_transform(X), columns=["PC1", "PC2"])

    pca_fig = px.scatter(X_pca, x="PC1", y="PC2", color=labels.astype(str),
                         title="PCA Cluster Representation")

    # Summary Stats
    summary_stats = df.describe().to_dict(orient='records')

    return bar_fig, kmeans_fig, pca_fig, summary_stats


if __name__ == "__main__":
    app.run_server(debug=True)

