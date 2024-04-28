import datetime
import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, dash_table, no_update
from dash.dependencies import Input, Output, State
from loguru import logger

from src.utils import models
from src.utils.graphing import defect_plots, pipe_plots
from src.utils.layout import center_align_style

dash.register_page(__name__)


def layout():
    # Data input table configuration
    # Configure input table with default values as defined in Example A.1-1
    input_fields = [
        {'Parameter': 'Pipe Outer Diameter', 'Value': 812.8, 'Unit': 'mm'},
        {'Parameter': 'Pipe Wall Thickness', 'Value': 19.1, 'Unit': 'mm'},
        {'Parameter': 'SMTS', 'Value': 530.9, 'Unit': 'MPa'},
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
        style_cell_conditional=[
            {
                'if': {'column_id': 'Parameter'},
                'textAlign': 'left'
            }
        ],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMTS"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMYS"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Defect Width"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Defect Depth"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Accuracy"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            },
            {
                'if': {
                    'filter_query': '{Parameter} contains "Stress"',
                    'column_id': 'Parameter'
                },
                'color': 'grey'
            }
        ],
        tooltip_conditional=[
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMTS"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Specified Minimum Tensile Strength'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "SMYS"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Specified Minimum Yield Stress'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Axial Stress"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Stress calculations require a Defect Width value.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Bending Stress"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Stress calculations require a Defect Width value.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Combined Stress"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Calculates based on Axial and Bending Stresses. Can also be entered manually. '
                         'Stress calculations require a Defect Width value. '
                         '\n\nNote: Will automatically convert to a compressive load.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Defect Width"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Required for stress calculations.\n\nLeave blank if not applicable.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Defect Depth"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Defect depth as a fraction of the pipe wall thickness or as an absolute value.'
            },
            {
                'if': {
                    'filter_query': '{Parameter} eq "Accuracy"',
                    'column_id': 'Parameter'
                },
                'type': 'markdown',
                'value': 'Accuracy as a percentage or absolute value.'
            },
        ]
    )

    secondary_defect_input_fields = [
        {'Parameter': 'Defect Length', 'Value': '', 'Unit': 'mm'},
        {'Parameter': 'Defect Width', 'Value': '', 'Unit': 'mm'},
        {'Parameter': 'Defect Depth', 'Value': '', 'Unit': 't'},
        {'Parameter': 'Defect Separation', 'Value': '', 'Unit': 'mm'}
    ]

    collapse = html.Div(
        [
            dbc.Button(
                "Secondary defect",
                id="secondary_defect_collapse_button",
                className="mb-3",
                color="primary",
                n_clicks=0,
                style={"margin-top": "10px"}
            ),
            dbc.Collapse(
                [
                    dbc.Row(
                        dash_table.DataTable(
                            id='single_defect_secondary_input_table',
                            columns=[
                                {'name': 'Parameter', 'id': 'Parameter', 'editable': False},
                                {'name': 'Value', 'id': 'Value', 'editable': True},
                                {'name': 'Unit', 'id': 'Unit', 'editable': False}],
                            data=secondary_defect_input_fields,
                            # fill_width=False,
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'Parameter'},
                                    'textAlign': 'left'
                                }
                            ],
                            style_data={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                            }
                        )
                    ),
                    dbc.Row(
                        dcc.DatePickerRange(
                            id='single_defect_date_range',
                            display_format='DD/MM/YYYY',
                            min_date_allowed=datetime.date(1990, 1, 1),
                            max_date_allowed=datetime.datetime.now().date(),
                            initial_visible_month=datetime.datetime.now().date(),
                            end_date=datetime.datetime.now().date(),
                            start_date_placeholder_text='First Date',
                            end_date_placeholder_text='Second Date'
                        )
                    )
                ],
                id="secondary_defect_collapse",
                is_open=False,
            ),
        ]
    )

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
            dbc.Row(dbc.Col(collapse, style=center_align_style)),
            dbc.Row(dbc.Col(
                [
                    dbc.Button(children='Analyse', id='single_defect_table_analyse',
                               style={"margin-top": "10px", "margin-bottom": "10px"}),
                    dcc.Markdown(id='single_defect_table_analysis')
                ]
            )),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Input Error")),
                    dbc.ModalBody(id='single_defect_input_error_modal_body'),
                ],
                id="single_defect_input_error_modal",
                is_open=False,
            ),
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
            dbc.Row(dbc.Col(dcc.Markdown(id='single_defect_table_evaluation', style={"text-align": "center"})))
        ],
        style={"margin-top": "15px", **center_align_style}
    )

    combined_layout = dbc.Container(
        children=[
            html.Div(id='display'),
            dbc.Row(html.H1("Defect Analysis"), style={"text-align": "center"}),
            input_layout,
            graphs_layout
        ],
        fluid=True
    )

    return combined_layout


