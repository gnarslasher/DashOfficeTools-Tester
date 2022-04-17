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

nav = Navbar()

from site_lists import all_sites

def site_data(site1, site2):
    metric = 'WTEQ'

    http = 'https://www.nrcs.usda.gov/Internet/WCIS/sitedata/MONTHLY/$METRIC$/$TRIPLET$.json'

    http = http.replace('$METRIC$', metric)

    # site 1

    http = http.replace('$TRIPLET$', site1)

    response = requests.get(http)

    todo = json.loads(response.text)

    todo_list = todo['values']
    beginDate = todo["beginDate"]
    endDate = todo["endDate"]

    beginDate = dt.datetime.strptime(beginDate, '%Y-%m-%d %H:%M:%S')
    endDate = dt.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')

    dates = pd.date_range(beginDate, endDate, freq='MS')

    date_list = []
    for i in dates:
        date_list.append(i.to_pydatetime())

    data1 = {site1: {Key1: None for Key1 in date_list}}

    month_iterator = beginDate

    count = len(todo_list)
    for i in range(count):
        value = todo_list[i]
        data1[site1][month_iterator] = value
        month_iterator = month_iterator + relativedelta(months=+1)

    # site 2

    http = http.replace(site1, '$TRIPLET$')

    http = http.replace('$TRIPLET$', site2)

    response = requests.get(http)

    todo = json.loads(response.text)

    todo_list = todo['values']
    beginDate = todo["beginDate"]
    endDate = todo["endDate"]

    beginDate = dt.datetime.strptime(beginDate, '%Y-%m-%d %H:%M:%S')
    endDate = dt.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')

    dates = pd.date_range(beginDate, endDate, freq='MS')

    date_list = []
    for i in dates:
        date_list.append(i.to_pydatetime())

    data2 = {site2: {Key1: None for Key1 in date_list}}

    month_iterator = beginDate

    count = len(todo_list)
    for i in range(count):
        value = todo_list[i]
        data2[site2][month_iterator] = value
        month_iterator = month_iterator + relativedelta(months=+1)

    # create dataframes and join

    df1 = pd.DataFrame.from_dict(data1, dtype='float')
    df2 = pd.DataFrame.from_dict(data2, dtype='float')

    df = df1.join(df2)
    df = df.dropna()

    return df

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
        html.H1('Site Correlator (SWE Only)',
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
            html.H2('Site 1'),
            dcc.Dropdown(id='triplet1', options=all_sites, value='07E05_WY_SNOW'),
        ]),
        dbc.Col([
            html.H2('Site 2'),
            dcc.Dropdown(id='triplet2', options=all_sites, value='1132_WY_SNTL'),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            html.Br(),
            html.H6('Note: Type in site name or scroll through list. Site lists include all SNOTEL and Snow Courses in '
                    'MT, WY, SD, and ID. Refresh web browser if having issues selecting new sites.'),
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
        html.H6('Note: The trendline is calculated using Ordinary Least Squares (OLS) trendline function.'),
        html.Div(
            dcc.Graph(id='scatter-plot')),
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
        html.H3('Filtered Scatter Plot'),
        html.H6('Note: The trendline is calculated using Ordinary Least Squares (OLS) trendline function.'),
        html.Br(),
        html.H5('Select Months to Include'),
        html.Div(
            dcc.Checklist(
                id='list-months',
                options=[
                    {'label': 'January 1st |', 'value': 1},
                    {'label': 'February 1st |', 'value': 2},
                    {'label': 'March 1st |', 'value': 3},
                    {'label': 'April 1st |', 'value': 4},
                    {'label': 'May 1st |', 'value': 5},
                    {'label': 'June 1st |', 'value': 6},
                ],
                value=[1, 2, 3, 4, 5, 6],
            )
        ),
        html.Div(
            dcc.Graph(id='filtered-scatter-plot')),
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
        html.H3('Line Plot'),
        html.Div(
            dcc.Graph(id='line-plot')),
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
        html.Div(id='site_data_table'),
    ])),
], fluid=True)


def WTEQ_WTEQ():
    layout = html.Div([
        nav,
        body
    ])
    return layout


@app.callback(Output('scatter-plot', 'figure'),
              [Input('triplet1', 'value'),
               Input('triplet2', 'value')
               ])
