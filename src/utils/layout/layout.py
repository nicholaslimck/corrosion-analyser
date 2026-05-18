import dash_bootstrap_components as dbc
from dash import html


def build_evaluation_alert(effective_pressure: float, pressure_resistance: float) -> dbc.Alert:
    is_acceptable = effective_pressure < pressure_resistance
    comparison = '<' if is_acceptable else '>'
    status = 'acceptable' if is_acceptable else 'unacceptable'
    return dbc.Alert(
        [
            html.P(f"Effective Pressure {effective_pressure:.2f} MPa "
                   f"{comparison} "
                   f"Pressure Resistance {pressure_resistance:.2f} MPa.",
                   className="mb-2"),
            html.H5(f"Corrosion is {status}.", className="mb-0"),
        ],
        color="success" if is_acceptable else "danger",
        className="mt-3 text-center",
    )


center_align_style = {
    "text-align": "center",
    "display": "flex",
    "justify-content": "center",
    "align-items": "center",
}
