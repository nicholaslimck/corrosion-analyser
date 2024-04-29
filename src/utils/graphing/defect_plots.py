import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils import models


def generate_defect_depth_plot(pipe: models.Pipe) -> go.Figure:
    """
    Generates a plot to represent the pipe's current state, with a single defect represented as a point
    with the maximum allowable defect depth at each length represented as a line.
    Args:
        pipe: Pipe object

    Returns:
        fig: Figure
    """
    # Plot figure
    fig = px.line(
        pipe.properties.maximum_allowable_defect_depth[0], x='defect_length', y='defect_relative_depth',
        color_discrete_sequence=['red'],
        labels={
            'defect_length': 'Corrosion Defect Length (mm)',
            'defect_relative_depth': 'Allowable Measured Relative Depth (d/t)'
        },
        range_y=[0, 1.0], range_x=[0, 1000])

    if len(pipe.properties.maximum_allowable_defect_depth) > 1:
        interacting_limits = px.line(
            pipe.properties.maximum_allowable_defect_depth[1], x='defect_length', y='defect_relative_depth',
            color_discrete_sequence=['red'],
            line_dash_sequence=['dash'],
            labels={
                'defect_length': 'Corrosion Defect Length (mm)',
                'defect_relative_depth': 'Allowable Measured Relative Depth (d/t)'
            },
            range_y=[0, 1.0], range_x=[0, 1000]
        )
        fig.add_trace(interacting_limits.data[0])

    def add_marker(defect):
        marker_df = pd.DataFrame(
            {
                'defect_length': defect.length,
                'defect_relative_depth': defect.relative_depth,
                'pressure_resistance': round(defect.pressure_resistance, 2)
            }, index=[0])
        marker_colour = 'blue' if pipe.properties.effective_pressure <= defect.pressure_resistance else 'red'
        marker = px.scatter(marker_df, x='defect_length', y='defect_relative_depth', text='pressure_resistance',
                            color_discrete_sequence=[marker_colour])

        fig.add_trace(marker.data[0])

    for defect in pipe.defects:
        add_marker(defect)

    fig.update_traces(textposition='top center')

    if len(fig['data']) == 2:
        fig['data'][0]['showlegend'] = True
        fig['data'][1]['showlegend'] = True
        fig['data'][0]['name'] = 'Calculated Limits'
        fig['data'][1]['name'] = 'Measured Defect'
    elif len(fig['data']) == 3:
        fig['data'][0]['showlegend'] = True
        fig['data'][1]['showlegend'] = True
        fig['data'][2]['showlegend'] = True

        fig['data'][0]['name'] = 'Calculated Limits'
        fig['data'][1]['name'] = 'Measured Defect'
        fig['data'][2]['name'] = 'Second Measured Defect'
        # set secondary marker to be a square
        fig['data'][2]['marker']['symbol'] = 'square'
    elif len(fig['data']) == 5:
        fig['data'][0]['showlegend'] = True
        fig['data'][1]['showlegend'] = True
        fig['data'][2]['showlegend'] = True
        fig['data'][3]['showlegend'] = True
        fig['data'][4]['showlegend'] = True

        fig['data'][0]['name'] = 'Calculated Limits - Primary'
        fig['data'][1]['name'] = 'Calculated Limits - Interacting'
        fig['data'][2]['name'] = 'Measured Defect'
        fig['data'][3]['name'] = 'Second Measured Defect'
        fig['data'][4]['name'] = 'Combined Defect'

        # set secondary marker to be a square
        fig['data'][3]['marker']['symbol'] = 'square'
        # set combined marker to be a square
        fig['data'][4]['marker']['symbol'] = 'x'

    fig.update_layout(
        # height=800,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1)
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
