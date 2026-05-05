import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

dash.register_page(__name__, path='/')

layout = dbc.Container([
    html.Div([
        html.P("DNV-RP-F101", className="hero-eyebrow"),
        html.H1("Pipeline Corrosion\nAnalyser", className="hero-title"),
        html.P(
            "Assess corroded pipeline integrity per DNV-RP-F101. "
            "Calculate pressure resistance, maximum allowable defect depths, "
            "and remaining service life.",
            className="hero-subtitle"
        ),
        html.Div([
            dcc.Link(
                dbc.Button("Start Analysis →", color="primary", className="me-3"),
                href="/defect-analysis"
            ),
            dcc.Link(
                dbc.Button("View Examples", color="primary", outline=True),
                href="/examples"
            ),
        ]),
    ], className="hero-section"),

    dbc.Row([
        dbc.Col(html.Div([
            html.P("⊘", className="feature-icon"),
            html.P("Single Defect", className="feature-title"),
            html.P(
                "Assess individual corrosion defects against DNV-RP-F101 allowable limits.",
                className="feature-desc"
            ),
        ], className="feature-card"), xs=12, md=4, className="mb-3"),

        dbc.Col(html.Div([
            html.P("⊕", className="feature-icon"),
            html.P("Interacting Defects", className="feature-title"),
            html.P(
                "Evaluate nearby defects that combine into a single effective larger defect.",
                className="feature-desc"
            ),
        ], className="feature-card"), xs=12, md=4, className="mb-3"),

        dbc.Col(html.Div([
            html.P("◷", className="feature-icon"),
            html.P("Remaining Life", className="feature-title"),
            html.P(
                "Predict remaining service life from time-shifted corrosion measurements.",
                className="feature-desc"
            ),
        ], className="feature-card"), xs=12, md=4, className="mb-3"),
    ], className="px-4 pb-4"),
], fluid=True)
