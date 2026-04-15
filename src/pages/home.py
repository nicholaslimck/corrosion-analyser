import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from src.utils.layout import center_align_style

dash.register_page(__name__, path='/')

layout = dbc.Container(
    [
        dbc.Row(dbc.Col(
            html.Div([
                dcc.Markdown(
                    "# Pipeline Corrosion Analyser\n"
                    "## Based on DNV-RP-F101\n"
                    "This application is designed to assist in the assessment of "
                    "corrosion defects in steel pipelines.\n\n"
                    "Steel pipeline networks are used extensively in the oil and gas "
                    "industry to transport materials over long distances. "
                    "Such pipelines are subjected to regular corrosion damage during "
                    "operation and such damage must be assessed during "
                    "regular inspections.\n\n"
                    '![corrosion_modes](https://ars.els-cdn.com/content/image/'
                    '1-s2.0-S1875510019302239-fx1_lrg.jpg#threeQuarterWidth '
                    '"Different forms of internal corrosion in hydrocarbon'
                    ' pipelines")\n\n'
                    "*Different forms of internal corrosion in hydrocarbon "
                    "pipelines. (Askari et al. 2019)*\n\n"
                    "The DNV-RP-F101 recommended practice provides guidelines "
                    "for the assessment of such corrosion defects in carbon "
                    "steel pipelines. This application is an implementation of "
                    "the recommended practice to simplify the assessment "
                    "process."
                ),
                html.P([
                    "Example data is provided to demonstrate the assessment under ",
                    dcc.Link("Examples", href="/examples"),
                    "."
                ]),
                html.P([
                    "To begin analysing defects, go to ",
                    dcc.Link("Defect analysis", href="/defect-analysis"),
                    "."
                ]),
            ])
        ), style=center_align_style)
    ],
    fluid=True
)
