import time

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html, callback, dash_table
from dash.dependencies import Input, Output, State
from loguru import logger

from src.utils import models
from src.utils.graphing import single_defect

dash.register_page(__name__)


def layout():

    # Data input table configuration
    # Configure input table with default values as defined in Example A.1-1
    input_fields = [
        {'Parameter': 'Pipe Outer Diameter', 'Value': 812.8, 'Unit': 'mm'},
        {'Parameter': 'Pipe Wall Thickness', 'Value': 19.1, 'Unit': 'mm'},
        {'Parameter': 'SMTS', 'Value': 530.9, 'Unit': 'MPa'},
        {'Parameter': 'SMYS', 'Value': '', 'Unit': 'MPa'},
        {'Parameter': 'Defect Length', 'Value': 200, 'Unit': 'mm'},
        {'Parameter': 'Defect Width', 'Value': '', 'Unit': 'mm'},
        {'Parameter': 'Defect Depth', 'Value': 0.25, 'Unit': 't'},
        {'Parameter': 'Defect Elevation', 'Value': -100, 'Unit': 'm'},
        {'Parameter': 'Design Pressure', 'Value': 150, 'Unit': 'bar'},
        {'Parameter': 'Design Temperature', 'Value': 75, 'Unit': '°C'},
        {'Parameter': 'Incidental to Design Pressure Ratio', 'Value': 1.1, 'Unit': ''},
        {'Parameter': 'Accuracy', 'Value': 0.1, 'Unit': ''},
        {'Parameter': 'Confidence Level', 'Value': 0.8, 'Unit': ''},
        {'Parameter': 'Seawater Density', 'Value': 1025, 'Unit': 'kg/m³'},
        {'Parameter': 'Containment Density', 'Value': 200, 'Unit': 'kg/m³'},
        {'Parameter': 'Elevation Reference', 'Value': 30, 'Unit': 'm'},
        {'Parameter': 'Axial Stress', 'Value': '', 'Unit': 'MPa'},
        {'Parameter': 'Bending Stress', 'Value': '', 'Unit': 'MPa'},
        {'Parameter': 'Combined Stress', 'Value': '', 'Unit': 'MPa'}
    ]
    input_table = dash_table.DataTable(
        id='single_defect_input_table',
        columns=[
            {'name': 'Parameter', 'id': 'Parameter', 'editable': False},
            {'name': 'Value', 'id': 'Value', 'editable': True},
            {'name': 'Unit', 'id': 'Unit', 'editable': False}],
        data=input_fields,
        fill_width=False,
        tooltip_conditional=[
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMTS"'
                },
                'type': 'markdown',
                'value': 'Specified Minimum Tensile Strength'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMYS"'
                },
                'type': 'markdown',
                'value': 'Specified Minimum Yield Strength'
            },
            {
                'if': {
                    'filter_query': '{Parameter} contains "Stress"'
                },
                'type': 'markdown',
                'value': 'Populate Bending and/or Axial stress, or only Combined Stress. Leave blank if not applicable.'
                         ' Stress calculations also require a Defect Width value.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Defect Width"'
                },
                'type': 'markdown',
                'value': 'Must be populated if stress is provided. Leave blank if not applicable.'
            }
        ]
    )

    # Layout configuration
    center_align_style = {
            "text-align": "center",
            "display": "flex",
            "justify-content": "center",
            "align-items": "center"
        }

    input_layout = dbc.Row(
        [
            dbc.Row(dbc.Col(html.H2('Input Parameters'))),
            dbc.Row(
                [
                    dbc.Col(dbc.InputGroup([
                        dbc.InputGroupText("Safety Class:"),
                        dbc.Select(
                            id='single_defect_select_safety_class',
                            value='medium',
                            options=[
                                {'label': 'Low', 'value': 'low'},
                                {'label': 'Medium', 'value': 'medium'},
                                {'label': 'High', 'value': 'high'}
                            ], style=center_align_style
                        )
                    ], className="mb-3"), xs=12, md=6),
                ], style=center_align_style
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.InputGroup([
                        dbc.InputGroupText("Defect Measurement:"),
                        dbc.Select(
                            id='single_defect_select_measurement',
                            value='relative',
                            options=[
                                {'label': 'Relative', 'value': 'relative'},
                                {'label': 'Absolute', 'value': 'absolute'}
                            ], style=center_align_style
                        )
                    ], className="mb-3"), xs=12, md=6),
                ], style=center_align_style
            ),
            dbc.Row(dbc.Col(input_table, style=center_align_style)),
            dbc.Row(dbc.Col(
                [
                    dbc.Button(children='Calculate', id='single_defect_table_analyse', style={"margin-top": "10px"}),
                    html.Div(id='single_defect_table_analysis')
                ]
            ))
        ],
        style={"margin-top": "15px", **center_align_style}
    )

    graphs_layout = dbc.Row(
        children=[
            dbc.Row(dbc.Col(html.H3('Remaining Life Assessment', style={"text-align": "center"}))),
            dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(id='single_defect_table_graph')), xs=12, md=10), justify='center'),
            dbc.Row([
                dbc.Col(dcc.Loading(dcc.Graph(id='single_defect_pipe_cross_section_graph')), xs=12, sm=10, md=5),
                dbc.Col(dcc.Loading(dcc.Graph(id='single_defect_defect_cross_section_graph')), xs=12, sm=10, md=5)
            ], justify='center'),
            dbc.Row(dbc.Col(html.Div(id='single_defect_table_evaluation', style={"text-align": "center"})))
        ],
        style={"margin-top": "15px", **center_align_style}
    )

    combined_layout = dbc.Container(
        children=[
            html.Div(id='display'),
            dbc.Row(html.H1("Single Defect Analysis"), style={"text-align": "center"}),
            input_layout,
            graphs_layout
        ],
        fluid=True,
        style={"padding": "10px 10px"}
    )

    return combined_layout


