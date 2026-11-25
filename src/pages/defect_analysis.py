import datetime
import json
import time

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, no_update
from dash.dependencies import Input, Output, State
from loguru import logger

from src.utils import models
from src.utils.graphing import defect_plots, pipe_plots
from src.utils.assessment import build_pipe
from src.utils.report import build_report, filename, render_markdown
from src.utils.layout import center_align_style, build_evaluation_alert, build_result_items
from src.utils.units import format_pressure, from_bar, to_bar

dash.register_page(__name__)


def _input_row(label: str, input_id: str, default, unit: str, unit_id: str | None = None,
               optional: bool = False) -> dbc.Row:
    unit_component = (dbc.InputGroupText(unit, id=unit_id)
                      if unit_id else dbc.InputGroupText(unit))
    return dbc.Row([
        dbc.Col(html.Label(f"{label}{' (optional)' if optional else ''}",
                           htmlFor=input_id, className='col-form-label small'), width=7),
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
            _input_row('Width', 'input-defect-width', None, 'mm', optional=True),
            _input_row('Depth', 'input-defect-depth', 0.25, 't', unit_id='unit-defect-depth'),
        ], title='Defect', item_id='defect'),

        dbc.AccordionItem([
            _input_row('Elevation', 'input-defect-elevation', -100, 'm'),
            _input_row('Design Pressure', 'input-design-pressure', 150, 'bar',
                       unit_id='unit-design-pressure'),
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
                    html.Label("Safety Class", htmlFor='single_defect_select_safety_class',
                               className="col-form-label small"),
                    dbc.Select(
                        id='single_defect_select_safety_class',
                        value='medium',
                        options=[
                            {'label': 'Low', 'value': 'low'},
                            {'label': 'Medium', 'value': 'medium'},
                            {'label': 'High', 'value': 'high'},
                            {'label': 'Very High', 'value': 'very high'},
                        ],
                        size="sm",
                    ),
                ]),
                dbc.Col([
                    html.Label("Defect depth unit", htmlFor='single_defect_select_measurement',
                               className="col-form-label small"),
                    dbc.Select(
                        id='single_defect_select_measurement',
                        value='relative',
                        options=[
                            {'label': 'Fraction of t', 'value': 'relative'},
                            {'label': 'Millimetre', 'value': 'absolute'},
                        ],
                        size="sm",
                    ),
                ]),
            ], className="mb-2"),
            dbc.Row(
                dbc.Col([
                    html.Label("Sizing accuracy", htmlFor='single_defect_select_accuracy_type',
                               className="col-form-label small"),
                    dbc.Select(
                        id='single_defect_select_accuracy_type',
                        value='relative',
                        options=[
                            {'label': 'Relative (fraction of t)', 'value': 'relative'},
                            {'label': 'Absolute (mm)', 'value': 'absolute'},
                        ],
                        size="sm",
                    ),
                ]),
                className="mb-3",
            ),
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
            html.Div(id='single_defect_table_analysis'),
            html.Div(
                dbc.Button(
                    'Analyse',
                    id='single_defect_table_analyse',
                    className='w-100',
                    color='primary',
                ),
                className='analyse-footer',
            ),
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
            # The verdict leads. This is a pass/fail tool: the answer is the
            # first thing after the title, not the fourth thing after two
            # schematics that carry no decision.
            dbc.Row(
                dbc.Col(html.Div(id='single_defect_table_evaluation'), xs=12, md=10),
                justify='center'
            ),
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
                dbc.Col(html.Div(id='calculation-trace'), xs=12, md=10),
                justify='center'
            ),
            dbc.Row(
                dbc.Col(
                    html.Div([
                        dbc.Button('Print / Save as PDF', id='print-button', color='secondary',
                                   outline=True, size='sm', className='me-2',
                                   title='Prints in the current theme - switch to light first '
                                         'for a print-friendly copy'),
                        dbc.Button('Download Markdown', id='download-markdown-button', color='secondary',
                                   outline=True, size='sm', className='me-2'),
                        dbc.Button('Download JSON', id='download-json-button', color='secondary',
                                   outline=True, size='sm'),
                        html.Div(id='print-trigger', style={'display': 'none'}),
                    ], className='text-center mt-2'),
                    xs=12, md=10
                ),
                justify='center',
                className='no-print'
            ),
            dcc.Store(id='report-store', storage_type='memory'),
            dcc.Store(id='pressure-unit-previous', data='bar'),
            dcc.Store(id='depth-unit-previous', data='relative'),
            dcc.Download(id='download-markdown'),
            dcc.Download(id='download-json'),
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
    """Build the pipe model from the interface inputs and run the assessment."""
    pipe = build_pipe(pipe_data)
    pipe.analyze()
    return pipe


