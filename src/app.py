import dash
import dash_bootstrap_components as dbc
from dash import html

from src.utils import is_docker

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
    if is_docker():
        # If run within a docker container, disable debug functions for performance and set IP Address to be
        # accessible from outside the container
        app.run_server(host='0.0.0.0', debug=False)
    else:
        # If run directly, enable debug functions
        app.run_server(debug=True)
