import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
# from app import server

from apps.homepage import HOMEPAGE
from apps.coming_soon import COMINGSOON
from apps.editing_qc import EDITING_QC
from apps.wteq_wteq import WTEQ_WTEQ
from apps.wteq_prec import WTEQ_PREC
from apps.peak_flow import PEAK_FLOW

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/editing_qc':
        return EDITING_QC()
    elif pathname == '/comingsoon':
        return COMINGSOON()
    elif pathname == '/wteq_wteq':
        return WTEQ_WTEQ()
    elif pathname == '/wteq_prec':
        return WTEQ_PREC()
    elif pathname == '/peak_flow':
        return PEAK_FLOW()
    else:
        return HOMEPAGE()


if __name__ == '__main__':
    app.run_server(debug=True)
