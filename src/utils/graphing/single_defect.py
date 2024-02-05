import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    # limits = pipe.calculate_acceptable_limits()
    limits_alt = pipe.calculate_acceptable_limits()

    # Plot figure
    fig = px.line(
        limits_alt, x='defect_length', y='defect_depth',
        color_discrete_sequence=['red'],
        labels={
            'defect_length': 'Corrosion Defect Length (mm)',
            'defect_depth': 'Allowable Measured Relative Depth (d/t)'
        },
        range_y=[0, 1.0], range_x=[0, 1000])

    marker_df = pd.DataFrame(
        {
            'defect_length': pipe.defect.length,
            'defect_depth': pipe.defect.relative_depth
        }, index=[0])

    if pipe.properties.effective_pressure <= pipe.properties.pressure_resistance:
        colour = 'blue'
    else:
        colour = 'red'

    marker = px.scatter(marker_df, x='defect_length', y='defect_depth', color_discrete_sequence=[colour])

    fig.add_trace(marker.data[0])

    fig['data'][0]['showlegend'] = True
    fig['data'][1]['showlegend'] = True
    fig['data'][0]['name'] = 'Calculated Limits'
    fig['data'][1]['name'] = 'Measured Defect'

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


def generate_cross_section_plot(pipe: models.Pipe, orientation: str = 'vertical') -> go.Figure:
    """
    Generates a pair of plots as cross-sectional representations of the pipe and defect.
    Args:
        pipe: Pipe object
        orientation: 'horizontal' or 'vertical'

    Returns:
        fig: Figure
    """
    outer_diameter = pipe.dimensions.outside_diameter
    inner_diameter = pipe.dimensions.outside_diameter - 2 * pipe.dimensions.wall_thickness
    thickness = pipe.dimensions.wall_thickness

    if orientation == 'vertical':
        fig = make_subplots(rows=2, cols=1)
        sp1_placement = {
            'row': 1,
            'col': 1
        }
        sp2_placement = {
            'row': 2,
            'col': 1
        }
    elif orientation == 'horizontal':
        fig = make_subplots(rows=1, cols=2)
        sp1_placement = {
            'row': 1,
            'col': 1
        }
        sp2_placement = {
            'row': 1,
            'col': 2
        }
    else:
        raise ValueError('Unsupported orientation')

    # Set up pipe cross-section plot
    fig.add_trace(go.Scatter(
        x=[0, 0, 0],
        y=[outer_diameter / 2, outer_diameter / 2.4, outer_diameter / 3],
        text=[f"Outer Diameter: {outer_diameter:.2f}",
              f"Wall Thickness: {thickness:.2f}",
              f"Inner Diameter: {inner_diameter:.2f}"],
        mode="text"),
        **sp1_placement
    )
    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-outer_diameter / 2, y0=-outer_diameter / 2,
        x1=outer_diameter / 2, y1=outer_diameter / 2,
        line_color="LightSeaGreen", **sp1_placement
    )
    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-inner_diameter / 2, y0=-inner_diameter / 2,
        x1=inner_diameter / 2, y1=inner_diameter / 2,
        line_color="LightSeaGreen", **sp1_placement
    )

    fig.update_xaxes(range=[-outer_diameter / 2 * 1.05, outer_diameter / 2 * 1.05],
                     zeroline=False, fixedrange=True, row=1, col=1)
    fig.update_yaxes(range=[-outer_diameter / 2 * 1.05, outer_diameter / 2 * 1.05],
                     zeroline=False, fixedrange=True, row=1, col=1)

    # Set up defect cross-section subplot
    fig.add_shape(
        type="rect",
        fillcolor="LightSeaGreen",
        xref="x", yref="y",
        x0=-10, y0=0,
        x1=pipe.defect.length * 2.05, y1=thickness,
        label=dict(text=f"Wall Thickness: {thickness:.2f}", font=dict(color="White")),
        # opacity=0.5,
        **sp2_placement)
    fig.add_shape(
        type="rect",
        fillcolor="LightSalmon",
        xref="x", yref="y",
        x0=pipe.defect.length * 0.5, y0=pipe.dimensions.wall_thickness - pipe.defect.depth,
        x1=pipe.defect.length * 1.5, y1=pipe.dimensions.wall_thickness,
        opacity=0.6,
        label=dict(text=f"Defect Depth: {pipe.defect.depth:.2f}", font=dict(color="White")),
        **sp2_placement)
    fig.update_xaxes(range=[0, pipe.defect.length * 2], fixedrange=True, **sp2_placement)
    fig.update_yaxes(range=[-pipe.dimensions.wall_thickness * 0.05, pipe.dimensions.wall_thickness * 1.05],
                     fixedrange=True, **sp2_placement)

    fig.update_layout(showlegend=False)
    if orientation == 'vertical':
        fig.update_layout(width=400, height=800)
    elif orientation == 'horizontal':
        fig.update_layout(width=800, height=450)
    return fig


# generate a plotly dash table to display the pipe properties
def generate_pipe_properties_table(pipe: models.Pipe) -> go.Figure:
    """
    Generates a table to display the pipe properties
    Args:
        pipe: Pipe object

    Returns:
        fig: Figure
    """
    pipe_properties = pd.DataFrame(
        {
            'Property': [
                'Outside Diameter',
                'Wall Thickness',
                'Material SMTS',
                'Material SMYS',
                'Defect Length',
                'Defect Depth',
                'Defect Relative Depth'
            ],
            'Value': [
                pipe.dimensions.outside_diameter,
                pipe.dimensions.wall_thickness,
                pipe.material_properties.smts,
                pipe.material_properties.smys,
                pipe.defect.length,
                pipe.defect.depth,
                pipe.defect.relative_depth]
        }
    )
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(pipe_properties.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[pipe_properties.Property, pipe_properties.Value],
                   fill_color='lavender',
                   align='left'))
    ])
    # fig.update_layout(width=400, height=200, showlegend=False)
    return fig