def create_pipe(input_df: pd.DataFrame):
    diameter = input_df.query("Parameter == 'Pipe Outer Diameter'")['Value'].values[0]
    wall_thickness = input_df.query("Parameter == 'Pipe Wall Thickness'")['Value'].values[0]
    smts = input_df.query("Parameter == 'SMTS'")['Value'].values[0]
    design_pressure = input_df.query("Parameter == 'Design Pressure'")['Value'].values[0]
    design_temperature = input_df.query("Parameter == 'Design Temperature'")['Value'].values[0]
    incidental_to_design_pressure_ratio = input_df.query("Parameter == 'Incidental to Design Pressure Ratio'")['Value'].values[0]
    accuracy = input_df.query("Parameter == 'Accuracy'")['Value'].values[0]
    confidence_level = input_df.query("Parameter == 'Confidence Level'")['Value'].values[0]
    safety_class = input_df.query("Parameter == 'Safety Class'")['Value'].values[0]

    measurement_method = "relative" if input_df.query("Parameter == 'Defect Depth'")['Unit'].values[0] == "t" else "absolute"
    pipe_config = {
        'outside_diameter': diameter,
        'wall_thickness': wall_thickness,
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

    defect_length = input_df.query("Parameter == 'Defect Length'")['Value'].values[0]
    defect_width = input_df.query("Parameter == 'Defect Width'")['Value'].values[0]
    defect_depth = float(input_df.query("Parameter == 'Defect Depth'")['Value'].values[0])
    defect_elevation = input_df.query("Parameter == 'Defect Elevation'")['Value'].values[0]
    defect_config = {
        'length': defect_length,
        'width': defect_width,
        "relative_depth" if input_df.query("Parameter == 'Defect Depth'")['Unit'].values[0] == "t" else "depth": defect_depth,
        'elevation': defect_elevation
    }

    seawater_density = input_df.query("Parameter == 'Seawater Density'")['Value'].values[0]
    containment_density = input_df.query("Parameter == 'Containment Density'")['Value'].values[0]
    elevation_reference = input_df.query("Parameter == 'Elevation Reference'")['Value'].values[0]
    environment_config = {
        'seawater_density': seawater_density,
        'containment_density': containment_density,
        'elevation_reference': elevation_reference
    }

    axial_stress = input_df.query("Parameter == 'Axial Stress'")['Value'].values[0]
    bending_stress = input_df.query("Parameter == 'Bending Stress'")['Value'].values[0]
    combined_stress = input_df.query("Parameter == 'Combined Stress'")['Value'].values[0]
    if any([axial_stress, bending_stress, combined_stress]):
        loading_config = {
            'axial_load': axial_stress,
            'bending_load': bending_stress,
            'combined_stress': combined_stress
        }
    else:
        loading_config = None

    pipe = init_pipe(pipe_config, defect_config, environment_config, loading_config)

    return pipe


def init_pipe(pipe_config, defect_config, environment_config, loading_config=None):
    pipe = models.Pipe(config=pipe_config)
    defect = models.Defect(**defect_config)
    environment = models.Environment(**environment_config)

    pipe.add_defect(defect)
    if loading_config:
        pipe.add_loading(**loading_config)
    pipe.set_environment(environment)

    # Calculate p_corr
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    return pipe


# Add controls to build the interaction
@callback(
    Output(component_id='single_defect_table_graph', component_property='figure'),
    Output(component_id='single_defect_pipe_cross_section_graph', component_property='figure'),
    Output(component_id='single_defect_defect_cross_section_graph', component_property='figure'),
    Output(component_id='single_defect_table_analysis', component_property='children'),
    Output(component_id='single_defect_table_evaluation', component_property='children'),
    Input(component_id='single_defect_table_analyse', component_property='n_clicks'),
    State(component_id='single_defect_input_table', component_property='data'),
    State(component_id='single_defect_select_safety_class', component_property='value'),
    # State(component_id='single_defect_select_measurement', component_property='value'),
)
def update_graph(trigger_update, data, safety_class):
    start_time = time.time()

    data.append({'Parameter': 'Safety Class', 'Value': safety_class, 'Unit': ''})
    for item in data:
        try:
            item['Value'] = float(item['Value'])
        except ValueError:
            pass
    df = pd.DataFrame(
        data=data
    )

    pipe = create_pipe(df)

    fig1 = single_defect.generate_defect_depth_plot(pipe)
    fig2 = single_defect.generate_pipe_cross_section_plot(pipe)
    fig3 = single_defect.generate_defect_cross_section_plot(pipe)

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
    return fig1, fig2, fig3, analysis, evaluation


@callback(
    Output(component_id='single_defect_input_table', component_property='data'),
    Input(component_id='single_defect_select_measurement', component_property='value'),
    State(component_id='single_defect_input_table', component_property='data')
)
def update_measurement_method(measurement, data):
    if measurement == 'relative':
        data[6]['Unit'] = 't'
        data[11]['Unit'] = ''
    else:
        data[6]['Unit'] = 'mm'
        data[11]['Unit'] = 'mm'
    return data
