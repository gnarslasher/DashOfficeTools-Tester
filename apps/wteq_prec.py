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
import pandas as pd

from app import app
from navbar import Navbar

from datetime import datetime
from calendar import isleap

from site_lists import all_SNOTEL

nav = Navbar()

def fetch_wteq_prec(triplet, include_months, exclude_years):
    
    # =========================================================================
    # WTEQ
    # =========================================================================
        
    url = "https://www.nrcs.usda.gov/Internet/WCIS/sitedata/DAILY/WTEQ/$TRIPLET$.json"

    url = url.replace('$TRIPLET$', triplet)

    data_json = requests.get(url).json()

    start_date = data_json["beginDate"]
    end_date = data_json["endDate"]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d 00:00:00")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d 00:00:00")
    start_yr = start_dt.year
    end_yr = end_dt.year
    yr_rng = list(range(start_yr + 1, end_yr + 1, 1))

    days_to_oct1 = (datetime(start_yr, 10, 1) - start_dt).days

    if start_dt > datetime(start_yr, 10, 1):
        days_to_oct1 = 366 + days_to_oct1
        del yr_rng[0]
        start_yr = start_yr + 1

    data_with_feb29 = data_json["values"][days_to_oct1:]

    wy_with_feb29 = [data_with_feb29[i : i + 366] for i in range(0, len(data_with_feb29), 366)]

    data_dict = {yr: wy_with_feb29[i] for i, yr in enumerate(yr_rng)}

    for k in data_dict.keys():
        if not isleap(k) and len(data_dict[k]) >= 151:
            del data_dict[k][151]
                       
    serial_data = []
    for k, v in data_dict.items():
        serial_data.extend(v)
        
    date_rng = pd.date_range(datetime(start_yr, 10, 1), end_dt)

    df_wteq = pd.DataFrame(serial_data, index=date_rng, columns=['wteq'])

    df_wteq = df_wteq[(df_wteq.T != 0).any()]
    df_wteq = df_wteq.reset_index()
    df_wteq['month'] = pd.DatetimeIndex(df_wteq['index']).month
    df_wteq['w_year'] = pd.DatetimeIndex(df_wteq['index']).year
    df_wteq.loc[df_wteq['month'] >= 9, 'w_year'] = df_wteq['w_year'] + 1
    dt = df_wteq['index']
    day = pd.Timedelta('1d')
    in_block = ((dt - dt.shift(-1)).abs() == day) | (dt.diff() == day)
    filt = df_wteq.loc[in_block]
    breaks = filt['index'].diff() != day
    group = breaks.cumsum()
    df_wteq['group'] = group
    df_wteq['g_max'] = df_wteq.groupby('group')['wteq'].transform('max')
    df_wteq['wy_max'] = df_wteq.groupby('w_year')['wteq'].transform('max')
    df_wteq = df_wteq[df_wteq['g_max'] == df_wteq['wy_max']]
    df_wteq = df_wteq.drop(columns=['group', 'g_max'])
    df_wteq = df_wteq.set_index('index')

    # =============================================================================
    # PREC    
    # =============================================================================

    url = "https://www.nrcs.usda.gov/Internet/WCIS/sitedata/DAILY/PREC/$TRIPLET$.json"

    url = url.replace('$TRIPLET$', triplet)

    data_json = requests.get(url).json()

    start_date = data_json["beginDate"]
    end_date = data_json["endDate"]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d 00:00:00")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d 00:00:00")
    start_yr = start_dt.year
    end_yr = end_dt.year
    yr_rng = list(range(start_yr + 1, end_yr + 1, 1))

    days_to_oct1 = (datetime(start_yr, 10, 1) - start_dt).days

    if start_dt > datetime(start_yr, 10, 1):
        days_to_oct1 = 366 + days_to_oct1
        del yr_rng[0]
        start_yr = start_yr + 1
           
    data_with_feb29 = data_json["values"][days_to_oct1:]

    wy_with_feb29 = [data_with_feb29[i : i + 366] for i in range(0, len(data_with_feb29), 366)]

    data_dict = {yr: wy_with_feb29[i] for i, yr in enumerate(yr_rng)}

    for y in data_dict.keys():
        if not isleap(y) and len(data_dict[y]) >= 151:
            del data_dict[y][151]
            
    serial_data = []
    for k, v in data_dict.items():
        serial_data.extend(v)
        
    date_rng = pd.date_range(datetime(start_yr, 10, 1), end_dt)

    df_prec = pd.DataFrame(serial_data, index=date_rng, columns=['prec'])

    df_prec['prec_delta'] = df_prec['prec'].diff()
    df_prec[df_prec['prec_delta'] < 0] = 0

    # =========================================================================
    # Combine
    # =========================================================================

    df = df_wteq.merge(df_prec, left_index=True, right_index=True)

    df_trim = df[df.index.month.isin(include_months)]
    df_trim = df_trim[~df['w_year'].isin(exclude_years)]

    unique = df_trim['w_year'].unique()
    dict_trim = {year: None for year in unique}

    for i in unique:
        df_calcs = df_trim[df['w_year'] == i]
        onset = df_calcs.first_valid_index()
        max_wteq = df_calcs[['wteq']].max().values[0]
        max_date = df_calcs['wteq'].idxmax()
        wteq_at_start = df_calcs.iloc[0]['wteq']
        wteq_diff = max_wteq
        pcp_diff = df_calcs.loc[max_date]['prec'].sum()
        dict_trim[i] = [wteq_diff, pcp_diff, onset, max_date]
        
    df_final = pd.DataFrame.from_dict(dict_trim, orient='index', columns=(['wteq_delta', 'pcp_delta', 'onset', 'max_date']))
    
    return df_final

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
        html.H1('WTEQ vs PREC',
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
            html.H2('Snotel Site'),
            html.Br(),
            dcc.Dropdown(id='triplet', options=all_SNOTEL, value='916_MT_SNTL'),
            html.Br(),
            html.H6('Note: Type in site name or scroll through list. Site lists include all SNOTEL sites in '
                    'MT, WY, SD, and ID. Refresh web browser if having issues selecting new sites.'),
            html.Br(),
            html.H2('Include Months'),
            dcc.Checklist(
                id='include_months',
                options=[
                    {'label': 'October |', 'value': 10},
                    {'label': 'November |', 'value': 11},
                    {'label': 'December |', 'value': 12},
                    {'label': 'January |', 'value': 1},
                    {'label': 'February |', 'value': 2},
                    {'label': 'March |', 'value': 3},
                    {'label': 'April |', 'value': 4},
                    {'label': 'May |', 'value': 5},
                    {'label': 'June |', 'value': 6},
                    {'label': 'July |', 'value': 7},
                    {'label': 'August |', 'value': 8},
                    {'label': 'September', 'value': 9},
                ],
                value=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            ),
            html.Br(),
            html.H2('Exclude Years'),
            dcc.Input(id='exclude_year', type='text', value=''),
            html.Br(),
            html.Br(),
            html.H6('Note: Type in years to exclude. If multiple use a "," (ie. 2015, 2016) '),
            html.Br(),
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
            dcc.Graph(id='scatter-plot1')),
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
            dcc.Graph(id='bar-plot1')),
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
        html.Div(id='site_data_table1'),
        html.Br(),
        html.Br(),
    ])),
], fluid=True)