def create_pipe(pipe_data: dict) -> models.Pipe:
    """
    Creates a Pipe object from the input data
    Args:
        pipe_data:

    Returns:
        pipe: Pipe object
    """
    diameter = pipe_data['Pipe Outer Diameter']['Value']
    wall_thickness = pipe_data['Pipe Wall Thickness']['Value']
    smts = pipe_data['SMTS']['Value']
    design_pressure = pipe_data['Design Pressure']['Value']
    design_temperature = pipe_data['Design Temperature']['Value']
    incidental_to_design_pressure_ratio = pipe_data['Incidental to Design Pressure Ratio']['Value']
    accuracy = pipe_data['Accuracy']['Value']
    confidence_level = pipe_data['Confidence Level']['Value']
    safety_class = pipe_data['Safety Class']['Value']

    measurement_method = "relative" if pipe_data['Defect Depth']['Unit'] == "t" else "absolute"
    pipe_config = {
        'outside_diameter': diameter,
        'wall_thickness': wall_thickness,
        'smts': smts,
        'design_pressure': design_pressure,
        'design_temperature': design_temperature,
        'incidental_to_design_pressure_ratio': incidental_to_design_pressure_ratio,
        'accuracy': accuracy,
        'confidence_level': confidence_level,
        'safety_class': safety_class,
        'measurement_method': measurement_method
    }

    # Configure defect(s)
    defect_config = {
        'length': pipe_data['Defect Length']['Value'],
        'width': pipe_data['Defect Width']['Value'],
        "relative_depth" if pipe_data['Defect Depth']['Unit'] == "t" else "depth": pipe_data['Defect Depth']['Value']
    }
    secondary_defect_config = {
        'length': pipe_data['Secondary Defect Length']['Value'],
        'width': pipe_data['Secondary Defect Width']['Value'],
        "relative_depth" if pipe_data['Secondary Defect Depth']['Unit'] == "t" else "depth": pipe_data['Secondary Defect Depth']['Value']
    }
    if pipe_data['First Date']['Value'] and pipe_data['Second Date']['Value']:
        first_timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(pipe_data['First Date']['Value'], '%Y-%m-%d'))
        second_timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(pipe_data['Second Date']['Value'], '%Y-%m-%d'))

        defect_config['measurement_timestamp'] = first_timestamp
        secondary_defect_config['measurement_timestamp'] = second_timestamp
    if pipe_data['Secondary Defect Separation']['Value']:
        secondary_defect_config['position'] = pipe_data['Secondary Defect Separation']['Value']

    # Configure environment
    seawater_density = pipe_data['Seawater Density']['Value']
    containment_density = pipe_data['Containment Density']['Value']
    elevation_reference = pipe_data['Elevation Reference']['Value']
    environment_config = {
        'seawater_density': seawater_density,
        'containment_density': containment_density,
        'elevation_reference': elevation_reference,
        'elevation': pipe_data['Defect Elevation']['Value']
    }

    combined_stress = pipe_data['Combined Stress']['Value']
    if combined_stress:
        if not defect_config['width']:
            raise ValueError('Defect Width is required for stress calculations.')
        loading_config = {
            'combined_stress': combined_stress
        }
    else:
        loading_config = None

    pipe = models.Pipe(config=pipe_config)
    defect = models.Defect(**defect_config)
    environment = models.Environment(**environment_config)

    pipe.add_defect(defect)
    if secondary_defect_config['length']:
        secondary_defect = models.Defect(**secondary_defect_config)
        pipe.add_defect(secondary_defect)

    if loading_config:
        pipe.add_loading(**loading_config)
    pipe.set_environment(environment)

    # Calculate p_corr
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()

    # Calculate maximum allowable defect depth
    pipe.calculate_maximum_allowable_defect_depth()

    # Calculate estimated remaining life
    if len(pipe.defects) > 1 and all(defect.measurement_timestamp for defect in pipe.defects):
        pipe.estimate_remaining_life()

    return pipe


