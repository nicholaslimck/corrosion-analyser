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
    limits = pipe.properties.maximum_allowable_defect_depth

    # Plot figure
    fig = px.line(
        limits, x='defect_length', y='defect_depth',
        color_discrete_sequence=['red'],
        labels={
            'defect_length': 'Corrosion Defect Length (mm)',
            'defect_depth': 'Allowable Measured Relative Depth (d/t)'
        },
        range_y=[0, 1.0], range_x=[0, 1000])

    marker_df = pd.DataFrame(
        {
            'defect_length': pipe.defects[0].length,
            'defect_depth': pipe.defects[0].relative_depth,
            'pressure_resistance': round(pipe.defects[0].pressure_resistance, 2)
        }, index=[0])
    marker_colour = 'blue' if pipe.properties.effective_pressure <= pipe.defects[0].pressure_resistance else 'red'
    marker = px.scatter(marker_df, x='defect_length', y='defect_depth', text='pressure_resistance',
                        color_discrete_sequence=[marker_colour])

    fig.add_trace(marker.data[0])

    fig['data'][0]['showlegend'] = True
    fig['data'][1]['showlegend'] = True
    fig['data'][0]['name'] = 'Calculated Limits'
    fig['data'][1]['name'] = 'Measured Defect'

    if len(pipe.defects) > 1:
        secondary_marker_df = pd.DataFrame(
            {
                'defect_length': [pipe.defects[1].length],
                'defect_depth': [pipe.defects[1].relative_depth],
                'pressure_resistance': round(pipe.defects[1].pressure_resistance, 2)
            }, index=[0])
        secondary_marker_colour = 'blue' if pipe.properties.effective_pressure <= pipe.defects[1].pressure_resistance else 'red'
        secondary_marker = px.scatter(secondary_marker_df, x='defect_length', y='defect_depth',
                                     text='pressure_resistance',
                                      color_discrete_sequence=[secondary_marker_colour])

        fig.add_trace(secondary_marker.data[0])
        fig['data'][2]['showlegend'] = True
        fig['data'][2]['name'] = 'Second Measured Defect'
        # set secondary marker to be a square
        fig['data'][2]['marker']['symbol'] = 'square'
    if len(pipe.defects) > 2:
        tertiary_marker_df = pd.DataFrame(
            {
                'defect_length': [pipe.defects[2].length],
                'defect_depth': [pipe.defects[2].relative_depth],
                'pressure_resistance': round(pipe.defects[2].pressure_resistance, 2)
            }, index=[0])
        tertiary_marker_colour = 'blue' if pipe.properties.effective_pressure <= pipe.defects[2].pressure_resistance else 'red'
        tertiary_marker = px.scatter(tertiary_marker_df, x='defect_length', y='defect_depth',
                                     text='pressure_resistance',
                                     color_discrete_sequence=[tertiary_marker_colour])

        fig.add_trace(tertiary_marker.data[0])
        fig['data'][3]['showlegend'] = True
        fig['data'][3]['name'] = 'Combined Defect'
        # set secondary marker to be a square
        fig['data'][3]['marker']['symbol'] = 'x'

    fig.update_traces(textposition='top center')

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
