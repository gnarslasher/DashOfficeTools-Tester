import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol

import requests
import xml.dom.minidom as minidom
import datetime as dt
import pandas as pd

from app import app
from navbar import Navbar

nav = Navbar()


def daily_data(station_triplet, start_date, end_date):
    metrics = ['WTEQ', 'PREC', 'SNWD', 'TOBS', 'TMAX', 'TMIN', 'TAVG']

    today = dt.datetime.today()
    today_str = today.strftime('%m/%d/%Y')
    dt_start = dt.datetime.strptime(start_date, '%m/%d/%Y')
    dt_end = dt.datetime.strptime(end_date, '%m/%d/%Y')

    if dt_end > today:
        final_date = today_str
    else:
        final_date = end_date

    dates = pd.date_range(start_date, final_date, freq='d')
    date_list = []
    for i in dates:
        date_list.append(i.to_pydatetime())

    data = {Key1: {Key2: None for Key2 in metrics} for Key1 in date_list}

    headers = {'Content-type': 'text/soap'}

    wsURL = 'https://wcc.sc.egov.usda.gov/awdbWebService/services?WSDL'

    SOAP = '''<?xml version="1.0" encoding="UTF-8"?> <SOAP-ENV:Envelope 
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:q0="http://www.wcc.nrcs.usda.gov/ns/awdbWebService" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
        <SOAP-ENV:Body>
        <q0:getData>        
          <stationTriplets>$TRIPLET$</stationTriplets>
          <elementCd>$METRIC$</elementCd>
          <ordinal>1</ordinal>
          <duration>DAILY</duration>
          <getFlags>false</getFlags>
          <beginDate>$BEGINDATE$</beginDate>
          <endDate>$ENDDATE$</endDate>
          <alwaysReturnDailyFeb29>false</alwaysReturnDailyFeb29>
        </q0:getData>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    '''.strip()

    for x in metrics:
        day_iterator = dt_start
        SOAP = SOAP.replace('$METRIC$', x)
        SOAP = SOAP.replace('$TRIPLET$', station_triplet)
        SOAP = SOAP.replace('$BEGINDATE$', start_date)
        SOAP = SOAP.replace('$ENDDATE$', end_date)
        response = requests.post(wsURL, data=SOAP, headers=headers)
        xmldoc = minidom.parseString(response.text)
        return_tag = xmldoc.getElementsByTagName('return')
        for children in return_tag:
            count = len(children.getElementsByTagName('values'))
            for i in range(count):
                if children.getElementsByTagName('values')[i].firstChild:
                    value = children.getElementsByTagName('values')[i].firstChild.data
                    data[day_iterator][x] = value
                    day_iterator = day_iterator + dt.timedelta(days=1)
                else:
                    value = None
                    data[day_iterator][x] = value
                    day_iterator = day_iterator + dt.timedelta(days=1)
        SOAP = SOAP.replace(x, '$METRIC$')

    df = pd.DataFrame.from_dict(data, orient='index', dtype='float')

    df['DENSITY'] = (df['WTEQ'] / df['SNWD'] * 100).astype('int', errors='ignore')

    df['WTEQ_DELTA'] = (df['WTEQ'] - df['WTEQ'].shift(1)).round(1)
    df['PREC_DELTA'] = (df['PREC'] - df['PREC'].shift(1)).round(1)
    df['WTEQ_vs_PREC'] = (df['WTEQ_DELTA'] - df['PREC_DELTA']).round(1)
    df['SNWD_DELTA'] = (df['SNWD'] - df['SNWD'].shift(1)).round(1)

    df = df.round({'TOBS': 1, 'TMAX': 1, 'TMIN': 1, 'TAVG': 1})

    df['WTEQ'] = df['WTEQ'].map('{:,.1f}'.format)
    df['PREC'] = df['PREC'].map('{:,.1f}'.format)
    df['TOBS'] = df['TOBS'].map('{:,.1f}'.format)
    df['TMAX'] = df['TMAX'].map('{:,.1f}'.format)
    df['TMIN'] = df['TMIN'].map('{:,.1f}'.format)
    df['TAVG'] = df['TAVG'].map('{:,.1f}'.format)
    df['DENSITY'] = df['DENSITY'].map('{:,.1f}'.format)
    df['WTEQ_DELTA'] = df['WTEQ_DELTA'].map('{:,.1f}'.format)
    df['PREC_DELTA'] = df['PREC_DELTA'].map('{:,.1f}'.format)
    df['WTEQ_vs_PREC'] = df['WTEQ_vs_PREC'].map('{:,.1f}'.format)

    df.index = pd.to_datetime(df.index, format='%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y')
    df = df.reset_index()
    df.rename(columns={'index': 'DATE'}, inplace=True)

    return df


