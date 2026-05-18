import datetime
import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, no_update
from dash.dependencies import Input, Output, State
from loguru import logger

from src.utils import models
from src.utils.graphing import defect_plots, pipe_plots
from src.utils.layout import center_align_style, build_evaluation_alert

dash.register_page(__name__)


def _input_row(label: str, input_id: str, default, unit: str, unit_id: str = None) -> dbc.Row:
    unit_component = (dbc.InputGroupText(unit, id=unit_id)
                      if unit_id else dbc.InputGroupText(unit))
    return dbc.Row([
        dbc.Col(html.Label(label, className='col-form-label small'), width=7),
        dbc.Col(
            dbc.InputGroup([
                dbc.Input(
                    id=input_id,
                    type='number',
                    value=default,
                    debounce=True,
                    class_name='text-end',
                ),
                unit_component,
            ], size='sm'),
            width=5
        ),
    ], className='mb-1 align-items-center')


def layout():
    accordion = dbc.Accordion([
        dbc.AccordionItem([
            _input_row('Outer Diameter', 'input-outer-diameter', 812.8, 'mm'),
            _input_row('Wall Thickness', 'input-wall-thickness', 19.1, 'mm'),
        ], title='Pipe Geometry', item_id='pipe-geometry'),

        dbc.AccordionItem([
            _input_row('SMTS', 'input-smts', 530.9, 'MPa'),
        ], title='Material', item_id='material'),

        dbc.AccordionItem([
            _input_row('Length', 'input-defect-length', 200, 'mm'),
            _input_row('Width', 'input-defect-width', None, 'mm'),
            _input_row('Depth', 'input-defect-depth', 0.25, 't', unit_id='unit-defect-depth'),
        ], title='Defect', item_id='defect'),

        dbc.AccordionItem([
            _input_row('Elevation', 'input-defect-elevation', -100, 'm'),
            _input_row('Design Pressure', 'input-design-pressure', 150, 'bar'),
            _input_row('Design Temperature', 'input-design-temp', 75, '°C'),
            _input_row('Incidental/Design Ratio', 'input-incidental-ratio', 1.1, ''),
            _input_row('Seawater Density', 'input-seawater-density', 1025, 'kg/m³'),
            _input_row('Containment Density', 'input-containment-density', 200, 'kg/m³'),
        ], title='Environment', item_id='environment'),

        dbc.AccordionItem([
            _input_row('Accuracy', 'input-accuracy', 0.1, '', unit_id='unit-accuracy'),
            _input_row('Confidence Level', 'input-confidence-level', 0.8, ''),
        ], title='Assessment', item_id='assessment'),

        dbc.AccordionItem([
            _input_row('Elevation Reference', 'input-elevation-reference', 30, 'm'),
            _input_row('Axial Stress', 'input-axial-stress', None, 'MPa'),
            _input_row('Bending Stress', 'input-bending-stress', None, 'MPa'),
            _input_row('Combined Stress', 'input-combined-stress', None, 'MPa'),
            dbc.Tooltip(
                "Auto-calculated from Axial + Bending if both are set. "
                "Treated as a compressive load. Requires Defect Width.",
                target='input-combined-stress',
            ),
        ], title='Loading & Stress', item_id='loading'),
    ], active_item=['pipe-geometry', 'defect'], always_open=True)

    secondary_inputs = dbc.Collapse([
        _input_row('Length', 'input-sec-length', None, 'mm'),
        _input_row('Width', 'input-sec-width', None, 'mm'),
        _input_row('Depth', 'input-sec-depth', None, 't', unit_id='unit-sec-defect-depth'),
        _input_row('Separation', 'input-sec-separation', None, 'mm'),
        dbc.Row(
            dcc.DatePickerRange(
                id='single_defect_date_range',
                display_format='DD/MM/YYYY',
                min_date_allowed=datetime.date(1990, 1, 1),
                max_date_allowed=datetime.datetime.now().date(),
                initial_visible_month=datetime.datetime.now().date(),
                end_date=datetime.datetime.now().date(),
                start_date_placeholder_text='Start',
                end_date_placeholder_text='End',
            ), className='mt-2'
        ),
    ], id="secondary_defect_collapse", is_open=False)

    input_sidebar = dbc.Offcanvas(
        [
            dbc.Row([
                dbc.Col([
                    html.Small("Safety Class", className="text-muted"),
                    dbc.Select(
                        id='single_defect_select_safety_class',
                        value='medium',
                        options=[
                            {'label': 'Low', 'value': 'low'},
                            {'label': 'Medium', 'value': 'medium'},
                            {'label': 'High', 'value': 'high'},
                        ],
                        size="sm",
                    ),
                ]),
                dbc.Col([
                    html.Small("Measurement", className="text-muted"),
                    dbc.Select(
                        id='single_defect_select_measurement',
                        value='relative',
                        options=[
                            {'label': 'Relative', 'value': 'relative'},
                            {'label': 'Absolute', 'value': 'absolute'},
                        ],
                        size="sm",
                    ),
                ]),
            ], className="mb-3"),
            accordion,
            dbc.Button(
                "Secondary Defect",
                id="secondary_defect_collapse_button",
                className="w-100 mt-3 mb-2",
                color="secondary",
                outline=True,
                size="sm",
                n_clicks=0,
            ),
            secondary_inputs,
            dbc.Button(
                'Analyse',
                id='single_defect_table_analyse',
                className="w-100 mt-2 mb-3",
                color="primary",
            ),
            html.Div(id='single_defect_table_analysis'),
        ],
        id="input_sidebar",
        title="Input Parameters",
        placement="start",
        is_open=True,
        scrollable=True,
        backdrop=False,
        close_button=True,
        style={"width": "420px"},
    )

    error_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Input Error")),
            dbc.ModalBody(id='single_defect_input_error_modal_body'),
            dbc.ModalFooter(
                dbc.Button("Close", id="single_defect_error_close", className="ms-auto", n_clicks=0)
            ),
        ],
        id="single_defect_input_error_modal",
        is_open=False,
    )

    graphs_layout = dbc.Row(
        children=[
            dbc.Row(
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='single_defect_table_graph')), className='graph-card'),
                    xs=12, md=10
                ),
                justify='center'
            ),
            dbc.Row([
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='single_defect_pipe_cross_section_graph')), className='graph-card'),
                    xs=12, sm=10, md=5
                ),
                dbc.Col(
                    html.Div(dcc.Loading(dcc.Graph(id='single_defect_defect_cross_section_graph')), className='graph-card'),
                    xs=12, sm=10, md=5
                ),
            ], justify='center'),
            dbc.Row(
                dbc.Col(html.Div(id='single_defect_table_evaluation'), xs=12, md=8),
                justify='center'
            ),
        ],
        style={"margin-top": "15px", **center_align_style}
    )

    return dbc.Container(
        children=[
            input_sidebar,
            error_modal,
            html.Div([
                dbc.Button(
                    "Input Parameters",
                    id="input_sidebar_toggle",
                    color="primary",
                    outline=True,
                    n_clicks=0,
                    style={"position": "absolute", "left": "15px", "top": "0"},
                ),
                html.H1("Defect Analysis", className="text-center"),
                html.P("DNV-RP-F101 Assessment", className="text-center text-muted mb-0",
                       style={"fontSize": "0.85rem"}),
            ], style={"position": "relative"}, className="mb-3"),
            graphs_layout,
        ],
        fluid=True
    )


