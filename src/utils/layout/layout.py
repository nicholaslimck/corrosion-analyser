import dash_bootstrap_components as dbc
from dash import html

from src.utils.units import format_pressure
from src.utils.report import STANDARD


def build_evaluation_alert(effective_pressure: float, pressure_resistance: float,
                           unit: str = 'bar', *, safety_class: str | None = None,
                           design_factor: float | None = None) -> dbc.Alert:
    """The verdict as a decision object, not a sentence.

    Carries the utilisation against capacity, the margin in the selected unit,
    the governing clause and — on rejection — what to do next. Colour is never
    the only carrier of the outcome.
    """
    is_acceptable = effective_pressure < pressure_resistance
    comparison = '<' if is_acceptable else '>'
    status = 'acceptable' if is_acceptable else 'unacceptable'
    colour = 'success' if is_acceptable else 'danger'
    utilisation = (effective_pressure / pressure_resistance
                   if pressure_resistance else None)
    margin = pressure_resistance - effective_pressure

    def meta(text: str) -> html.P:
        return html.P(text, className='verdict-meta mb-1')

    children = [
        html.Div([
            html.Span('✔' if is_acceptable else '✖', className='verdict-icon me-2'),
            html.H5(f"Corrosion is {status}.", className='mb-0'),
        ], className='verdict-headline d-flex align-items-center justify-content-center'),
        html.P(f"Effective Pressure {format_pressure(effective_pressure, unit)} "
               f"{comparison} "
               f"Pressure Resistance {format_pressure(pressure_resistance, unit)}.",
               className="mb-2 mt-2"),
    ]

    if utilisation is not None:
        children.append(dbc.Progress(
            value=min(utilisation * 100, 100),
            label=(f"{utilisation:.1%} of capacity" if utilisation < 10
                   else 'over 999% of capacity'),
            color=colour,
            className='verdict-utilisation mb-2',
            style={'height': '1.25rem'},
        ))

    children.append(meta(f"Margin: {format_pressure(margin, unit)}"))

    clause = [STANDARD]
    if safety_class:
        clause.append(f"§3.3 Safety Class {str(safety_class).title()}")
    if design_factor is not None:
        clause.append(f"Table 3-2 γm = {design_factor:.2f}")
    children.append(meta(' · '.join(clause)))

    resistance_text = format_pressure(pressure_resistance, unit)
    if not is_acceptable:
        # Branch on the value as displayed: anything that renders as 0.00 takes
        # the acceptance-limits path, because "reduce the pressure below 0.00
        # bar" is not an instruction anyone can follow.
        if pressure_resistance > 0 and not resistance_text.startswith('0.00'):
            steps = [
                f"Reduce the operating pressure below "
                f"{resistance_text}.",
                "Re-inspect the defect, or re-classify the safety class.",
                "Repair or replace the affected pipe section.",
            ]
        else:
            # Zero resistance means the defect is outside acceptance limits,
            # not that the operating pressure is the lever.
            steps = [
                "The defect is outside the RP-F101 acceptance limits for this pipe.",
                "Re-inspect and repair, or replace, the affected pipe section.",
                "Re-assess with corrected geometry before returning it to service.",
            ]
        children.append(html.Ul([html.Li(step) for step in steps],
                                className='verdict-actions mb-0 mt-2 text-start'))

    return dbc.Alert(children, color=colour,
                     className="mt-3 text-center verdict-card")


def build_result_items(pipe, unit: str = 'bar') -> list:
    """The result summary list, with every pressure shown in the selected unit."""
    items = [
        dbc.ListGroupItem([html.Strong("Effective Pressure: "),
                           format_pressure(pipe.properties.effective_pressure, unit)]),
        dbc.ListGroupItem([html.Strong("Pressure Resistance: "),
                           format_pressure(pipe.properties.pressure_resistance, unit)]),
    ]
    if any(defect.position for defect in pipe.defects):
        interaction_text = ("Defect interaction found" if pipe.combined_defect is not None
                            else "No defect interaction found")
        items.append(dbc.ListGroupItem([html.Strong("Interaction: "), interaction_text]))
    if pipe.properties.remaining_life is not None:
        items.append(dbc.ListGroupItem(
            [html.Strong("Remaining Life: "), f"{pipe.properties.remaining_life:.0f} days"]))
    return items


