import sys
from os import environ

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
from loguru import logger

from src.utils import IS_DOCKER
from src.utils.units import PRESSURE_UNITS


DARK_THEME_URL = dbc.themes.DARKLY
LIGHT_THEME_URL = dbc.themes.FLATLY

logger.remove()
logger.add(sys.stdout, level=environ.get('LOG_LEVEL', 'INFO' if IS_DOCKER else 'DEBUG'))

# Callbacks run synchronously: the heaviest assessment (the allowable depth curves with a
# superimposed stress) takes about a second, so queueing it through Celery or diskcache
# bought nothing and pulled in a pickle based cache that has no patched version.
app = dash.Dash(
    __name__,
    use_pages=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"}],
)

_NAVBAR_COLOR_DARK = '#1e293b'
_NAVBAR_COLOR_LIGHT = '#f8fafc'

navbar = dbc.NavbarSimple(
    [
        *[
            dbc.NavItem(dbc.NavLink(page['name'], href=page['relative_path'], active="exact"))
            for page in dash.page_registry.values()
        ],
        dbc.NavItem(
            [
                # dbc.Select whitelists its props and rejects aria-label, so the
                # select is named by a bound, visually hidden label instead.
                html.Label('Pressure unit', htmlFor='pressure-unit',
                           className='visually-hidden'),
                dbc.Select(
                    id='pressure-unit',
                    options=[{'label': f'Pressure in {u}', 'value': u} for u in PRESSURE_UNITS],
                    value='bar',
                    size='sm',
                    className='navbar-unit-select',
                ),
            ],
            className='me-2 d-flex align-items-center',
        ),
        dbc.NavItem(
            # html.Button, not dbc.Button: dbc whitelists its props, so it cannot
            # carry aria-pressed (which the theme callback now outputs).
            html.Button(
                '🌙',
                id='theme-toggle',
                className='navbar-theme-toggle btn btn-link',
                n_clicks=0,
                title='Toggle light and dark theme',
                **{'aria-label': 'Toggle light and dark theme'},
            )
        ),
    ],
    id='main-navbar',
    brand='Corrosion Analyser',
    brand_href='/',
    fluid=True,
    color=_NAVBAR_COLOR_DARK,
)

app.layout = html.Div([
    html.Link(id='theme-stylesheet', rel='stylesheet', href=DARK_THEME_URL),
    dcc.Store(id='theme-store', storage_type='local', data='dark'),
    html.Div(id='theme-dummy', style={'display': 'none'}),
    navbar,
    dash.page_container,
])


@app.callback(
    Output('theme-stylesheet', 'href'),
    Output('theme-store', 'data'),
    Output('theme-toggle', 'children'),
    Output('main-navbar', 'color'),
    Output('theme-toggle', 'aria-pressed'),
    Input('theme-toggle', 'n_clicks'),
    Input('theme-store', 'modified_timestamp'),
    State('theme-store', 'data'),
)
def manage_theme(n_clicks, ts, current_theme):
    from dash import ctx
    if ctx.triggered_id == 'theme-toggle':
        new_theme = 'light' if current_theme == 'dark' else 'dark'
    else:
        new_theme = current_theme or 'dark'
    href = LIGHT_THEME_URL if new_theme == 'light' else DARK_THEME_URL
    icon = '☀️' if new_theme == 'dark' else '🌙'
    navbar_color = _NAVBAR_COLOR_DARK if new_theme == 'dark' else _NAVBAR_COLOR_LIGHT
    pressed = 'true' if new_theme == 'light' else 'false'
    return href, new_theme, icon, navbar_color, pressed


app.clientside_callback(
    """
    function(n_clicks) {
        // The browser dialog offers "Save as PDF" on every platform; the print
        // stylesheet turns the page into a document rather than a UI.
        if (n_clicks) { setTimeout(function() { window.print(); }, 100); }
        return '';
    }
    """,
    Output('print-trigger', 'children'),
    Input('print-button', 'n_clicks'),
    prevent_initial_call=True,
)

app.clientside_callback(
    """
    function(theme) {
        document.body.setAttribute('data-theme', theme || 'dark');
        return theme;
    }
    """,
    Output('theme-dummy', 'children'),
    Input('theme-store', 'data'),
)

if __name__ == '__main__':
    if IS_DOCKER:
        from waitress import serve
        logger.info('Starting server')
        serve(app.server, host="0.0.0.0", port=8050)
    else:
        logger.info('Starting development server')
        app.run(debug=True)