all_SNOTEL = [
    {'label': 'Badger Pass', 'value': '307:MT:SNTL'},
    {'label': 'Bald Mtn.', 'value': '309:WY:SNTL'},
    {'label': 'Banfield Mountain', 'value': '311:MT:SNTL'},
    {'label': 'Barker Lakes', 'value': '313:MT:SNTL'},
    {'label': 'Basin Creek', 'value': '315:MT:SNTL'},
    {'label': 'Beagle Springs', 'value': '318:MT:SNTL'},
    {'label': 'Bear Trap Meadow', 'value': '325:WY:SNTL'},
    {'label': 'Beartooth Lake', 'value': '326:WY:SNTL'},
    {'label': 'Beaver Creek', 'value': '328:MT:SNTL'},
    {'label': 'Bisson Creek', 'value': '346:MT:SNTL'},
    {'label': 'Black Bear', 'value': '347:MT:SNTL'},
    {'label': 'Black Pine', 'value': '349:MT:SNTL'},
    {'label': 'Blackwater', 'value': '350:WY:SNTL'},
    {'label': 'Blind Park', 'value': '354:SD:SNTL'},
    {'label': 'Bloody Dick', 'value': '355:MT:SNTL'},
    {'label': 'Bone Springs Div', 'value': '358:WY:SNTL'},
    {'label': 'Boulder Mountain', 'value': '360:MT:SNTL'},
    {'label': 'Box Canyon', 'value': '363:MT:SNTL'},
    {'label': 'Brackett Creek', 'value': '365:MT:SNTL'},
    {'label': 'Burgess Junction', 'value': '377:WY:SNTL'},
    {'label': 'Burroughs Creek', 'value': '379:WY:SNTL'},
    {'label': 'Calvert Creek', 'value': '381:MT:SNTL'},
    {'label': 'Canyon', 'value': '384:WY:SNTL'},
    {'label': 'Carrot Basin', 'value': '385:MT:SNTL'},
    {'label': 'Cloud Peak Reservoir', 'value': '402:WY:SNTL'},
    {'label': 'Clover Meadow', 'value': '403:MT:SNTL'},
    {'label': 'Cold Springs', 'value': '405:WY:SNTL'},
    {'label': 'Cole Creek', 'value': '407:MT:SNTL'},
    {'label': 'Combination', 'value': '410:MT:SNTL'},
    {'label': 'Copper Bottom', 'value': '413:MT:SNTL'},
    {'label': 'Copper Camp', 'value': '414:MT:SNTL'},
    {'label': 'Crystal Lake', 'value': '427:MT:SNTL'},
    {'label': 'Daly Creek', 'value': '433:MT:SNTL'},
    {'label': 'Darkhorse Lake', 'value': '436:MT:SNTL'},
    {'label': 'Deadman Creek', 'value': '437:MT:SNTL'},
    {'label': 'Divide', 'value': '448:MT:SNTL'},
    {'label': 'Dome Lake', 'value': '451:WY:SNTL'},
    {'label': 'Dupuyer Creek', 'value': '458:MT:SNTL'},
    {'label': 'Emery Creek', 'value': '469:MT:SNTL'},
    {'label': 'Evening Star', 'value': '472:WY:SNTL'},
    {'label': 'Fisher Creek', 'value': '480:MT:SNTL'},
    {'label': 'Flattop Mtn.', 'value': '482:MT:SNTL'},
    {'label': 'Frohner Meadow', 'value': '487:MT:SNTL'},
    {'label': 'Grave Creek', 'value': '500:MT:SNTL'},
    {'label': 'Grave Springs', 'value': '501:WY:SNTL'},
    {'label': 'Hand Creek', 'value': '510:MT:SNTL'},
    {'label': 'Hansen Sawmill', 'value': '512:WY:SNTL'},
    {'label': 'Hawkins Lake', 'value': '516:MT:SNTL'},
    {'label': 'Hobbs Park', 'value': '525:WY:SNTL'},
    {'label': 'Hoodoo Basin', 'value': '530:MT:SNTL'},
    {'label': 'Kirwin', 'value': '560:WY:SNTL'},
    {'label': 'Kraft Creek', 'value': '562:MT:SNTL'},
    {'label': 'Lakeview Ridge', 'value': '568:MT:SNTL'},
    {'label': 'Lemhi Ridge', 'value': '576:MT:SNTL'},
    {'label': 'Lick Creek', 'value': '578:MT:SNTL'},
    {'label': 'Little Warm', 'value': '585:WY:SNTL'},
    {'label': 'Lone Mountain', 'value': '590:MT:SNTL'},
    {'label': 'Lower Twin', 'value': '603:MT:SNTL'},
    {'label': 'Lubrecht Flume', 'value': '604:MT:SNTL'},
    {'label': 'Madison Plateau', 'value': '609:MT:SNTL'},
    {'label': 'Many Glacier', 'value': '613:MT:SNTL'},
    {'label': 'Marquette', 'value': '616:WY:SNTL'},
    {'label': 'Middle Powder', 'value': '625:WY:SNTL'},
    {'label': 'Monument Peak', 'value': '635:MT:SNTL'},
    {'label': 'Moss Peak', 'value': '646:MT:SNTL'},
    {'label': 'Mount Lockhart', 'value': '649:MT:SNTL'},
    {'label': 'Mule Creek', 'value': '656:MT:SNTL'},
    {'label': 'N Fk Elk Creek', 'value': '657:MT:SNTL'},
    {'label': 'Nez Perce Camp', 'value': '662:MT:SNTL'},
    {'label': 'Noisy Basin', 'value': '664:MT:SNTL'},
    {'label': 'North Fork Jocko', 'value': '667:MT:SNTL'},
    {'label': 'Northeast Entrance', 'value': '670:MT:SNTL'},
    {'label': 'Owl Creek', 'value': '676:WY:SNTL'},
    {'label': 'Parker Peak', 'value': '683:WY:SNTL'},
    {'label': 'Pickfoot Creek', 'value': '690:MT:SNTL'},
    {'label': 'Pike Creek', 'value': '693:MT:SNTL'},
    {'label': 'Placer Basin', 'value': '696:MT:SNTL'},
    {'label': 'Porcupine', 'value': '700:MT:SNTL'},
    {'label': 'Powder River Pass', 'value': '703:WY:SNTL'},
    {'label': 'Rocker Peak', 'value': '722:MT:SNTL'},
    {'label': 'S Fork Shields', 'value': '725:MT:SNTL'},
    {'label': 'Saddle Mtn.', 'value': '727:MT:SNTL'},
    {'label': 'Shell Creek', 'value': '751:WY:SNTL'},
    {'label': 'Short Creek', 'value': '753:MT:SNTL'},
    {'label': 'Shower Falls', 'value': '754:MT:SNTL'},
    {'label': 'Skalkaho Summit', 'value': '760:MT:SNTL'},
    {'label': 'South Pass', 'value': '775:WY:SNTL'},
    {'label': 'Spur Park', 'value': '781:MT:SNTL'},
    {'label': 'Sleeping Woman', 'value': '783:MT:SNTL'},
    {'label': 'St. Lawrence Alt', 'value': '786:WY:SNTL'},
    {'label': 'Stahl Peak', 'value': '787:MT:SNTL'},
    {'label': 'Sucker Creek', 'value': '798:WY:SNTL'},
    {'label': 'Sylvan Lake', 'value': '806:WY:SNTL'},
    {'label': 'Sylvan Road', 'value': '807:WY:SNTL'},
    {'label': 'Tepee Creek', 'value': '813:MT:SNTL'},
    {'label': 'Tie Creek', 'value': '818:WY:SNTL'},
    {'label': 'Timber Creek', 'value': '819:WY:SNTL'},
    {'label': 'Togwotee Pass', 'value': '822:WY:SNTL'},
    {'label': 'Townsend Creek', 'value': '826:WY:SNTL'},
    {'label': 'Twelvemile Creek', 'value': '835:MT:SNTL'},
    {'label': 'Twin Lakes', 'value': '836:MT:SNTL'},
    {'label': 'Waldron', 'value': '847:MT:SNTL'},
    {'label': 'Warm Springs', 'value': '850:MT:SNTL'},
    {'label': 'Whiskey Creek', 'value': '858:MT:SNTL'},
    {'label': 'White Mill', 'value': '862:MT:SNTL'},
    {'label': 'Wolverine', 'value': '875:WY:SNTL'},
    {'label': 'Wood Creek', 'value': '876:MT:SNTL'},
    {'label': 'Younts Peak', 'value': '878:WY:SNTL'},
    {'label': 'Tizer Basin', 'value': '893:MT:SNTL'},
    {'label': 'Stuart Mountain', 'value': '901:MT:SNTL'},
    {'label': 'Nevada Ridge', 'value': '903:MT:SNTL'},
    {'label': 'Albro Lake', 'value': '916:MT:SNTL'},
    {'label': 'Rocky Boy', 'value': '917:MT:SNTL'},
    {'label': 'Garver Creek', 'value': '918:MT:SNTL'},
    {'label': 'Daisy Peak', 'value': '919:MT:SNTL'},
    {'label': 'North Rapid Creek', 'value': '920:SD:SNTL'},
    {'label': 'Deer Park', 'value': '923:WY:SNTL'},
    {'label': 'West Yellowstone', 'value': '924:MT:SNTL'},
    {'label': 'Sacajawea', 'value': '929:MT:SNTL'},
    {'label': 'Peterson Meadows', 'value': '930:MT:SNTL'},
    {'label': 'Big Goose', 'value': '931:WY:SNTL'},
    {'label': 'Poorman Creek', 'value': '932:MT:SNTL'},
    {'label': 'Burnt Mtn', 'value': '981:MT:SNTL'},
    {'label': 'Cole Canyon', 'value': '982:WY:SNTL'},
    {'label': 'Onion Park', 'value': '1008:MT:SNTL'},
    {'label': 'Stringer Creek', 'value': '1009:MT:SNTL'},
    {'label': 'East Boulder Mine', 'value': '1105:MT:SNTL'},
    {'label': 'Elk Peak', 'value': '1106:MT:SNTL'},
    {'label': 'Castle Creek', 'value': '1130:WY:SNTL'},
    {'label': 'Little Goose', 'value': '1131:WY:SNTL'},
    {'label': 'Soldier Park', 'value': '1132:WY:SNTL'},
    {'label': 'Blacktail Mtn', 'value': '1144:MT:SNTL'},
    {'label': 'JL Meadow', 'value': '1287:MT:SNTL'},
]

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
        html.H1('Editing QC Tool',
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

    dbc.Row(dbc.Col([
        html.H3('MTDCO Data Editing Guidelines'),
        dash_table.DataTable(
            columns=[
                {"name": "Rule", "id": "Rule"},
                {"name": "Notes", "id": "Notes"},
                {"name": "Check", "id": "Check"},
                {"name": "Formatting Example", "id": "Formatting"}
            ],
            data=[
                {
                    "Rule": "Precipitation data should never decrease",
                    "Check": "PREC_DELTA column for negative numbers",
                    "Formatting": "-0.1",
                },
                {
                    "Rule": "Precipitation data should not increase in the winter if SWE is not increasing",
                    "Notes": "Unless hourly Tobs > 3 degrees C and the snowpack is < 24 inches deep",
                    "Check": "If WTEQ_DELTA > 0 then check if PREC_DELTA > WTEQ_DELTA",
                    "Formatting": "[0.1][0.3]",
                },
                {
                    "Rule": "Timing of precipitation & SWE should be the same in the winter",
                    "Check": "None Yet",
                    "Formatting": "None Yet",
                },
                {
                    "Rule": "Precipitation increments should be similar to SWE increments during winter months",
                    "Notes": "Check out WTEQ/PREC relationships Tool",
                    "Check": "None Yet",
                    "Formatting": "None Yet",
                },
                {
                    "Rule": "Snowpack density should be within the range of 5% to 70% ",
                    "Check": "Density column for values > 70% or < 5%",
                    "Formatting": "90.0",
                },
            ],
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': '{Formatting} = -0.1 or {Formatting} = 90.0',
                        'column_id': 'Formatting'
                    },
                    'backgroundColor': 'Red',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{Formatting} = [0.1][0.3]',
                        'column_id': 'Formatting'
                    },
                    'backgroundColor': 'DarkGoldenRod',
                    'color': 'white'
                },
            ],
            style_cell={
                'textAlign': 'center',
                'height': 'auto',
                'minWidth': '100px', 'width': '100px', 'maxWidth': '100px',
                'whiteSpace': 'normal'
            },
            fixed_rows={'headers': True},
            style_table={'overflowX': 'auto'},
        ),

        html.Br(),

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

    dbc.Row([
        dbc.Col([
            html.H2('Select SNOTEL Site'),
            dcc.Dropdown(id='triplet', options=all_SNOTEL, value='1286:MT:SNTL'),
        ]),
        dbc.Col([
            html.Div([
                html.Div([
                    html.H2('Select Date Range'),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date_placeholder_text="Start Period",
                        end_date_placeholder_text="End Period",
                        calendar_orientation='vertical',
                    ),
                ]),
            ]),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            html.H6('Note: Refresh web browser to select new site'),
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
        html.H3('Daily Data'),
        html.Div(id='daily_data_table'),
    ])),
], fluid=True)