def _num(value, digits: int = 2, unit: str = '') -> str:
    return '—' if value is None else f'{value:.{digits}f}{unit}'


def build_print_summary(report: dict | None) -> list:
    """The paper record: what was assessed, with which factors, and the outcome.

    The inputs live in a fixed offcanvas, and print hides it, so the PDF used to
    carry a verdict with no record of the pipe it belonged to. This renders the
    same report dictionary the JSON and Markdown exports use, so the paper and
    the file cannot disagree.
    """
    if not report:
        return []

    assessment = report['assessment']
    material = report['material']
    design = report['design']
    results = report['results']
    generated = report['generated_at'].replace('T', ' ')

    gamma_m = f"{assessment['gamma_m']:.2f}"
    gamma_d = f"{assessment['gamma_d']:.4f}"
    epsilon_d = f"{assessment['epsilon_d']:.4f}"
    xi = f"{assessment['xi']:.2f}"
    factors = f'{gamma_m} / {gamma_d} / {epsilon_d} / {xi}'

    def rows(pairs):
        body = [html.Tr([html.Th(label, scope='row'), html.Td(value)]) for label, value in pairs]
        return html.Table(html.Tbody(body), className='print-table')

    def section(title, body):
        return html.Div([html.H3(title, className='print-section-title'), body],
                        className='print-section')

    identity = html.Div([
        html.H2('Pipeline Corrosion Assessment', className='print-title mb-1'),
        html.P(f"{report['standard']} · generated {generated}", className='print-meta mb-0'),
    ], className='print-header')

    geometry = section('Geometry, material and assessment', rows([
        ('Outside diameter', _num(report['pipe']['outside_diameter_mm'], 1, ' mm')),
        ('Wall thickness', _num(report['pipe']['wall_thickness_mm'], 2, ' mm')),
        ('SMTS', _num(material['smts_mpa'], 1, ' MPa')),
        ('Design pressure', _num(design['design_pressure_bar'], 1, ' bar')),
        ('Incidental/design ratio', _num(design['incidental_to_design_ratio'])),
        ('Safety class', str(assessment['safety_class']).title()),
        ('Inspection method', str(assessment['measurement_method'])),
        ('Sizing accuracy', f"{assessment['measurement_accuracy']:g}"),
        ('Confidence level', f"{assessment['confidence_level']:g}"),
        ('γm / γd / εd / ξ', factors),
    ]))

    defect_rows = []
    for index, defect in enumerate(report['defects'], start=1):
        defect_rows.append(html.Tr([
            html.Td('Combined' if defect['combined'] else str(index)),
            html.Td(_num(defect['length_mm'], 1)),
            html.Td(_num(defect['width_mm'], 1)),
            html.Td(_num(defect['depth_mm'], 2)),
            html.Td(_num(defect['relative_depth'], 4)),
            html.Td(_num(defect['adjusted_relative_depth'], 4)),
            html.Td(_num(defect['pressure_resistance_mpa'])),
        ]))

    headings = ('Defect', 'Length [mm]', 'Width [mm]', 'Depth [mm]',
                'd/t', '(d/t)*', 'p_corr [MPa]')
    defect_table = html.Table([
        html.Thead(html.Tr([html.Th(heading) for heading in headings])),
        html.Tbody(defect_rows),
    ], className='print-table')
    defects = section('Defects', defect_table)

    outcome = section('Results', rows([
        ('Effective pressure', f"{results['effective_pressure_mpa']:.3f} MPa "
                               f"({results['effective_pressure_bar']:.2f} bar)"),
        ('Pressure resistance', f"{results['pressure_resistance_mpa']:.3f} MPa "
                                f"({results['pressure_resistance_bar']:.2f} bar)"),
        ('Margin', f"{report['verdict']['pressure_margin_mpa']:+.3f} MPa"),
        ('Verdict', 'Acceptable' if report['verdict']['acceptable'] else 'Not acceptable'),
    ]))

    return [identity, geometry, defects, outcome]


center_align_style = {
    "text-align": "center",
    "display": "flex",
    "justify-content": "center",
    "align-items": "center",
}