def create_pipe(pipe_data: dict) -> models.Pipe:
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
        'measurement_method': measurement_method,
    }

    defect_depth_unit = pipe_data['Defect Depth']['Unit']
    defect_config = {
        'length': pipe_data['Defect Length']['Value'],
        'width': pipe_data['Defect Width']['Value'],
        ("relative_depth" if defect_depth_unit == "t" else "depth"): pipe_data['Defect Depth']['Value'],
    }

    sec_depth_unit = pipe_data['Secondary Defect Depth']['Unit']
    secondary_defect_config = {
        'length': pipe_data['Secondary Defect Length']['Value'],
        'width': pipe_data['Secondary Defect Width']['Value'],
        ("relative_depth" if sec_depth_unit == "t" else "depth"): pipe_data['Secondary Defect Depth']['Value'],
    }

    if pipe_data['First Date']['Value'] and pipe_data['Second Date']['Value']:
        first_ts = datetime.datetime.timestamp(
            datetime.datetime.strptime(pipe_data['First Date']['Value'], '%Y-%m-%d'))
        second_ts = datetime.datetime.timestamp(
            datetime.datetime.strptime(pipe_data['Second Date']['Value'], '%Y-%m-%d'))
        defect_config['measurement_timestamp'] = first_ts
        secondary_defect_config['measurement_timestamp'] = second_ts

    secondary_defect_separation = pipe_data['Secondary Defect Separation']['Value']
    if secondary_defect_separation:
        secondary_defect_config['position'] = secondary_defect_separation

    environment_config = {
        'seawater_density': pipe_data['Seawater Density']['Value'],
        'containment_density': pipe_data['Containment Density']['Value'],
        'elevation_reference': pipe_data['Elevation Reference']['Value'],
        'elevation': pipe_data['Defect Elevation']['Value'],
    }

    combined_stress = pipe_data['Combined Stress']['Value']
    if combined_stress:
        if secondary_defect_separation:
            raise ValueError('Interacting defects are not supported with superimposed stress.')
        if not pipe_data['Defect Width']['Value']:
            raise ValueError('Defect Width is required for stress calculations.')
        loading_config = {'combined_stress': -abs(float(combined_stress))}
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

    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()

    if len(pipe.defects) > 1 and all(d.measurement_timestamp for d in pipe.defects):
        pipe.estimate_remaining_life()

    return pipe