def update_scatter(id1, id2):
    if id1 and id2 and id1 != id2:
        df = site_data(id1, id2)
        df.index = pd.to_datetime(df.index, format='%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y')
        df = df.reset_index()
        df.rename(columns={'index': 'DATE'}, inplace=True)
        fig = px.scatter(data_frame=df, x=id1, y=id2, trendline="ols", marginal_x="box", marginal_y="box")

        model = px.get_trendline_results(fig)
        results = model.iloc[0]["px_fit_results"]
        nobs = results.nobs
        alpha = results.params[0]
        beta = results.params[1]
        p_beta = results.pvalues[1]
        r_squared = results.rsquared

        line1 = 'y = ' + str(round(alpha, 4)) + ' + ' + str(round(beta, 4))+'x'
        line2 = 'p-value = ' + '{:.5f}'.format(p_beta)
        line3 = 'R^2 = ' + str(round(r_squared, 3))
        line4 = 'n = ' + str(int(nobs))
        summary = line1 + '<br>' + line2 + '<br>' + line3 + '<br>' + line4

        fig.add_annotation(
            xref="x",
            yref="paper",
            x=df[id1].max(),
            y='0',
            text=summary,
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=16,
                color="#ffffff"
            ),
            align="right",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            borderwidth=2,
            borderpad=4,
            bgcolor="rgba(100,100,100, 0.6)",
            opacity=0.8
        )
        return fig
    else:
        return None


@app.callback(Output('filtered-scatter-plot', 'figure'),
              [Input('triplet1', 'value'),
               Input('triplet2', 'value'),
               Input('list-months', 'value')
               ])
def update_scatter_filtered(id1, id2, months):
    if id1 and id2 and id1 != id2:
        df = site_data(id1, id2)
        df = df.reset_index()
        df.rename(columns={'index': 'DATE'}, inplace=True)
        df1 = df.loc[df['DATE'].dt.month.isin(months)]
        fig = px.scatter(data_frame=df1, x=id1, y=id2, trendline="ols", marginal_x="box", marginal_y="box")

        model = px.get_trendline_results(fig)
        results = model.iloc[0]["px_fit_results"]
        nobs = results.nobs
        alpha = results.params[0]
        beta = results.params[1]
        p_beta = results.pvalues[1]
        r_squared = results.rsquared

        line1 = 'y = ' + str(round(alpha, 4)) + ' + ' + str(round(beta, 4))+'x'
        line2 = 'p-value = ' + '{:.5f}'.format(p_beta)
        line3 = 'R^2 = ' + str(round(r_squared, 3))
        line4 = 'n = ' + str(int(nobs))
        summary = line1 + '<br>' + line2 + '<br>' + line3 + '<br>' + line4

        fig.add_annotation(
            xref="x",
            yref="paper",
            x=df[id1].max(),
            y='0',
            text=summary,
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=16,
                color="#ffffff"
            ),
            align="right",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            borderwidth=2,
            borderpad=4,
            bgcolor="rgba(100,100,100, 0.6)",
            opacity=0.8
        )
        return fig
    else:
        return None


@app.callback(Output('line-plot', 'figure'),
              [Input('triplet1', 'value'),
               Input('triplet2', 'value')
               ])
def update_lineplot(id1, id2):
    if id1 and id2 and id1 != id2:
        df = site_data(id1, id2)
        df.index = pd.to_datetime(df.index, format='%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y')
        df = df.reset_index()
        df.rename(columns={'index': 'DATE'}, inplace=True)
        fig = px.line(data_frame=df, x='DATE', y=[id1, id2], labels={'x': 'WTEQ (inches)'})
        return fig
    else:
        return None


@app.callback(Output('site_data_table', 'children'),
              [Input('triplet1', 'value'),
               Input('triplet2', 'value')
               ])
def daily_table(triplet1, triplet2):
    if triplet1 and triplet2 and triplet1 != triplet2:
        df = site_data(triplet1, triplet2)
        df.index = pd.to_datetime(df.index, format='%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y')
        df = df.reset_index()
        df.rename(columns={'index': 'DATE'}, inplace=True)
        df['Difference'] = (df[triplet1] - df[triplet2]).round(1)
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
