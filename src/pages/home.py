import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.utils.layout import center_align_style

dash.register_page(__name__, path='/')

layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1('Pipeline Corrosion Analyser')), style=center_align_style),
        dbc.Row(dbc.Col(html.H4('Based on DNV-RP-F101')), style=center_align_style),
        dbc.Row(dbc.Col(
            html.Div('This application is designed to assist in the assessment of the remaining life of pipelines with defects.')
        ), style=center_align_style),
    ],
    fluid=True
)
