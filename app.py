import dash
import dash_bootstrap_components as dbc

import plotly.express as px

import os


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.YETI], suppress_callback_exceptions=True)
server = app.server
server.secret_key = os.environ.get('secret_key', 'secret')
