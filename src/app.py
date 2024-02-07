from os import environ
import sys

import dash
import dash_bootstrap_components as dbc
from dash import html
from loguru import logger

from src.utils import IS_DOCKER

# Configure log level
logger.remove()
logger.add(sys.stdout, level=environ.get('LOG_LEVEL', 'INFO' if IS_DOCKER else 'DEBUG'))

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.MATERIA],
    use_pages=True,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1",
        }
    ],
)

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
    if IS_DOCKER:
        # If run within a docker container, disable debug functions for performance and set IP Address to be
        # accessible from outside the container
        from waitress import serve

        logger.info('Starting server')
        serve(app.server, host="0.0.0.0", port=8050)
        # app.run_server(host='0.0.0.0', debug=False)
    else:
        # If run directly, enable debug functions
        logger.info('Starting development server')
        app.run_server(debug=True)