@callback(
    Output('single_defect_table_graph', 'figure'),
    Output('single_defect_pipe_cross_section_graph', 'figure'),
    Output('single_defect_defect_cross_section_graph', 'figure'),
    Output('single_defect_table_analysis', 'children'),
    Output('single_defect_table_evaluation', 'children'),
    Output('single_defect_input_error_modal', 'is_open'),
    Output('single_defect_input_error_modal_body', 'children'),
    Input('single_defect_table_analyse', 'n_clicks'),
    State('single_defect_select_safety_class', 'value'),
    State('input-outer-diameter', 'value'),
    State('input-wall-thickness', 'value'),
    State('input-smts', 'value'),
    State('input-defect-length', 'value'),
    State('input-defect-width', 'value'),
    State('input-defect-depth', 'value'),
    State('unit-defect-depth', 'children'),
    State('input-defect-elevation', 'value'),
    State('input-design-pressure', 'value'),
    State('input-design-temp', 'value'),
    State('input-incidental-ratio', 'value'),
    State('input-accuracy', 'value'),
    State('input-confidence-level', 'value'),
    State('input-seawater-density', 'value'),
    State('input-containment-density', 'value'),
    State('input-elevation-reference', 'value'),
    State('input-axial-stress', 'value'),
    State('input-bending-stress', 'value'),
    State('input-combined-stress', 'value'),
    State('input-sec-length', 'value'),
    State('input-sec-width', 'value'),
    State('input-sec-depth', 'value'),
    State('unit-sec-defect-depth', 'children'),
    State('input-sec-separation', 'value'),
    State('single_defect_date_range', 'start_date'),
    State('single_defect_date_range', 'end_date'),
    State('theme-store', 'data'),
)
def calculate_pipe_characteristics(
        n_clicks,
        safety_class,
        outer_diameter, wall_thickness, smts,
        defect_length, defect_width, defect_depth, defect_depth_unit,
        defect_elevation, design_pressure, design_temp, incidental_ratio,
        accuracy, confidence_level,
        seawater_density, containment_density, elevation_reference,
        axial_stress, bending_stress, combined_stress,
        sec_length, sec_width, sec_depth, sec_depth_unit, sec_separation,
        start_date, end_date,
        theme,
):
    start_time = time.time()

    pipe_data = {
        'Pipe Outer Diameter': {'Value': outer_diameter, 'Unit': 'mm'},
        'Pipe Wall Thickness': {'Value': wall_thickness, 'Unit': 'mm'},
        'SMTS': {'Value': smts, 'Unit': 'MPa'},
        'Defect Length': {'Value': defect_length, 'Unit': 'mm'},
        'Defect Width': {'Value': defect_width, 'Unit': 'mm'},
        'Defect Depth': {'Value': defect_depth, 'Unit': defect_depth_unit},
        'Defect Elevation': {'Value': defect_elevation, 'Unit': 'm'},
        'Design Pressure': {'Value': design_pressure, 'Unit': 'bar'},
        'Design Temperature': {'Value': design_temp, 'Unit': '°C'},
        'Incidental to Design Pressure Ratio': {'Value': incidental_ratio, 'Unit': ''},
        'Accuracy': {'Value': accuracy, 'Unit': ''},
        'Confidence Level': {'Value': confidence_level, 'Unit': ''},
        'Safety Class': {'Value': safety_class, 'Unit': ''},
        'Seawater Density': {'Value': seawater_density, 'Unit': 'kg/m³'},
        'Containment Density': {'Value': containment_density, 'Unit': 'kg/m³'},
        'Elevation Reference': {'Value': elevation_reference, 'Unit': 'm'},
        'Axial Stress': {'Value': axial_stress, 'Unit': 'MPa'},
        'Bending Stress': {'Value': bending_stress, 'Unit': 'MPa'},
        'Combined Stress': {'Value': combined_stress, 'Unit': 'MPa'},
        'Secondary Defect Length': {'Value': sec_length, 'Unit': 'mm'},
        'Secondary Defect Width': {'Value': sec_width, 'Unit': 'mm'},
        'Secondary Defect Depth': {'Value': sec_depth, 'Unit': sec_depth_unit},
        'Secondary Defect Separation': {'Value': sec_separation, 'Unit': 'mm'},
        'First Date': {'Value': start_date, 'Unit': 'date'},
        'Second Date': {'Value': end_date, 'Unit': 'date'},
    }

    theme = theme or 'dark'
    error_encountered = False
    error = ''
    fig1 = fig2 = fig3 = analysis = evaluation = no_update

    try:
        required = {
            'Outer Diameter': outer_diameter, 'Wall Thickness': wall_thickness,
            'SMTS': smts, 'Defect Length': defect_length, 'Defect Depth': defect_depth,
            'Defect Elevation': defect_elevation, 'Design Pressure': design_pressure,
            'Design Temperature': design_temp, 'Incidental/Design Ratio': incidental_ratio,
            'Accuracy': accuracy, 'Confidence Level': confidence_level,
            'Seawater Density': seawater_density, 'Containment Density': containment_density,
            'Elevation Reference': elevation_reference,
        }
        missing = [k for k, v in required.items() if v is None]
        if missing:
            raise ValueError(f"Required fields are empty: {', '.join(missing)}")

        pipe = create_pipe(pipe_data)

        fig1 = defect_plots.generate_defect_depth_plot(pipe, theme=theme)
        fig2 = pipe_plots.generate_pipe_cross_section_plot(pipe, theme=theme)
        fig3 = pipe_plots.generate_defect_cross_section_plot(pipe, theme=theme)

        result_items = [
            dbc.ListGroupItem([html.Strong("Effective Pressure: "),
                               f"{pipe.properties.effective_pressure:.2f} MPa"]),
            dbc.ListGroupItem([html.Strong("Pressure Resistance: "),
                               f"{pipe.properties.pressure_resistance:.2f} MPa"]),
        ]
        if any(d.position for d in pipe.defects):
            interaction_text = ("Defect interaction found" if len(pipe.defects) == 3
                                else "No defect interaction found")
            result_items.append(dbc.ListGroupItem([html.Strong("Interaction: "), interaction_text]))
        if pipe.properties.remaining_life is not None:
            result_items.append(dbc.ListGroupItem(
                [html.Strong("Remaining Life: "), f"{pipe.properties.remaining_life:.0f} days"]
            ))
        analysis = dbc.Card([
            dbc.CardHeader("Results"),
            dbc.ListGroup(result_items, flush=True),
        ], className="mt-3 mb-3")

        evaluation = build_evaluation_alert(pipe.properties.effective_pressure, pipe.properties.pressure_resistance)
        logger.info(f"Single-Defect Scenario loaded | Processing time: {time.time() - start_time:.2f}s")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_encountered = True
        error = str(e)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        error_encountered = True
        error = "An unexpected error occurred. Please check your inputs and try again."

    return fig1, fig2, fig3, analysis, evaluation, error_encountered, error