def WTEQ_PREC():
    layout = html.Div([
        nav,
        body
    ])
    return layout


@app.callback(Output('scatter-plot1', 'figure'),
              [Input('triplet', 'value'),
               Input('include_months', 'value'),
               Input('exclude_year', 'value')
               ])
def update_scatter(site, months, ex_year):
    if site and months:
        if len(ex_year) > 0:
            year_list = list(map( int, ex_year.split(',') ))
        else:
            year_list = []
        df = fetch_wteq_prec(site, months, year_list)
        fig = px.scatter(data_frame=df, x='wteq_delta', y='pcp_delta', trendline='ols', marginal_x="box", marginal_y="box", hover_data=[df.index])

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
            x=df['wteq_delta'].max(),
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


@app.callback(Output('bar-plot1', 'figure'),
              [Input('triplet', 'value'),
               Input('include_months', 'value'),
               Input('exclude_year', 'value')
               ])
def update_bar(site, months, ex_year):
    if site and months:
        if len(ex_year) > 0:
            year_list = list(map( int, ex_year.split(',') ))
        else:
            year_list = []
        df = fetch_wteq_prec(site, months, year_list)
        fig = px.bar(data_frame=df, x=df.index, y=['wteq_delta', 'pcp_delta'], barmode='group', text_auto=True)
        fig.update_xaxes(type='category')
        return fig
    else:
        return None

@app.callback(Output('site_data_table1', 'children'),
              [Input('triplet', 'value'),
                Input('include_months', 'value'),
                Input('exclude_year', 'value')
                ])
def daily_table(site, months, ex_year):
    if site and months:
        if len(ex_year) > 0:
            year_list = list(map( int, ex_year.split(',') ))
        else:
            year_list = []
        df = fetch_wteq_prec(site, months, year_list)
        df = df.reset_index()
        df['onset'] = pd.to_datetime(df['onset'], format='%Y-%m-%dT%H:%M:%S').dt.strftime('%m/%d/%Y')
        df['max_date'] = pd.to_datetime(df['max_date'], format='%Y-%m-%dT%H:%M:%S').dt.strftime('%m/%d/%Y')
        df.rename(columns={'index': 'water_year', 'onset': 'wteq_onset', 'max_date': 'wteq_max_date'}, inplace=True)
        df['wteq - prec'] = (df['wteq_delta'] - df['pcp_delta'])
        df = df.round(1)
        df['pcp/wteq'] = (df['pcp_delta'] / df['wteq_delta'])
        df['pcp/wteq'] = df['pcp/wteq'].round(2)
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
