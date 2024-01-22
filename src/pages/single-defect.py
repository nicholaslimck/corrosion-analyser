import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from loguru import logger

from src.utils import models
from src.utils.graphing import single_defect

dash.register_page(__name__)


def layout():
    def generate_input(name, field_type):
        return dbc.Input(id=f'input_{name.lower().replace(" ", "_")}', type=field_type, debounce=1, placeholder=name)

    pipe_dimensions = dbc.Col([
        html.H4("Pipe Dimensions"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('Outer Diameter', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Wall Thickness', 'number'))])
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top'})

    material_properties = dbc.Col([
        html.H4("Material Properties"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('SMTS', 'number'))]),
            dbc.Row([dbc.Col(generate_input('SMYS', 'number'))])
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top'})

    defect_properties = dbc.Col([
        html.H4("Defect Properties"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('Defect Length', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Defect Depth', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Defect Elevation', 'number'))])
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top'})

    environment_properties = dbc.Col([
        html.H4("Environment Properties"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('Seawater Density', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Containment Density', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Elevation Reference', 'number'))])
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top'})

    design_parameters = dbc.Col([
        html.H4("Design Parameters"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('Design Pressure', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Design Temperature', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Incidental to Design Pressure Ratio', 'number'))]),
            dbc.Row([dbc.Col(dcc.Dropdown(id='safety_class', options=[
                'low', 'medium', 'high'], placeholder='Safety Class'))
                     ], style={'padding': '10px 0px'})
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top', 'width': 250})

    measurement_parameters = dbc.Col([
        html.H4("Measurement Parameters"),
        dbc.Form([
            dbc.Row([dbc.Col(generate_input('Accuracy', 'number'))]),
            dbc.Row([dbc.Col(generate_input('Confidence Level', 'number'))]),
            dbc.Row([dbc.Col(dcc.Dropdown(id='measurement_method', options=[
                'relative', 'absolute'], placeholder='Measurement Method'))
                     ], style={'padding': '10px 0px'})
        ])
    ], style={'display': 'inline-block', 'padding': '0px 10px', 'vertical-align': 'text-top'})

    combined_layout = html.Div(
        [
            html.H1("Single Defect Analysis"),
            html.Div(
                children=[
                    pipe_dimensions,
                    material_properties,
                    defect_properties,
                    environment_properties,
                    design_parameters,
                    measurement_parameters,
                    html.Button(children='Submit', id='single_defect_analyse'),
                    html.Div(id='single_defect_analysis',
                             style={'display': 'inline-block', "padding": "0px 10px", "vertical-align": "middle"})
                ]
            ),
            html.H3('Remaining Life Assessment'),
            dcc.Graph(id='single_defect_graph', figure={}),
            html.Div(id='single_defect_evaluation')
        ],
        style={"padding": "10px 10px"}
    )

    return combined_layout


def example_a_1():
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
        'measurement_method': 'relative'
    }

    defect_config = {
        'length': 200,
        'elevation': -100,
        'relative_depth': 0.25
    }

    environment_config = {
        'seawater_density': 1025,
        'containment_density': 200,
        'elevation_reference': 30
    }

    pipe = init_pipe(pipe_config, defect_config, environment_config)

    return pipe


def init_pipe(pipe_config, defect_config, environment_config):
    pipe = models.Pipe(config=pipe_config)
    defect = models.Defect(**defect_config)
    environment = models.Environment(**environment_config)

    pipe.add_defect(defect)
    pipe.set_environment(environment)

    # Calculate length correction factor
    defect.generate_length_correction_factor(
        d_nominal=pipe.dimensions.outside_diameter,
        t=pipe.dimensions.wall_thickness
    )

    # Calculate p_corr
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    return pipe


# Add controls to build the interaction
@callback(
    Output(component_id='single_defect_graph', component_property='figure'),
    Output(component_id='single_defect_analysis', component_property='children'),
    Output(component_id='single_defect_evaluation', component_property='children'),
    Input(component_id='single_defect_analyse', component_property='n_clicks'),
    Input(component_id='input_outer_diameter', component_property='value'),
    Input(component_id='input_wall_thickness', component_property='value'),
    Input(component_id='input_smts', component_property='value'),
    Input(component_id='input_design_pressure', component_property='value'),
    Input(component_id='input_design_temperature', component_property='value'),
    Input(component_id='input_incidental_to_design_pressure_ratio', component_property='value'),
    Input(component_id='input_accuracy', component_property='value'),
    Input(component_id='input_confidence_level', component_property='value'),
    Input(component_id='safety_class', component_property='value'),
    Input(component_id='measurement_method', component_property='value'),
    Input(component_id='input_defect_length', component_property='value'),
    Input(component_id='input_defect_depth', component_property='value'),
    Input(component_id='input_defect_elevation', component_property='value'),
    Input(component_id='input_seawater_density', component_property='value'),
    Input(component_id='input_containment_density', component_property='value'),
    Input(component_id='input_elevation_reference', component_property='value')
)
def update_graph(trigger_update,
                 pipe_outer_diameter,
                 pipe_wall_thickness,
                 smts,
                 design_pressure,
                 design_temperature,
                 incidental_to_design_pressure_ratio,
                 accuracy,
                 confidence_level,
                 safety_class,
                 measurement_method,
                 defect_length,
                 defect_depth,
                 defect_elevation,
                 seawater_density,
                 containment_density,
                 elevation_reference):
    start_time = time.time()
    if not trigger_update:
        pipe = example_a_1()
    else:
        pipe_config = {
            'outside_diameter': pipe_outer_diameter,
            'wall_thickness': pipe_wall_thickness,
            'alpha_u': 0.96,
            'smts': smts,
            'design_pressure': design_pressure,
            'design_temperature': design_temperature,
            'incidental_to_design_pressure_ratio': incidental_to_design_pressure_ratio,
            'accuracy': accuracy,
            'confidence_level': confidence_level,
            'safety_class': safety_class,
            'measurement_method': measurement_method
        }

        defect_config = {
            'length': defect_length,
            'relative_depth': defect_depth,
            'elevation': defect_elevation
        }

        environment_config = {
            'seawater_density': seawater_density,
            'containment_density': containment_density,
            'elevation_reference': elevation_reference
        }

        pipe = init_pipe(pipe_config, defect_config, environment_config)

    fig = single_defect.generate_plot(pipe)
    analysis = [
        f"""Effective Pressure:         {pipe.properties.effective_pressure:.2f}
        Pressure Resistance:        {pipe.properties.pressure_resistance:.2f}
        """
    ]
    evaluation = f"Effective Pressure {pipe.properties.effective_pressure:.2f} MPa " \
                 f"{'<' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else '>'} " \
                 f"Pressure Resistance {pipe.properties.pressure_resistance:.2f} MPa. " \
                 f"Corrosion is {'acceptable' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else 'unacceptable'}."
    analysis = [html.Div(contents, style={
        'whiteSpace': 'pre-line', 'display': 'inline-block', "padding": "0px 10px", "vertical-align": "text-top"})
                for contents in analysis]
    logger.debug(f"Single-Defect Scenario loaded | Render time: {time.time() - start_time:.2f}s")
    return fig, analysis, evaluation
