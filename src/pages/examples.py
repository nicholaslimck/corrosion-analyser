import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from loguru import logger

from src.utils.layout import center_align_style
from src.utils import models
from src.utils.graphing.defect_plots import generate_defect_depth_plot
from src.utils.graphing.pipe_plots import (generate_pipe_cross_section_plot, generate_defect_cross_section_plot,
                                           generate_pipe_properties_table)

dash.register_page(__name__)


def layout():
    return html.Div(
        [
            html.H1("Examples from DNV-RP-F101"),
            dbc.Row(
                dbc.Col(
                    html.Div(
                        children=[
                            html.P(
                                "The following examples are taken from DNV-RP-F101, a recommended practice for "
                                "the assessment of the integrity of pipelines and risers. The examples are used to "
                                "demonstrate the application of the recommended practice to assess the remaining life "
                                "of pipelines with defects."
                            )
                        ]
                    )
                )
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            'Select Example',
                            dcc.RadioItems(
                                options=['Example A.1-1', 'Example A.1-2', 'Example A.1-3'],
                                value='Example A.1-1',
                                id='example-selector')],
                        style={'display': 'inline-block'}),
                    html.Div(id='example_description',
                             style={'display': 'inline-block', "padding": "0px 10px", "vertical-align": "middle"})
                ]
            ),
            html.H3('Remaining Life Assessment'),

            # dcc.Loading(

            dbc.Row(
                children=[
                    dbc.Row(dbc.Col(html.H3('Remaining Life Assessment', style={"text-align": "center"}))),
                    dbc.Row(dbc.Col(dcc.Loading(dcc.Graph(id='example_defect_graph')), xs=12, md=10),
                            justify='center'),
                    dbc.Row([
                        dbc.Col(dcc.Loading(dcc.Graph(id='example_pipe_cross_section_graph')), xs=12, sm=10,
                                md=5),
                        dbc.Col(dcc.Loading(dcc.Graph(id='example_defect_cross_section_graph')), xs=12, sm=10,
                                md=5)
                    ], justify='center'),
                    dbc.Row(dbc.Col(dcc.Markdown(id='example_evaluation', style={"text-align": "center"})))
                ],
                style={"margin-top": "15px", **center_align_style}
            )
        ],
        style={"padding": "10px 10px"}
    )


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
        'measurement_method': 'relative'
    }
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=200,
        relative_depth=0.25
    )

    environment = models.Environment(
        seawater_density=1025,
        containment_density=200,
        elevation_reference=30,
        elevation=-100
    )

    pipe.add_defect(defect)
    pipe.set_environment(environment)

    # Calculate p_corr
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
        'measurement_method': 'absolute'
    }
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=200,
        relative_depth=0.25
    )

    environment = models.Environment(
        seawater_density=1025,
        containment_density=200,
        elevation_reference=30,
        elevation=-200
    )

    pipe.add_defect(defect)
    pipe.set_environment(environment)

    # Calculate p_corr
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
        'measurement_method': 'relative'
    }
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=200.0,
        width=100.0,
        relative_depth=0.62
    )

    environment = models.Environment(
        seawater_density=1025,
        containment_density=200,
        elevation_reference=30,
        elevation=-100
    )

    pipe.add_defect(defect)
    pipe.add_loading(combined_stress=-200)
    pipe.set_environment(environment)

    # Calculate p_corr
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


# Add controls to build the interaction
@callback(
    Output(component_id='example_defect_graph', component_property='figure'),
    Output(component_id='example_pipe_cross_section_graph', component_property='figure'),
    Output(component_id='example_defect_cross_section_graph', component_property='figure'),
    Output(component_id='example_description', component_property='children'),
    Output(component_id='example_evaluation', component_property='children'),
    Input(component_id='example-selector', component_property='value')
)
def update_graph(example_selected):
    start_time = time.time()
    if example_selected == 'Example A.1-1':
        pipe = example_a_1_1()
    elif example_selected == 'Example A.1-2':
        pipe = example_a_1_2()
    elif example_selected == 'Example A.1-3':
        pipe = example_a_1_3()
    else:
        raise ValueError('Unsupported selection')
    fig_defect_assessment = generate_defect_depth_plot(pipe)
    fig_pipe_cross_section = generate_pipe_cross_section_plot(pipe)
    fig_defect_cross_section = generate_defect_cross_section_plot(pipe)

    description = [
        f"""Pipe Dimensions:
            Outside Diameter:      {pipe.dimensions.outside_diameter} mm
            Wall Thickness:         {pipe.dimensions.wall_thickness} mm
        """,
        f"""Material Properties:
            SMTS:                   {pipe.material_properties.smts} N/mm^2
            SMYS:                   {pipe.material_properties.smys} N/mm^2
        """,
        f"""Defect Properties:
            Length:                 {pipe.defect.length} mm
            Depth:                  {pipe.defect.depth:.2f} mm
            Relative Depth:         {pipe.defect.relative_depth:.2f}t
        """,
        f"""Environment Properties:
            Seawater Density:       {pipe.environment.seawater_density} kg/m^3
            Containment Density:    {pipe.environment.containment_density} kg/m^3
            Elevation Reference:    {pipe.environment.elevation_reference} m
            Elevation:              {pipe.environment.elevation} m
            External Pressure:      {pipe.environment.external_pressure:.2f} bar
            Incidental Pressure:    {pipe.environment.incidental_pressure:.2f} bar
        """
    ]
    if hasattr(pipe, 'loading'):
        stress_description = 'Loading: \n'
        loading = pipe.loading
        if hasattr(loading, 'axial_stress') and loading.axial_stress:
            stress_description += f"""Axial Stress:         {loading.axial_stress:.2f} N/mm^2\n"""
        if hasattr(loading, 'bending_stress') and loading.bending_stress:
            stress_description += f"""Bending Stress:         {loading.bending_stress:.2f} N/mm^2\n"""
        if hasattr(loading, 'loading_stress') and loading.loading_stress:
            stress_description += f"""Loading Stress:        {loading.loading_stress:.2f} N/mm^2\n"""
        description.append(stress_description)
    description.append(
        f"""Effective Pressure:         {pipe.properties.effective_pressure:.2f} N/mm^2
        Pressure Resistance:        {pipe.properties.pressure_resistance:.2f} N/mm^2
        """)
    evaluation = f"""
            Effective Pressure {pipe.properties.effective_pressure:.2f} MPa 
            {'<' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else '>'} 
            Pressure Resistance {pipe.properties.pressure_resistance:.2f} MPa.  
            Corrosion is **{'acceptable' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else 'unacceptable'}**.
            """
    description = [html.Div(contents, style={
        'whiteSpace': 'pre-line', 'display': 'inline-block', "padding": "0px 10px", "vertical-align": "text-top"})
                   for contents in description]
    logger.info(f"Loaded {example_selected} | Time elapsed: {time.time() - start_time:.2f}s")
    return fig_defect_assessment, fig_pipe_cross_section, fig_defect_cross_section, description, evaluation