def EDITING_QC():
    layout = html.Div([
        nav,
        body
    ])
    return layout


@app.callback(Output('daily_data_table', 'children'),
              [Input('triplet', 'value'),
               Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date')])
def daily_table(triplet, start, end):
    if start and end:
        start = dt.datetime.strptime(start, '%Y-%m-%d')
        start = start.strftime('%m/%d/%Y')
        end = dt.datetime.strptime(end, '%Y-%m-%d')
        end = end.strftime('%m/%d/%Y')
        df = daily_data(triplet, start, end)
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {"name": ["", "DATE"], "id": "DATE"},
                {"name": ["h2o Data", "WTEQ"], "id": "WTEQ", "hideable": [True, True]},
                {"name": ["h2o Data", "PREC"], "id": "PREC", "hideable": [True, True]},
                {"name": ["h2o Data", "SNWD"], "id": "SNWD", "hideable": [True, True]},
                {"name": ["Temperature Data", "TMAX"], "id": "TMAX", "hideable": [True, True]},
                {"name": ["Temperature Data", "TMIN"], "id": "TMIN", "hideable": [True, True]},
                {"name": ["Temperature Data", "TAVG"], "id": "TAVG", "hideable": [True, True]},
                {"name": ["Calculations", "DENSITY"], "id": "DENSITY", "hideable": [True, True]},
                {"name": ["Calculations", "WTEQ_DELTA"], "id": "WTEQ_DELTA", "hideable": [True, True]},
                {"name": ["Calculations", "PREC_DELTA"], "id": "PREC_DELTA", "hideable": [True, True]},
                {"name": ["Calculations", "WTEQ_vs_PREC"], "id": "WTEQ_vs_PREC", "hideable": [True, True]},
                {"name": ["Calculations", "SNWD_DELTA"], "id": "SNWD_DELTA", "hideable": [True, True]},
            ],
            style_header_conditional=[
                {'if': {'header_index': 0},
                 'backgroundColor': 'Grey',
                 'color': 'white'},
                {'if': {'column_id': 'DATE', 'header_index': 1},
                 'backgroundColor': 'Grey',
                 'color': 'white'},
                {'if': {'column_id': ['WTEQ', 'PREC', 'SNWD'], 'header_index': 1},
                 'backgroundColor': 'Blue',
                 'color': 'white'},
                {'if': {'column_id': ['TMAX', 'TMIN', 'TAVG'], 'header_index': 1},
                 'backgroundColor': 'OrangeRed',
                 'color': 'white'},
                {'if': {'column_id': ['DENSITY', 'WTEQ_DELTA', 'PREC_DELTA', 'WTEQ_vs_PREC', 'SNWD_DELTA'],
                        'header_index': 1},
                 'backgroundColor': 'Green',
                 'color': 'white'},
            ],
            style_data_conditional=[
                {'if': {'column_id': 'DATE'},
                 'backgroundColor': 'LightGrey',
                 'color': 'black'},
                {'if': {'column_id': ['WTEQ', 'PREC', 'SNWD']},
                 'backgroundColor': 'LightBlue',
                 'color': 'black'},
                {'if': {'column_id': ['TMAX', 'TMIN', 'TAVG']},
                 'backgroundColor': 'Orange',
                 'color': 'black'},
                {'if': {'column_id': ['DENSITY', 'WTEQ_DELTA', 'PREC_DELTA', 'WTEQ_vs_PREC', 'SNWD_DELTA']},
                 'backgroundColor': 'LightGreen',
                 'color': 'black'},
                {
                    'if': {
                        'filter_query': '70 < {DENSITY} > 5',
                        'column_id': 'DENSITY'
                    },
                    'backgroundColor': 'Red',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{PREC_DELTA} < 0',
                        'column_id': 'PREC_DELTA'
                    },
                    'backgroundColor': 'Red',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{PREC_DELTA} > {WTEQ_DELTA} and {WTEQ_DELTA} > 0',
                        'column_id': ['PREC_DELTA', 'WTEQ_DELTA']
                    },
                    'backgroundColor': 'DarkGoldenRod',
                    'color': 'white'
                },
            ],
            tooltip_conditional=[
                {
                    'if': {
                        'filter_query': '70 < {DENSITY} > 5',
                        'column_id': 'DENSITY'
                    },
                    'type': 'markdown',
                    'value': '70% > DENSITY < 5% [Verify this is real]'
                },
                {
                    'if': {
                        'filter_query': '{PREC_DELTA} < 0',
                        'column_id': 'PREC_DELTA'
                    },
                    'type': 'markdown',
                    'value': 'PREC_DELTA < 0'
                },
                {
                    'if': {
                        'filter_query': '{PREC_DELTA} > {WTEQ_DELTA} and {WTEQ_DELTA} > 0',
                        'column_id': 'WTEQ_DELTA'
                    },
                    'type': 'markdown',
                    'value': 'PREC_DELTA > WTEQ_DELTA. [Verify SD < 24 or TOBS > 3c]'
                },
            ],
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
            hidden_columns=['TMAX', 'TMIN', 'TAVG'],
        )
    else:
        return None
