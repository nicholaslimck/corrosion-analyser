import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.utils.layout import center_align_style

dash.register_page(__name__, path='/')

layout = dbc.Container(
    [
        dbc.Row(dbc.Col(
            dcc.Markdown(
                """
                # Pipeline Corrosion Analyser
                ## Based on DNV-RP-F101
                This application is designed to assist in the assessment of corrosion defects in steel pipelines.
                
                Steel pipeline networks are used extensively in the oil and gas industry to transport materials over long distances. 
                Such pipelines are subjected to regular corrosion damage during operation and such damage must be assessed during regular inspections.
                
                ![corrosion_modes](https://ars.els-cdn.com/content/image/1-s2.0-S1875510019302239-fx1_lrg.jpg#threeQuarterWidth "Different forms of internal corrosion in hydrocarbon pipelines")
                
                *Different forms of internal corrosion in hydrocarbon pipelines. (Askari et al. 2019)*
                
                The DNV-RP-F101 recommended practice provides guidelines for the assessment of such corrosion defects in carbon steel pipelines. 
                This application is an implementation of the recommended practice to simplify the assessment process.
                
                Example data is provided to demonstrate the assessment under <dccLink href="/examples" children="Examples" />.
                
                To begin analysing defects, go to <dccLink href="/defect-analysis" children="Defect analysis" />. 
                """,
                dangerously_allow_html=True
            )
        ), style=center_align_style)
    ],
    fluid=True
)
