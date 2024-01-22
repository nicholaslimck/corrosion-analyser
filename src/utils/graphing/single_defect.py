import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.utils import models


def generate_plot(pipe: models.Pipe) -> go.Figure:
    """
    Generates a plot to represent the pipe's current state, with a single defect represented as a point
    with the maximum allowable defect depth at each length represented as a line.
    Args:
        pipe: Pipe object

    Returns:
        fig: Figure
    """
    limits = pipe.calculate_acceptable_limits()

    # Plot figure
    fig = px.line(limits, x='defect_length', y='defect_depth',
                  color_discrete_sequence=['red'],
                  labels={
                      'defect_length': 'Corrosion Defect Length (mm)',
                      'defect_depth': 'Allowable Measured Relative Depth (d/t)'
                  },
                  range_y=[0, 1.0])

    marker_df = pd.DataFrame({'defect_length': pipe.defect.length, 'defect_depth': pipe.defect.relative_depth},
                             index=[0])

    if pipe.properties.effective_pressure < pipe.properties.pressure_resistance:
        colour = 'blue'
    else:
        colour = 'red'

    marker = px.scatter(marker_df, x='defect_length', y='defect_depth', color_discrete_sequence=[colour])

    fig.add_trace(marker.data[0])

    fig['data'][0]['showlegend'] = True
    fig['data'][1]['showlegend'] = True
    fig['data'][0]['name'] = 'Calculated Limits'
    fig['data'][1]['name'] = 'Actual Dimensions'

    fig.update_layout(width=1000, height=800,
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


def generate_pipe_plot(pipe: models.Pipe) -> go.Figure:
    """
    Generates a pair of plots as cross-sectional representations of the pipe and defect.
    Args:
        pipe: Pipe object

    Returns:
        fig: Figure
    """
    pipe_outer_diameter = pipe.dimensions.outside_diameter
    pipe_inner_diameter = pipe.dimensions.outside_diameter - 2 * pipe.dimensions.wall_thickness
    fig = go.Figure()
    fig = make_subplots(rows=2, cols=1)

    # Set up pipe cross-section plot
    fig.add_trace(go.Scatter(
        x=[0, 0, 0],
        y=[pipe_outer_diameter / 2, pipe_outer_diameter / 2.4, pipe_outer_diameter / 3],
        text=[f"Outer Diameter: {pipe_outer_diameter:.2f}",
              f"Wall Thickness: {pipe.dimensions.wall_thickness:.2f}",
              f"Inner Diameter: {pipe_inner_diameter:.2f}"],
        mode="text"),
        row=1, col=1
    )
    fig.add_shape(type="circle",
                  xref="x", yref="y",
                  x0=-pipe_outer_diameter / 2, y0=-pipe_outer_diameter / 2,
                  x1=pipe_outer_diameter / 2, y1=pipe_outer_diameter / 2,
                  line_color="LightSeaGreen", row=1, col=1
                  )
    fig.add_shape(type="circle",
                  xref="x", yref="y",
                  x0=-pipe_inner_diameter / 2, y0=-pipe_inner_diameter / 2,
                  x1=pipe_inner_diameter / 2, y1=pipe_inner_diameter / 2,
                  line_color="LightSeaGreen", row=1, col=1
                  )

    fig.update_xaxes(range=[-pipe_outer_diameter / 2 * 1.05, pipe_outer_diameter / 2 * 1.05],
                     zeroline=False, fixedrange=True, row=1, col=1)
    fig.update_yaxes(range=[-pipe_outer_diameter / 2 * 1.05, pipe_outer_diameter / 2 * 1.05],
                     zeroline=False, fixedrange=True, row=1, col=1)

    # Set up defect cross-section subplot
    fig.add_shape(type="rect",
                  fillcolor="LightSeaGreen",
                  xref="x", yref="y",
                  x0=-10, y0=0,
                  x1=pipe.defect.length * 2.05, y1=pipe.dimensions.wall_thickness,
                  label=dict(text=f"Wall Thickness: {pipe.dimensions.wall_thickness}"),
                  # opacity=0.5,
                  row=2, col=1)
    fig.add_shape(type="rect",
                  fillcolor="LightSalmon",
                  xref="x", yref="y",
                  x0=pipe.defect.length * 0.5, y0=pipe.dimensions.wall_thickness - pipe.defect.depth,
                  x1=pipe.defect.length * 1.5, y1=pipe.dimensions.wall_thickness,
                  opacity=0.6,
                  label=dict(text=f"Defect Depth: {pipe.defect.depth}"),
                  row=2, col=1)
    fig.update_xaxes(range=[0, pipe.defect.length * 2], fixedrange=True, row=2, col=1)
    fig.update_yaxes(range=[-pipe.dimensions.wall_thickness * 0.05, pipe.dimensions.wall_thickness * 1.05],
                     fixedrange=True, row=2, col=1)

    fig.update_layout(width=400, height=800, showlegend=False)
    return fig