@callback(
    Output('unit-defect-depth', 'children'),
    Output('unit-sec-defect-depth', 'children'),
    Output('unit-accuracy', 'children'),
    Input('single_defect_select_measurement', 'value'),
    prevent_initial_call=True,
)
def update_measurement_units(measurement: str):
    if measurement == 'relative':
        return 't', 't', ''
    return 'mm', 'mm', 'mm'


@callback(
    Output('input-combined-stress', 'value'),
    Input('input-axial-stress', 'value'),
    Input('input-bending-stress', 'value'),
    prevent_initial_call=True,
)
def update_combined_stress(axial, bending):
    axial_val = abs(float(axial)) if axial is not None else 0
    bending_val = abs(float(bending)) if bending is not None else 0
    if axial_val or bending_val:
        return axial_val + bending_val
    return no_update


@callback(
    Output("secondary_defect_collapse", "is_open"),
    Input("secondary_defect_collapse_button", "n_clicks"),
    State("secondary_defect_collapse", "is_open"),
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("single_defect_input_error_modal", "is_open", allow_duplicate=True),
    Input("single_defect_error_close", "n_clicks"),
    prevent_initial_call=True,
)
def close_error_modal(n_clicks):
    return False


@callback(
    Output("input_sidebar", "is_open"),
    Input("input_sidebar_toggle", "n_clicks"),
    State("input_sidebar", "is_open"),
    prevent_initial_call=True,
)
def toggle_input_sidebar(n, is_open):
    if n:
        return not is_open
    return is_open
