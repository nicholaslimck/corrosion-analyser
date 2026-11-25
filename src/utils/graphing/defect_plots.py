import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils import models
from src.utils.graphing.theme import apply_theme, get_palette


def generate_defect_depth_plot(pipe: models.Pipe, theme: str = 'dark') -> go.Figure:
    p = get_palette(theme)

    fig = px.line(
        pipe.properties.maximum_allowable_defect_depth[0], x='defect_length', y='defect_relative_depth',
        color_discrete_sequence=[p['limit_curve_color']],
        labels={
            'defect_length': 'Corrosion Defect Length (mm)',
            'defect_relative_depth': 'Allowable Measured Relative Depth (d/t)'
        },
        range_y=[0, 1.0])

    max_defect_length = max(defect.length for defect in pipe.assessment_defects)
    x_max = max(max_defect_length * 2, 500)
    fig.update_xaxes(range=[0, x_max])

    if len(pipe.properties.maximum_allowable_defect_depth) > 1:
        interacting_limits = px.line(
            pipe.properties.maximum_allowable_defect_depth[1], x='defect_length', y='defect_relative_depth',
            color_discrete_sequence=[p['limit_curve_color']],
            line_dash_sequence=['dash'],
            labels={
                'defect_length': 'Corrosion Defect Length (mm)',
                'defect_relative_depth': 'Allowable Measured Relative Depth (d/t)'
            },
            range_y=[0, 1.0]
        )
        fig.add_trace(interacting_limits.data[0])

    def add_marker(defect):
        marker_df = pd.DataFrame({
            'defect_length': defect.length,
            'defect_relative_depth': defect.relative_depth,
            'pressure_resistance': round(defect.pressure_resistance, 2)
        }, index=[0])
        passes = pipe.properties.effective_pressure <= defect.pressure_resistance
        colour = p['marker_pass_color'] if passes else p['marker_fail_color']
        marker = px.scatter(marker_df, x='defect_length', y='defect_relative_depth',
                            text='pressure_resistance', color_discrete_sequence=[colour])
        fig.add_trace(marker.data[0])

    for defect in pipe.assessment_defects:
        add_marker(defect)

    fig.update_traces(textposition='top center')

    # Label the traces from the structure of the assessment rather than from the number
    # of traces plotted: a count based mapping silently mislabels the series as soon as
    # one is added, dropped or reordered.
    interacting = len(pipe.properties.maximum_allowable_defect_depth) > 1
    curve_names = (['Calculated Limits - Primary', 'Calculated Limits - Interacting']
                   if interacting else ['Calculated Limits'])
    for index, name in enumerate(curve_names):
        fig['data'][index].update(showlegend=True, name=name)

    first_marker = len(curve_names)
    measured_count = len(pipe.defects)
    for index, defect in enumerate(pipe.assessment_defects):
        trace = fig['data'][first_marker + index]
        if defect is pipe.combined_defect:
            trace.update(showlegend=True, name='Combined Defect', marker=dict(symbol='x'))
        elif measured_count == 1:
            trace.update(showlegend=True, name='Measured Defect')
        else:
            updates = {'showlegend': True, 'name': f'Measured Defect {index + 1}'}
            if index == 1:
                updates['marker'] = dict(symbol='square')
            trace.update(**updates)

    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return apply_theme(fig, theme)
