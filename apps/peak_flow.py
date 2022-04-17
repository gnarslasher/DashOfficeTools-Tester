import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol

import plotly.express as px

import requests
import xml.dom.minidom as minidom
import datetime as dt
import pandas as pd

from app import app
from navbar import Navbar

import json
from dateutil.relativedelta import *

import numpy as np

nav = Navbar()

from site_lists import usgs_sites

def usgs_fetch(station_id): 
    for i in usgs_sites:
        if station_id in i['value']:
            key = i['label']
    start = key.find("(") + len("(")
    end = key.find(")")
    state_code = key[start:end]
    url = 'https://nwis.waterdata.usgs.gov/$STATE$/nwis/peak?site_no=$STATION_ID$&agency_cd=USGS&format=rdb'
    url = url.replace('$STATION_ID$', station_id)
    url = url.replace('$STATE$', state_code)   
    df = pd.read_csv(url, sep='\t', comment='#', header=[0,1])
    df = df.iloc[:, 2:7]
    df.columns = ['date', 'time', 'cfs', 'code', ' stage' ]
    df['date'] = pd.to_datetime(df['date'])
    df['1Jyear'] = df['date'].dt.year.apply(lambda x: dt.datetime(x, 1, 1))
    df['time_diff'] = df['date'] - df['1Jyear']
    df['julian_day'] = df['time_diff'].dt.days
    
    df_describe = df.describe()
    df_describe = df_describe.reset_index()
    df_describe = df_describe.rename(columns={'index': 'statistic'})
    adate = dt.datetime(1900, 1, 1)
    df_describe['start_date'] = adate
    df_describe['peak_day'] = df_describe['start_date'] + pd.to_timedelta(df_describe['julian_day'], unit='d')
    df_describe = df_describe.drop(columns=['code', 'start_date', 'julian_day', 'time_diff'])
    df = df.drop(columns=['1Jyear', 'time_diff', 'julian_day'])
    df_describe['peak_day'] = df_describe['peak_day'].dt.strftime('%m-%d')
    df_describe.iloc[0,3] = np.nan
    df_describe.iloc[2,3] = np.nan
    
    return df, df_describe

body = dbc.Container([
    dbc.Row(dbc.Col([
        html.Hr(
            style={
                "border": "none",
                "border-top": "3px double #333",
                "color": "#333",
                "overflow": "visible",
                "text-align": "center",
                "height": "5px",
            }),
        html.H1('Peak Flows',
                style={
                    "color": "black",
                    "text-align": "center",
                    "font-weight": "bold",
                }),
        html.Hr(
            style={
                "border": "none",
                "border-top": "3px double #333",
                "color": "#333",
                "overflow": "visible",
                "text-align": "center",
                "height": "5px",
            })],
    )),

    dbc.Row([
        dbc.Col([
            html.H2('Select Streamgage'),
            html.Br(),
            dcc.Dropdown(id='triplet', options=usgs_sites, value='06192500'),
            html.Br(),
            html.H6('Note: Type in site name or scroll through list. Site lists include all USGS streamgages in '
                    'MT. Refresh web browser if having issues selecting new sites.'),
        ]),
    ]),
    
    dbc.Row(dbc.Col(
        html.Hr(
            style={
                "border": "none",
                "border-top": "3px double #333",
                "color": "#333",
                "overflow": "visible",
                "text-align": "center",
                "height": "5px",
            }
        )
    )),

    dbc.Row(dbc.Col([
        html.H3('Scatter Plot'),
        html.Div(
            dcc.Graph(id='peak-scatter')),
    ])),

    dbc.Row(dbc.Col(
        html.Hr(
            style={
                "border": "none",
                "border-top": "3px double #333",
                "color": "#333",
                "overflow": "visible",
                "text-align": "center",
                "height": "5px",
            }
        )
    )),

    dbc.Row(dbc.Col([
        html.H3('Bar Plot'),
        html.Div(
            dcc.Graph(id='bar-plot2')),
    ])),

    dbc.Row(dbc.Col(
        html.Hr(
            style={
                "border": "none",
                "border-top": "3px double #333",
                "color": "#333",
                "overflow": "visible",
                "text-align": "center",
                "height": "5px",
            }
        )
    )),

    dbc.Row(dbc.Col([
        html.H3('Data Table'),
        html.Br(),
        html.Div(id='site_data_table2'),
        html.Br(),
        html.Br(),
    ])),
    
    dbc.Row(dbc.Col([
        html.H3('Data Table Stats'),
        html.Br(),
        html.Div(id='site_data_table3'),
        html.Br(),
        html.Br(),
    ])),
], fluid=True)


def PEAK_FLOW():
    layout = html.Div([
        nav,
        body
    ])
    return layout

@app.callback(Output('peak-scatter', 'figure'),
              [Input('triplet', 'value')])
def peak_scattter(station):
    if station:
        df, df_describe = usgs_fetch(station)
        fig = px.scatter(data_frame=df, x='date', y='cfs', marginal_y="box")
        return fig
    else:
        return None

@app.callback(Output('bar-plot2', 'figure'),
              [Input('triplet', 'value')])
def peak_bar(station):
    if station:
        df, df_describe = usgs_fetch(station)
        fig = px.bar(data_frame=df, x='date', y='cfs', text_auto=True)
        fig.update_xaxes(type='category')
        fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True,
            ),
            type="date"
            )   
        )
        return fig
    else:
        return None

@app.callback(Output('site_data_table2', 'children'),
              [Input('triplet', 'value')])
def peak_table(station):
    if station:
        df, df_describe = usgs_fetch(station)
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_cell={
                'textAlign': 'center',
                'height': 'auto',
                'minWidth': '100px', 'width': '100px', 'maxWidth': '100px',
                'whiteSpace': 'normal'
            },
            merge_duplicate_headers=True,
            fixed_rows={'headers': True},
            sort_action='native',
            style_data={'border': '2px solid black'},
            style_header={'border': '2px solid black'},
            style_table={'overflowX': 'auto'},
        )
    else:
        return None
    
@app.callback(Output('site_data_table3', 'children'),
              [Input('triplet', 'value')])
def peak_table_stats(station):
    if station:
        df, df_describe = usgs_fetch(station)
        return dash_table.DataTable(
            data=df_describe.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_describe.columns],
            style_cell={
                'textAlign': 'center',
                'height': 'auto',
                'minWidth': '100px', 'width': '100px', 'maxWidth': '100px',
                'whiteSpace': 'normal'
            },
            merge_duplicate_headers=True,
            fixed_rows={'headers': True},
            sort_action='native',
            style_data={'border': '2px solid black'},
            style_header={'border': '2px solid black'},
            style_table={'overflowX': 'auto'},
        )
    else:
        return None