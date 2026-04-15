import pandas as pd
import plotly.graph_objects as go

from src.utils import models

PIPE_COLOR = "#2C7A7B"
DEFECT_COLOR = "#E53E3E"


def generate_pipe_cross_section_plot(pipe: models.Pipe, figure_width: int = 400) -> go.Figure:
    """
    Generates a plot to represent the pipe's cross-section.
    Args:
        pipe: Pipe object
        figure_width: Width of the figure

    Returns:
        fig: Figure
    """
    outer_diameter = pipe.dimensions.outside_diameter
    inner_diameter = pipe.dimensions.outside_diameter - 2 * pipe.dimensions.wall_thickness
    thickness = pipe.dimensions.wall_thickness

    fig = go.Figure()
    # Set up pipe cross-section plot
    fig.add_trace(go.Scatter(
        x=[0, 0, 0],
        y=[outer_diameter / 2, outer_diameter / 2.4, outer_diameter / 3],
        text=[f"Outer Diameter: {outer_diameter:.2f}",
              f"Wall Thickness: {thickness:.2f}",
              f"Inner Diameter: {inner_diameter:.2f}"],
        mode="text"),
    )
    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-outer_diameter / 2, y0=-outer_diameter / 2,
        x1=outer_diameter / 2, y1=outer_diameter / 2,
        line_color=PIPE_COLOR
    )
    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-inner_diameter / 2, y0=-inner_diameter / 2,
        x1=inner_diameter / 2, y1=inner_diameter / 2,
        line_color=PIPE_COLOR
    )

    fig.update_xaxes(range=[-outer_diameter / 2 * 1.05, outer_diameter / 2 * 1.05],
                     zeroline=False, showticklabels=False)
    fig.update_yaxes(range=[-outer_diameter / 2 * 1.05, outer_diameter / 2 * 1.05],
                     zeroline=False, scaleanchor="x", scaleratio=1, autorange=True,
                     showticklabels=False)

    fig.update_layout(title_text="Pipe Cross-Section", title_x=0.5)

    return fig


def generate_defect_cross_section_plot(pipe: models.Pipe, figure_width: int = 400) -> go.Figure:
    """
    Generates a plot to represent the pipe's cross-section with a defect.
    Args:
        pipe: Pipe object
        figure_width: Width of the figure

    Returns:
        fig: Figure
    """
    thickness = pipe.dimensions.wall_thickness
    longest_defect = max([defect.length for defect in pipe.defects])  # noqa: F841
    if len(pipe.defects) > 1:
        position_range = pipe.defects[0].length + pipe.defects[1].length + pipe.defects[0].position + pipe.defects[1].position
    else:
        position_range = pipe.defects[0].length

    fig = go.Figure()
    # Create pipe shape
    fig.add_shape(
        type="rect",
        fillcolor=PIPE_COLOR,
        xref="x", yref="y",
        x0=-10, y0=0,
        x1=position_range * 2.05, y1=thickness,
        label=dict(text=f"Wall Thickness: {thickness:.2f}", font=dict(color="White"))
    )
    # Add defect shapes
    for index, defect in enumerate(pipe.defects):
        # Configure position
        if index == 1:
            x0 = position_range * 0.5 + pipe.defects[0].length + defect.position
        else:
            x0 = position_range * 0.5

        # Configure opacity
        if index == 2:
            opacity = 0.3
        else:
            opacity = 0.6

        # Configure name
        if len(pipe.defects) == 1:
            name = "Measured Defect"
        else:
            if index != 2:
                name = f"Measured Defect {index+1}"
            else:
                name = "Combined Defect"

        fig.add_shape(
            type="rect",
            fillcolor=DEFECT_COLOR,
            xref="x", yref="y",
            x0=x0, y0=pipe.dimensions.wall_thickness - defect.depth,
            x1=x0 + defect.length, y1=pipe.dimensions.wall_thickness,
            opacity=opacity,
            label=dict(text=f"Defect Depth: {defect.depth:.2f}", font=dict(color="White")),
            name=name,
            showlegend=True if len(pipe.defects) > 1 else False
        )
    fig.update_xaxes(range=[0, position_range * 2], showticklabels=False)
    fig.update_yaxes(range=[-pipe.dimensions.wall_thickness * 0.05, pipe.dimensions.wall_thickness * 1.05])

    fig.update_layout(title_text="Defect Cross-Section", title_x=0.5)

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
