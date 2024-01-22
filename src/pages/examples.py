import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, dash_table
from dash.dependencies import Input, Output
from loguru import logger

from src.utils import models
from src.utils.graphing.single_defect import generate_defect_depth_plot, generate_cross_section_plot

dash.register_page(__name__)


def layout():
    return html.Div(
        [
            html.H1("Examples from DNV-RP-F101"),
            html.Div(
                children=[
                    html.Div(
                        children=['Select Example',
                                  dcc.RadioItems(
                                      options=['Example A-1', 'Example A-2', 'Example A-3'],
                                      value='Example A-1',
                                      id='example-selector')],
                        style={'display': 'inline-block'}),
                    html.Div(id='example_description',
                             style={'display': 'inline-block', "padding": "0px 10px", "vertical-align": "middle"})
                ]
            ),
            html.H3('Remaining Life Assessment'),
            dbc.Row([
                dbc.Col(dcc.Graph(id='example_defect_graph', figure={}, style={'display': 'inline-block', 'width': '75vw'})),
                dbc.Col(dcc.Graph(id='example_pipe_graph', figure={}, style={'display': 'inline-block', 'width': '15vw'}))
            ]),
            html.Div(id='example_evaluation'),
            dash_table.DataTable(id='pipe_properties_table')
        ],
        style={"padding": "10px 10px"}
    )


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
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=200,
        elevation=-100,
        relative_depth=0.25
    )

    environment = models.Environment(
        seawater_density=1025,
        containment_density=200,
        elevation_reference=30
    )

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


def example_a_2():
    # Pipe properties
    outer_diameter = 812.8
    wall_thickness = 19.1
    smts = 530.9
    design_pressure = 150
    design_temperature = 75
    incidental_to_design_pressure_ratio = 1.1
    f_u_temp = 15

    # Environment properties
    elevation_reference = 30
    seawater_density = 1025
    containment_density = 200

    # Defect dimensions
    # print('>> Enter defect dimensions:')
    defect_length = 200
    defect_depth = 0.25
    defect_elevation = -200

    # Measurement accuracy
    # print('>> Enter measurement factors:')
    measurement_tolerance = 1
    measurement_confidence_level = 0.8
    safety_class = 'medium'

    pipe_config = {
        'outside_diameter': outer_diameter,
        'wall_thickness': wall_thickness,
        'alpha_u': 0.96,
        'smts': smts,
        'design_pressure': design_pressure,
        'design_temperature': design_temperature,
        'incidental_to_design_pressure_ratio': incidental_to_design_pressure_ratio,
        'accuracy': measurement_tolerance,
        'confidence_level': measurement_confidence_level,
        'safety_class': safety_class,
        'measurement_method': 'absolute'
    }
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=defect_length,
        elevation=defect_elevation,
        relative_depth=defect_depth
    )

    environment = models.Environment(
        seawater_density=seawater_density,
        containment_density=containment_density,
        elevation_reference=elevation_reference
    )

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


def example_a_3():
    # Defect dimensions
    defect_length = 200.0
    defect_width = 100.0
    defect_depth = 0.62
    defect_elevation = -200

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
        length=defect_length,
        width=defect_width,
        elevation=defect_elevation,
        relative_depth=defect_depth
    )

    environment = models.Environment(
        seawater_density=1025,
        containment_density=200,
        elevation_reference=30
    )

    pipe.add_defect(defect)
    pipe.add_loading('compressive', 200)
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
    Output(component_id='example_defect_graph', component_property='figure'),
    Output(component_id='example_pipe_graph', component_property='figure'),
    Output(component_id='example_description', component_property='children'),
    Output(component_id='example_evaluation', component_property='children'),
    Input(component_id='example-selector', component_property='value')
)
def update_graph(example_selected):
    start_time = time.time()
    if example_selected == 'Example A-1':
        pipe = example_a_1()
    elif example_selected == 'Example A-2':
        pipe = example_a_2()
    elif example_selected == 'Example A-3':
        pipe = example_a_3()
    else:
        raise ValueError('Unsupported selection')
    fig_defect_assessment = generate_defect_depth_plot(pipe)
    fig_pipe = generate_cross_section_plot(pipe)
    description = [
        f"""Pipe Dimensions:
            Outside Diameter:      {pipe.dimensions.outside_diameter} mm
            Wall Thickness:         {pipe.dimensions.wall_thickness} mm
        """,
        f"""Material Properties:
            SMTS:                   {pipe.material_properties.smts}
            SMYS:                   {pipe.material_properties.smys}
        """,
        f"""Defect Properties:
            Length:                 {pipe.defect.length} mm
            Depth:                  {pipe.defect.depth:.2f} mm
            Relative Depth:         {pipe.defect.relative_depth:.2f}t
        """,
        f"""Environment Properties:
            Seawater Density:       {pipe.environment.seawater_density}
            Containment Density:    {pipe.environment.containment_density}
            Elevation Reference:    {pipe.environment.elevation_reference}
            Elevation:              {pipe.environment.elevation}
            External Pressure:      {pipe.environment.external_pressure:.2f}
            Incidental Pressure:    {pipe.environment.incidental_pressure:.2f}
        """
    ]
    if hasattr(pipe, 'loading'):
        description.append(
            f"""Loading:         {pipe.loading.loading_type}
            Loading Stress:        {pipe.loading.loading_stress:.2f}
            """)
    description.append(
        f"""Effective Pressure:         {pipe.properties.effective_pressure:.2f}
        Pressure Resistance:        {pipe.properties.pressure_resistance:.2f}
        """)
    evaluation = f"Effective Pressure {pipe.properties.effective_pressure:.2f} MPa " \
                 f"{'<' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else '>'} " \
                 f"Pressure Resistance {pipe.properties.pressure_resistance:.2f} MPa. " \
                 f"Corrosion is {'acceptable' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else 'unacceptable'}."
    description = [html.Div(contents, style={
        'whiteSpace': 'pre-line', 'display': 'inline-block', "padding": "0px 10px", "vertical-align": "text-top"})
                   for contents in description]
    logger.debug(f"Loaded {example_selected} | Render time: {time.time() - start_time:.2f}s")
    return fig_defect_assessment, fig_pipe, description, evaluation
