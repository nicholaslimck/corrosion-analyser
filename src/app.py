import sys
from os import environ
from uuid import uuid4

import dash
import dash_bootstrap_components as dbc
from dash import html, DiskcacheManager, CeleryManager
from flask_caching import Cache
from loguru import logger

from src.utils import IS_DOCKER

launch_uid = uuid4()

# Configure log level
logger.remove()
logger.add(sys.stdout, level=environ.get('LOG_LEVEL', 'INFO' if IS_DOCKER else 'DEBUG'))

# Setup background callback manager
if 'REDIS_URL' in environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__, broker=environ['REDIS_URL'], backend=environ['REDIS_URL'])
    background_callback_manager = CeleryManager(
        celery_app, cache_by=[lambda: launch_uid], expire=60
    )

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(
        cache, cache_by=[lambda: launch_uid], expire=60
    )

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
    background_callback_manager=background_callback_manager
)

# Setup Flask-Caching
if 'REDIS_URL' in environ:
    cache = Cache(app.server, config={
        # try 'filesystem' if you don't want to setup redis
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': environ.get('REDIS_URL', '')
    })
else:
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'cache-directory'
    })

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
