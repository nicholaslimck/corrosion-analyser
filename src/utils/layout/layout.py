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
            label=f"{utilisation:.1%} of capacity",
            color=colour,
            className='verdict-utilisation mb-2',
            style={'height': '1.25rem'},
        ))

    children.append(meta(f"Margin: {format_pressure(margin, unit)}"))

    clause = [STANDARD]
    if safety_class:
        clause.append(f"§2.3 Safety Class {str(safety_class).title()}")
    if design_factor is not None:
        clause.append(f"γm = {design_factor:.2f}")
    children.append(meta(' · '.join(clause)))

    if not is_acceptable:
        if pressure_resistance > 0:
            steps = [
                f"Reduce the operating pressure below "
                f"{format_pressure(pressure_resistance, unit)}.",
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


center_align_style = {
    "text-align": "center",
    "display": "flex",
    "justify-content": "center",
    "align-items": "center",
}
