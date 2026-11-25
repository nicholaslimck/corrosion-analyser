"""Plotly chart theming for dark and light colour palettes.

Public API:
    get_palette(theme) -> dict
    apply_theme(fig, theme) -> go.Figure
"""
import plotly.graph_objects as go

_DARK = dict(
    plot_bgcolor='#0f172a',
    paper_bgcolor='#1e293b',
    font_color='#f1f5f9',
    gridcolor='#334155',
    axis_color='#94a3b8',
    limit_curve_color='#38bdf8',
    marker_pass_color='#38bdf8',
    marker_fail_color='#ef4444',
    # The defect itself stays #E53E3E, but #E53E3E as *text* over the tinted
    # fill measured 2.63:1. Labels get their own, theme-appropriate red.
    defect_text_color='#fca5a5',
)

_LIGHT = dict(
    plot_bgcolor='#ffffff',
    paper_bgcolor='#f8fafc',
    font_color='#0f172a',
    gridcolor='#e2e8f0',
    axis_color='#475569',
    limit_curve_color='#0ea5e9',
    marker_pass_color='#0ea5e9',
    marker_fail_color='#dc2626',
    defect_text_color='#991b1b',
)

_PALETTES = {'dark': _DARK, 'light': _LIGHT}


# The modebar is Plotly's own toolbar. On these three static illustrations it
# costs eleven tab stops at 24x22 with a 1.44:1 focus ring, for tools that do
# nothing here - the assessment is already exported as PDF, Markdown and JSON.
GRAPH_CONFIG = {'displayModeBar': False, 'displaylogo': False}


def get_palette(theme: str = 'dark') -> dict:
    return _PALETTES.get(theme, _DARK)


def apply_theme(fig: go.Figure, theme: str = 'dark') -> go.Figure:
    p = get_palette(theme)
    fig.update_layout(
        plot_bgcolor=p['plot_bgcolor'],
        paper_bgcolor=p['paper_bgcolor'],
        font=dict(color=p['font_color']),
    )
    fig.update_xaxes(gridcolor=p['gridcolor'], color=p['axis_color'], zerolinecolor=p['gridcolor'])
    fig.update_yaxes(gridcolor=p['gridcolor'], color=p['axis_color'], zerolinecolor=p['gridcolor'])
    return fig
