import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from loguru import logger

from src.utils import models
from src.utils.graphing.defect_plots import generate_defect_depth_plot
from src.utils.graphing.pipe_plots import (generate_pipe_cross_section_plot,
                                           generate_defect_cross_section_plot)

dash.register_page(__name__)


def layout():
    return dbc.Container([
        html.H1("Examples from DNV-RP-F101", className="mt-4 mb-2"),
        dbc.Row(dbc.Col(html.P(
            "The following examples are taken from DNV-RP-F101, a recommended practice for "
            "the assessment of the integrity of pipelines and risers."
        ))),
        html.Div(
            dcc.RadioItems(
                options=['Example A.1-1', 'Example A.1-2', 'Example A.1-3'],
                value='Example A.1-1',
                id='example-selector',
                inputClassName='form-check-input',
                labelClassName='form-check-label',
                inputStyle={'marginRight': '0.25rem'},
                inline=True,
            ),
            className='example-selector mb-3',
        ),
        html.Div(id='example_description'),
        dbc.Row([
            dbc.Row(
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='example_defect_graph')), className='graph-card'),
                    xs=12, md=10
                ),
                justify='center'
            ),
            dbc.Row([
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='example_pipe_cross_section_graph')), className='graph-card'),
                    xs=12, sm=10, md=5
                ),
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='example_defect_cross_section_graph')), className='graph-card'),
                    xs=12, sm=10, md=5
                ),
            ], justify='center'),
            dbc.Row(
                dbc.Col(html.Div(id='example_evaluation'), xs=12, md=10),
                justify='center'
            ),
        ], style={"margin-top": "15px"}),
    ], fluid=True)


def example_a_1_1():
    pipe_config = {
        'outside_diameter': 812.8,
        'wall_thickness': 19.1,
        'alpha_u': 0.96,
        'smts': 530.9,
        'design_pressure': 150,
        'design_temperature': 75,
        'incidental_to_design_pressure_ratio': 1.1,
        'accuracy': 0.1,
        'confidence_level': 0.8,
        'safety_class': 'medium',
        'measurement_method': 'relative',
    }
    pipe = models.Pipe(config=pipe_config)
    pipe.add_defect(models.Defect(length=200, relative_depth=0.25))
    pipe.set_environment(models.Environment(seawater_density=1025, containment_density=200,
                                            elevation_reference=30, elevation=-100))
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


def example_a_1_2():
    pipe_config = {
        'outside_diameter': 812.8,
        'wall_thickness': 19.1,
        'alpha_u': 0.96,
        'smts': 530.9,
        'design_pressure': 150,
        'design_temperature': 75,
        'incidental_to_design_pressure_ratio': 1.1,
        'accuracy': 1,
        'confidence_level': 0.8,
        'safety_class': 'medium',
        'measurement_method': 'absolute',
    }
    pipe = models.Pipe(config=pipe_config)
    pipe.add_defect(models.Defect(length=200, relative_depth=0.25))
    pipe.set_environment(models.Environment(seawater_density=1025, containment_density=200,
                                            elevation_reference=30, elevation=-200))
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


def example_a_1_3():
    pipe_config = {
        'outside_diameter': 219.0,
        'wall_thickness': 14.5,
        'alpha_u': 0.96,
        'smts': 455.1,
        'design_pressure': 150,
        'design_temperature': 100,
        'incidental_to_design_pressure_ratio': 1.0,
        'accuracy': 0.1,
        'confidence_level': 0.8,
        'safety_class': 'medium',
        'measurement_method': 'relative',
    }
    pipe = models.Pipe(config=pipe_config)
    pipe.add_defect(models.Defect(length=200.0, width=100.0, relative_depth=0.62))
    pipe.set_environment(models.Environment(seawater_density=1025, containment_density=200,
                                            elevation_reference=30, elevation=-100))
    pipe.add_loading(combined_stress=-200)
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


