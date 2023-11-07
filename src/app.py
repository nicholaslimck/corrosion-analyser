import time

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from loguru import logger

from utils import models, is_docker

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA], use_pages=True)

app.layout = html.Div([
    # html.H1('Corrosion Analyser'),
    dbc.NavbarSimple([
        # dbc.NavItem(dbc.NavLink('examples', href='examples'))
        dbc.NavItem(dbc.NavLink(page['name'], href=page['relative_path'])) for page in dash.page_registry.values()
    ],
        brand='Corrosion Analyser',
        fluid=True),
    # html.Div([
    #     html.Div(
    #         dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
    #     ) for page in dash.page_registry.values()
    # ]),
    dash.page_container
])

if __name__ == '__main__':
    if is_docker():
        app.run_server(host='0.0.0.0', debug=False)
    else:
        app.run_server(debug=True)