# Add controls to build the interaction
@callback(
    Output(component_id='single_defect_table_graph', component_property='figure'),
    Output(component_id='single_defect_pipe_cross_section_graph', component_property='figure'),
    Output(component_id='single_defect_defect_cross_section_graph', component_property='figure'),
    Output(component_id='single_defect_table_analysis', component_property='children'),
    Output(component_id='single_defect_table_evaluation', component_property='children'),
    Output(component_id="single_defect_input_error_modal", component_property="is_open"),
    Output(component_id="single_defect_input_error_modal_body", component_property="children"),
    Input(component_id='single_defect_table_analyse', component_property='n_clicks'),
    State(component_id='single_defect_input_table', component_property='data'),
    State(component_id='single_defect_select_safety_class', component_property='value'),
    State(component_id='single_defect_secondary_input_table', component_property='data'),
    State(component_id='single_defect_date_range', component_property='start_date'),
    State(component_id='single_defect_date_range', component_property='end_date'),
)
def calculate_pipe_characteristics(
        trigger_update,
        data,
        safety_class,
        secondary_data,
        start_date,
        end_date
):
    def set_dtypes(table_data):
        for item in table_data:
            if item['Value'] == '':
                item['Value'] = None
            else:
                try:
                    item['Value'] = float(item['Value'])
                except (ValueError, TypeError):
                    pass
        return table_data

    start_time = time.time()

    data.append({'Parameter': 'Safety Class', 'Value': safety_class, 'Unit': ''})
    data = set_dtypes(data)

    data_dict = {item['Parameter']: {"Value": item['Value'], "Unit": item['Unit']} for item in data}

    secondary_data = set_dtypes(secondary_data)
    secondary_data_dict = {f"Secondary {item['Parameter']}": {"Value": item['Value'], "Unit": item['Unit']} for item in
                           secondary_data}
    secondary_data_dict['First Date'] = {"Value": start_date, "Unit": 'date'}
    secondary_data_dict['Second Date'] = {"Value": end_date, "Unit": 'date'}

    data_dict = data_dict | secondary_data_dict

    error_encountered = False
    error = ''

    try:
        # Create pipe
        pipe = create_pipe(data_dict)

        # Generate figures
        fig1 = defect_plots.generate_defect_depth_plot(pipe)
        fig2 = pipe_plots.generate_pipe_cross_section_plot(pipe)
        fig3 = pipe_plots.generate_defect_cross_section_plot(pipe)

        analysis = f"""Effective Pressure:\t{pipe.properties.effective_pressure:.2f} MPa  
        Pressure Resistance:\t{pipe.properties.pressure_resistance:.2f} MPa"""
        if len(pipe.defects) == 3:
            analysis += "  \nDefect interaction found"

        if pipe.properties.remaining_life is not None:
            analysis += f"  \nRemaining Life:\t{pipe.properties.remaining_life:.0f} days"

        evaluation = f"""
        Effective Pressure {pipe.properties.effective_pressure:.2f} MPa 
        {'<' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else '>'} 
        Pressure Resistance {pipe.properties.pressure_resistance:.2f} MPa.  
        Corrosion is **{'acceptable' if pipe.properties.effective_pressure < pipe.properties.pressure_resistance else 'unacceptable'}**.
        """
        logger.info(f"Single-Defect Scenario loaded | Processing time: {time.time() - start_time:.2f}s")
    except Exception as e:
        # Upon error, open the modal
        logger.error(f"Error while loading single-defect scenario: {e}")
        error_encountered = True
        error = str(e)
        fig1 = no_update
        fig2 = no_update
        fig3 = no_update
        analysis = no_update
        evaluation = no_update

    return fig1, fig2, fig3, analysis, evaluation, error_encountered, error


@callback(
    Output(component_id='single_defect_input_table', component_property='data'),
    Output(component_id='single_defect_secondary_input_table', component_property='data'),
    Input(component_id='single_defect_select_measurement', component_property='value'),
    State(component_id='single_defect_input_table', component_property='data'),
    State(component_id='single_defect_secondary_input_table', component_property='data'),
    prevent_initial_call=True
)
def update_measurement_method(measurement: str, main_data: dict, secondary_data: dict):
    """
    Updates the input table to reflect the selected measurement method
    Args:
        measurement: 'relative' or 'absolute'
        main_data: main input table data
        secondary_data: secondary input table data

    Returns:

    """
    if measurement == 'relative':
        main_data[5]['Unit'] = 't'
        main_data[10]['Unit'] = ''

        secondary_data[2]['Unit'] = 't'
    else:
        main_data[5]['Unit'] = 'mm'
        main_data[10]['Unit'] = 'mm'

        secondary_data[2]['Unit'] = 'mm'
    return main_data, secondary_data


@callback(
    Output(component_id='single_defect_input_table', component_property='data', allow_duplicate=True),
    Input(component_id='single_defect_input_table', component_property='data_timestamp'),
    State(component_id='single_defect_input_table', component_property='data'),
    prevent_initial_call=True
)
def sanitise_stress_values(timestamp: str, rows: dict):
    """
    Updates the input table to reflect the selected measurement method
    Args:
        timestamp: data update timestamp
        rows: input table data rows

    Returns:

    """
    axial_stress = 0
    bending_stress = 0

    for row in rows:
        if row['Parameter'] == 'Axial Stress' and row['Value']:
            axial_stress = abs(float(row['Value']))
        if row['Parameter'] == 'Bending Stress' and row['Value']:
            bending_stress = abs(float(row['Value']))
        if row['Parameter'] == 'Combined Stress':
            if any([axial_stress, bending_stress]):
                row['Value'] = -1 * abs(axial_stress + bending_stress)
            elif row['Value']:
                row['Value'] = -1 * abs(float(row['Value']))

    return rows


@callback(
    Output("secondary_defect_collapse", "is_open"),
    [Input("secondary_defect_collapse_button", "n_clicks")],
    [State("secondary_defect_collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