@callback(
    Output('single_defect_table_graph', 'figure'),
    Output('single_defect_pipe_cross_section_graph', 'figure'),
    Output('single_defect_defect_cross_section_graph', 'figure'),
    Output('single_defect_table_analysis', 'children'),
    Output('single_defect_table_evaluation', 'children'),
    Output('single_defect_input_error_modal', 'is_open'),
    Output('single_defect_input_error_modal_body', 'children'),
    Output('report-store', 'data'),
    Input('single_defect_table_analyse', 'n_clicks'),
    State('single_defect_select_safety_class', 'value'),
    State('single_defect_select_accuracy_type', 'value'),
    State('input-outer-diameter', 'value'),
    State('input-wall-thickness', 'value'),
    State('input-smts', 'value'),
    State('input-defect-length', 'value'),
    State('input-defect-width', 'value'),
    State('input-defect-depth', 'value'),
    State('unit-defect-depth', 'children'),
    State('input-defect-elevation', 'value'),
    Input('input-design-pressure', 'value'),
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
    Input('theme-store', 'data'),
    Input('pressure-unit', 'value'),
)
def calculate_pipe_characteristics(
        n_clicks,
        safety_class,
        sizing_accuracy_type,
        outer_diameter, wall_thickness, smts,
        defect_length, defect_width, defect_depth, defect_depth_unit,
        defect_elevation, design_pressure, design_temp, incidental_ratio,
        accuracy, confidence_level,
        seawater_density, containment_density, elevation_reference,
        axial_stress, bending_stress, combined_stress,
        sec_length, sec_width, sec_depth, sec_depth_unit, sec_separation,
        start_date, end_date,
        theme, pressure_unit,
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
        'Design Pressure': {'Value': design_pressure, 'Unit': pressure_unit},
        'Design Temperature': {'Value': design_temp, 'Unit': '°C'},
        'Incidental to Design Pressure Ratio': {'Value': incidental_ratio, 'Unit': ''},
        'Accuracy': {'Value': accuracy, 'Unit': ''},
        'Confidence Level': {'Value': confidence_level, 'Unit': ''},
        'Safety Class': {'Value': safety_class, 'Unit': ''},
        'Sizing Accuracy Type': {'Value': sizing_accuracy_type, 'Unit': ''},
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
    pressure_unit = pressure_unit or 'bar'
    error_encountered = False
    error = ''
    fig1 = fig2 = fig3 = analysis = evaluation = report = no_update

    try:
        # Input validation and model construction live in src.utils.assessment
        pipe = create_pipe(pipe_data)

        fig1 = defect_plots.generate_defect_depth_plot(pipe, theme=theme,
                                                       pressure_unit=pressure_unit)
        fig2 = pipe_plots.generate_pipe_cross_section_plot(pipe, theme=theme)
        fig3 = pipe_plots.generate_defect_cross_section_plot(pipe, theme=theme)

        analysis = dbc.Card([
            dbc.CardHeader("Results"),
            dbc.ListGroup(build_result_items(pipe, pressure_unit), flush=True),
        ], className="mt-3 mb-3")

        evaluation = build_evaluation_alert(
            pipe.properties.effective_pressure,
            pipe.properties.pressure_resistance,
            pressure_unit,
            safety_class=pipe.factors.safety_class,
            design_factor=pipe.factors.gamma_m,
        )
        report = build_report(pipe)
        logger.info(f"Single-Defect Scenario loaded | Processing time: {time.time() - start_time:.2f}s")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_encountered = True
        error = str(e)
        # Clear the stored report. Leaving the previous assessment in place let the
        # export buttons hand out an older result's numbers after a failed run.
        report = None
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        error_encountered = True
        error = "An unexpected error occurred. Please check your inputs and try again."
        report = None

    return fig1, fig2, fig3, analysis, evaluation, error_encountered, error, report


def _trace_table(rows):
    return dbc.Table([
        html.Thead(html.Tr([html.Th('Quantity'), html.Th('Value'), html.Th('Source')])),
        html.Tbody([
            html.Tr([html.Td(quantity), html.Td(value), html.Td(source, className='text-muted')])
            for quantity, value, source in rows
        ]),
    ], bordered=False, striped=True, size='sm', className='mb-0')


def build_calculation_trace(report, pressure_unit='bar'):
    """
    The intermediate values behind a verdict, each with the clause it comes from.

    The assessment is only as trustworthy as the numbers going into it, so they are
    shown rather than left implicit: a reader can reproduce the result by hand.
    """
    if not report:
        return html.P('Run an analysis to see the calculation trace.',
                      className='text-muted small mb-0 mt-2')

    pipe_ = report['pipe']
    material = report['material']
    design = report['design']
    assessment = report['assessment']
    environment = report['environment']
    results = report['results']

    inputs = [
        ('Outside diameter, D', f"{pipe_['outside_diameter_mm']:.1f} mm", '§2.1'),
        ('Wall thickness, t', f"{pipe_['wall_thickness_mm']:.2f} mm", '§2.1'),
        ('SMTS', f"{material['smts_mpa']:.1f} N/mm²", '§2.6'),
        ('Design temperature', f"{material['design_temperature_c']:.0f} °C", 'Figure 2-3'),
        ('Design pressure, p_d', f"{from_bar(design['design_pressure_bar'], pressure_unit):.2f} {pressure_unit}", '§1.13'),
        ('Incidental/design ratio, γinc', f"{design['incidental_to_design_ratio']:.2f}", '§3.7.2.2'),
        ('De-rating, f_u,temp', f"{material['de_rating_mpa']:.1f} N/mm²", 'Figure 2-3'),
        ('Tensile strength, f_u', f"{material['f_u_mpa']:.2f} N/mm²", 'Table 2-1'),
        ('Safety class', str(assessment['safety_class']).title(), '§3.3'),
        ('Inspection method', assessment['measurement_method'], '§3.3'),
        ('Sizing accuracy',
         f"{assessment['measurement_accuracy']:g} "
         f"({'fraction of t' if assessment['measurement_method'] == 'relative' else 'mm'})",
         '§3.3'),
        ('Confidence level', f"{assessment['confidence_level']:.0%}", 'Table 3-3'),
        ('StD[d/t], σd', f"{assessment['standard_deviation']:.4f}", 'Tables 3-3 to 3-6'),
        ('Partial safety factor, γm', f"{assessment['gamma_m']:.2f}", 'Table 3-2'),
        ('Partial safety factor, γd', f"{assessment['gamma_d']:.4f}", 'Tables 3-7, 3-8'),
        ('Fractile value, εd', f"{assessment['epsilon_d']:.4f}", 'Tables 3-7, 3-8'),
        ('Usage factor, ξ', f"{assessment['xi']:.2f}", 'Table 3-10'),
        ('Incidental pressure, p_inc', format_pressure(environment['incidental_pressure_mpa'], pressure_unit, 3),
         '§3.7.2.2'),
        ('External pressure, p_le', format_pressure(environment['external_pressure_mpa'], pressure_unit, 3), '§3.7.2.2'),
        ('Effective pressure, p_li − p_le', format_pressure(results['effective_pressure_mpa'], pressure_unit, 3),
         '§3.7.2.2'),
        ('Pressure resistance, p_corr', format_pressure(results['pressure_resistance_mpa'], pressure_unit, 3), '§3.7.3.1'),
    ]
    defects = [
        (f"Defect {index} ({'combined' if defect['combined'] else 'measured'})",
         f"l = {defect['length_mm']:.1f} mm, d/t = {defect['relative_depth']:.4f}, "
         f"(d/t)* = {defect['adjusted_relative_depth']:.4f}, "
         f"Q = {defect['length_correction_factor']:.4f}, "
         f"p_corr = {format_pressure(defect['pressure_resistance_mpa'], pressure_unit, 3)}",
         '§3.7.3.1, §3.8.2')
        for index, defect in enumerate(report['defects'], start=1)
    ]

    return dbc.Accordion([
        dbc.AccordionItem(_trace_table(inputs), title='Inputs and partial safety factors'),
        dbc.AccordionItem(_trace_table(defects), title='Defect geometry and capacity'),
    ], start_collapsed=True, className='mt-3 small text-start')


@callback(
    Output('calculation-trace', 'children'),
    Input('report-store', 'data'),
    Input('pressure-unit', 'value'),
)
def update_calculation_trace(report, pressure_unit='bar'):
    return build_calculation_trace(report, pressure_unit or 'bar')


@callback(
    Output('input-design-pressure', 'value'),
    Output('pressure-unit-previous', 'data'),
    Input('pressure-unit', 'value'),
    State('pressure-unit-previous', 'data'),
    State('input-design-pressure', 'value'),
    prevent_initial_call=True,
)
def convert_design_pressure(unit, previous_unit, design_pressure):
    """Converting the entry on a unit change rather than re-reading it.

    Reinterpretation silently changed the physics of an untouched field: an
    assessment that failed at 150 bar passed when the selector moved to psi and
    the number was left alone.
    """
    unit = unit or 'bar'
    previous_unit = previous_unit or 'bar'
    if design_pressure is None or unit == previous_unit:
        return no_update, unit
    converted = from_bar(to_bar(float(design_pressure), previous_unit), unit)
    return float(f'{converted:.6g}'), unit


@callback(
    Output('download-markdown-button', 'disabled'),
    Output('download-json-button', 'disabled'),
    Input('report-store', 'data'),
)
def toggle_export_buttons(report):
    """Export only means something while there is a current assessment to export."""
    disabled = report is None
    return disabled, disabled


@callback(
    Output('download-markdown', 'data'),
    Input('download-markdown-button', 'n_clicks'),
    State('report-store', 'data'),
    prevent_initial_call=True,
)
def download_markdown(n_clicks, report):
    if not n_clicks or not report:
        return no_update
    return dcc.send_string(render_markdown(report), filename(report, 'md'))


@callback(
    Output('download-json', 'data'),
    Input('download-json-button', 'n_clicks'),
    State('report-store', 'data'),
    prevent_initial_call=True,
)
def download_json(n_clicks, report):
    if not n_clicks or not report:
        return no_update
    return dcc.send_string(json.dumps(report, indent=2), filename(report, 'json'))


@callback(
    Output('unit-design-pressure', 'children'),
    Input('pressure-unit', 'value'),
)
def update_pressure_unit_label(unit: str):
    return unit or 'bar'


@callback(
    Output('unit-defect-depth', 'children'),
    Output('unit-sec-defect-depth', 'children'),
    Output('unit-accuracy', 'children'),
    Output('input-defect-depth', 'value'),
    Output('depth-unit-previous', 'data'),
    Input('single_defect_select_measurement', 'value'),
    Input('single_defect_select_accuracy_type', 'value'),
    State('input-defect-depth', 'value'),
    State('depth-unit-previous', 'data'),
    State('input-wall-thickness', 'value'),
    prevent_initial_call=True,
)
def update_input_units(depth_unit: str, accuracy_type: str, depth_value,
                       previous_depth_unit: str, wall_thickness):
    """
    Depth and sizing accuracy units are independent choices: the standard pairs
    relative or absolute accuracy with either depth representation (3.3).

    Converting the entry on a unit change mirrors convert_design_pressure. A
    relabel left the digits alone, so 0.25 t became 0.25 mm - a 76x shallower
    defect - and the assessment re-ran on the new meaning without saying so.
    """
    depth_unit = depth_unit or 'relative'
    previous_depth_unit = previous_depth_unit or 'relative'
    depth_label = 't' if depth_unit == 'relative' else 'mm'
    # A blank suffix made "0.1" look like 0.1 mm when it means 10% of t.
    accuracy_label = 'fraction of t' if accuracy_type == 'relative' else 'mm'

    converted = no_update
    thickness = float(wall_thickness) if wall_thickness not in (None, '') else 0.0
    if (depth_value not in (None, '') and depth_unit != previous_depth_unit
            and thickness > 0):
        value = float(depth_value)
        converted_value = value * thickness if depth_unit == 'absolute' else value / thickness
        converted = float(f'{converted_value:.6g}')

    return depth_label, depth_label, accuracy_label, converted, depth_unit


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
