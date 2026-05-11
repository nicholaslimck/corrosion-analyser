import sys
from os import environ
from uuid import uuid4

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, DiskcacheManager, CeleryManager, Input, Output, State
from flask_caching import Cache
from loguru import logger

from src.utils import IS_DOCKER

launch_uid = uuid4()

DARK_THEME_URL = dbc.themes.DARKLY
LIGHT_THEME_URL = dbc.themes.FLATLY

logger.remove()
logger.add(sys.stdout, level=environ.get('LOG_LEVEL', 'INFO' if IS_DOCKER else 'DEBUG'))

if 'REDIS_URL' in environ:
    from celery import Celery
    celery_app = Celery(__name__, broker=environ['REDIS_URL'], backend=environ['REDIS_URL'])
    background_callback_manager = CeleryManager(
        celery_app, cache_by=[lambda: launch_uid], expire=60
    )
else:
    import diskcache
    cache = diskcache.Cache("/tmp/corrosion-analyser-cache")
    background_callback_manager = DiskcacheManager(
        cache, cache_by=[lambda: launch_uid], expire=60
    )

app = dash.Dash(
    __name__,
    use_pages=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"}],
    background_callback_manager=background_callback_manager
)

if 'REDIS_URL' in environ:
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': environ.get('REDIS_URL', '')
    })
else:
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': '/tmp/corrosion-analyser-flask-cache'
    })

_NAVBAR_COLOR_DARK = '#1e293b'
_NAVBAR_COLOR_LIGHT = '#f8fafc'

navbar = dbc.NavbarSimple(
    [
        *[
            dbc.NavItem(dbc.NavLink(page['name'], href=page['relative_path'], active="exact"))
            for page in dash.page_registry.values()
        ],
        dbc.NavItem(
            dbc.Button('🌙', id='theme-toggle', color='link',
                       className='navbar-theme-toggle', n_clicks=0)
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
    return href, new_theme, icon, navbar_color


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
        app.run_server(debug=True)
