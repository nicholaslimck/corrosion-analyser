import dash_bootstrap_components as dbc
from dash import html

from src.utils.units import format_pressure


def build_evaluation_alert(effective_pressure: float, pressure_resistance: float,
                           unit: str = 'bar') -> dbc.Alert:
    is_acceptable = effective_pressure < pressure_resistance
    comparison = '<' if is_acceptable else '>'
    status = 'acceptable' if is_acceptable else 'unacceptable'
    return dbc.Alert(
        [
            html.P(f"Effective Pressure {format_pressure(effective_pressure, unit)} "
                   f"{comparison} "
                   f"Pressure Resistance {format_pressure(pressure_resistance, unit)}.",
                   className="mb-2"),
            html.H5(f"Corrosion is {status}.", className="mb-0"),
        ],
        color="success" if is_acceptable else "danger",
        className="mt-3 text-center",
    )


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