@callback(
    Output('example_defect_graph', 'figure'),
    Output('example_pipe_cross_section_graph', 'figure'),
    Output('example_defect_cross_section_graph', 'figure'),
    Output('example_description', 'children'),
    Output('example_evaluation', 'children'),
    Input('example-selector', 'value'),
    State('theme-store', 'data'),
)
def update_graph(example_selected, theme):
    start_time = time.time()
    theme = theme or 'dark'

    if example_selected == 'Example A.1-1':
        pipe = example_a_1_1()
    elif example_selected == 'Example A.1-2':
        pipe = example_a_1_2()
    elif example_selected == 'Example A.1-3':
        pipe = example_a_1_3()
    else:
        raise ValueError('Unsupported selection')

    fig_defect_assessment = generate_defect_depth_plot(pipe, theme=theme)
    fig_pipe_cross_section = generate_pipe_cross_section_plot(pipe, theme=theme)
    fig_defect_cross_section = generate_defect_cross_section_plot(pipe, theme=theme)

    cards = [
        dbc.Card([
            dbc.CardHeader("Pipe"),
            dbc.CardBody([
                html.P(f"Outside Diameter: {pipe.dimensions.outside_diameter} mm", className="mb-1"),
                html.P(f"Wall Thickness: {pipe.dimensions.wall_thickness} mm", className="mb-0"),
            ]),
        ]),
        dbc.Card([
            dbc.CardHeader("Material"),
            dbc.CardBody([
                html.P(f"SMTS: {pipe.material_properties.smts} N/mm²", className="mb-1"),
                html.P(f"SMYS: {pipe.material_properties.smys}", className="mb-0"),
            ]),
        ]),
        dbc.Card([
            dbc.CardHeader("Defect"),
            dbc.CardBody([
                html.P(f"Length: {pipe.defect.length} mm", className="mb-1"),
                html.P(f"Depth: {pipe.defect.depth:.2f} mm", className="mb-1"),
                html.P(f"Relative Depth: {pipe.defect.relative_depth:.2f}t", className="mb-0"),
            ]),
        ]),
        dbc.Card([
            dbc.CardHeader("Environment"),
            dbc.CardBody([
                html.P(f"Elevation: {pipe.environment.elevation} m", className="mb-1"),
                html.P(f"External Pressure: {pipe.environment.external_pressure:.2f} MPa", className="mb-1"),
                html.P(f"Incidental Pressure: {pipe.environment.incidental_pressure:.2f} MPa", className="mb-0"),
            ]),
        ]),
    ]
    if pipe.loading:
        loading_items = []
        if pipe.loading.loading_stress:
            loading_items.append(
                html.P(f"Combined Stress: {pipe.loading.loading_stress:.2f} N/mm²", className="mb-0"))
        cards.append(dbc.Card([dbc.CardHeader("Loading"), dbc.CardBody(loading_items)]))

    cards.append(dbc.Card([
        dbc.CardHeader("Results"),
        dbc.CardBody([
            html.P(f"Effective Pressure: {pipe.properties.effective_pressure:.2f} MPa", className="mb-1"),
            html.P(f"Pressure Resistance: {pipe.properties.pressure_resistance:.2f} MPa", className="mb-0"),
        ]),
    ]))

    description = dbc.Row(
        [dbc.Col(card, xs=12, sm=6, lg=2, className="mb-2") for card in cards],
        className="mb-3"
    )

    is_acceptable = pipe.properties.effective_pressure < pipe.properties.pressure_resistance
    comparison = '<' if is_acceptable else '>'
    status = 'acceptable' if is_acceptable else 'unacceptable'
    evaluation = dbc.Alert(
        [
            html.P(f"Effective Pressure {pipe.properties.effective_pressure:.2f} MPa "
                   f"{comparison} "
                   f"Pressure Resistance {pipe.properties.pressure_resistance:.2f} MPa.",
                   className="mb-2"),
            html.H5(f"Corrosion is {status}.", className="mb-0"),
        ],
        color="success" if is_acceptable else "danger",
        className="mt-3 text-center",
    )
    logger.info(f"Loaded {example_selected} | Time elapsed: {time.time() - start_time:.2f}s")
    return fig_defect_assessment, fig_pipe_cross_section, fig_defect_cross_section, description, evaluation
