import dash_html_components as html
import dash_bootstrap_components as dbc

from navbar import Navbar

nav = Navbar()

body = html.Div([
    dbc.Row([dbc.Col(html.H1('Coming Soon...'))])
])


def COMINGSOON():
    layout = html.Div([
        nav,
        body
    ])
    return layout
