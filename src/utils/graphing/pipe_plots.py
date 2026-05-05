import math

import plotly.graph_objects as go

from src.utils import models
from src.utils.graphing.theme import apply_theme, get_palette

PIPE_COLOR = "#2C7A7B"
DEFECT_COLOR = "#E53E3E"


def generate_pipe_cross_section_plot(pipe: models.Pipe, figure_width: int = 400, theme: str = 'dark') -> go.Figure:
    p = get_palette(theme)
    outer_diameter = pipe.dimensions.outside_diameter
    inner_diameter = pipe.dimensions.outside_diameter - 2 * pipe.dimensions.wall_thickness
    thickness = pipe.dimensions.wall_thickness
    r_outer = outer_diameter / 2
    r_inner = inner_diameter / 2

    fig = go.Figure()

    n_points = 100
    angles = [2 * math.pi * i / n_points for i in range(n_points + 1)]

    outer_x = [r_outer * math.cos(a) for a in angles]
    outer_y = [r_outer * math.sin(a) for a in angles]
    inner_x = [r_inner * math.cos(a) for a in reversed(angles)]
    inner_y = [r_inner * math.sin(a) for a in reversed(angles)]

    ring_x = outer_x + [None] + inner_x
    ring_y = outer_y + [None] + inner_y

    fig.add_trace(go.Scatter(
        x=ring_x, y=ring_y,
        fill="toself",
        fillcolor=PIPE_COLOR,
        line=dict(color=PIPE_COLOR, width=1),
        opacity=0.3,
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=outer_x, y=outer_y,
        mode="lines",
        line=dict(color=PIPE_COLOR, width=2),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=inner_x, y=inner_y,
        mode="lines",
        line=dict(color=PIPE_COLOR, width=2),
        hoverinfo="skip",
        showlegend=False,
    ))

    wall_mid = (r_outer + r_inner) / 2
    fig.add_annotation(x=0, y=r_outer * 1.12, text=f"OD: {outer_diameter:.1f} mm",
                       showarrow=False, font=dict(size=12, color=p['font_color']))
    fig.add_annotation(x=0, y=-r_outer * 1.12, text=f"ID: {inner_diameter:.1f} mm",
                       showarrow=False, font=dict(size=12, color=p['font_color']))
    fig.add_annotation(
        x=wall_mid * math.cos(math.pi / 4), y=wall_mid * math.sin(math.pi / 4),
        ax=40, ay=-30,
        text=f"t = {thickness:.1f} mm",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        font=dict(size=11, color=p['font_color']),
        arrowcolor=p['axis_color'],
    )

    fig.update_xaxes(range=[-r_outer * 1.25, r_outer * 1.25],
                     zeroline=False, showticklabels=False, showgrid=False, constrain="domain")
    fig.update_yaxes(range=[-r_outer * 1.25, r_outer * 1.25],
                     zeroline=False, scaleanchor="x", scaleratio=1,
                     showticklabels=False, showgrid=False, constrain="domain")

    fig.update_layout(title_text="Pipe Cross-Section", title_x=0.5,
                      margin=dict(l=20, r=20, t=40, b=20))
    return apply_theme(fig, theme)


def generate_defect_cross_section_plot(pipe: models.Pipe, figure_width: int = 400, theme: str = 'dark') -> go.Figure:
    p = get_palette(theme)
    thickness = pipe.dimensions.wall_thickness
    longest_defect = max([defect.length for defect in pipe.defects])  # noqa: F841
    if len(pipe.defects) > 1:
        position_range = (pipe.defects[0].length + pipe.defects[1].length
                          + pipe.defects[0].position + pipe.defects[1].position)
    else:
        position_range = pipe.defects[0].length

    fig = go.Figure()

    fig.add_shape(
        type="rect", fillcolor=PIPE_COLOR,
        xref="x", yref="y",
        x0=-10, y0=0, x1=position_range * 2.05, y1=thickness,
        opacity=0.3, line=dict(color=PIPE_COLOR, width=1),
    )

    for index, defect in enumerate(pipe.defects):
        x0 = (position_range * 0.5 + pipe.defects[0].length + defect.position
               if index == 1 else position_range * 0.5)
        opacity = 0.3 if index == 2 else 0.7
        if len(pipe.defects) == 1:
            name = "Measured Defect"
        elif index != 2:
            name = f"Measured Defect {index + 1}"
        else:
            name = "Combined Defect"

        fig.add_shape(
            type="rect", fillcolor=DEFECT_COLOR,
            xref="x", yref="y",
            x0=x0, y0=pipe.dimensions.wall_thickness - defect.depth,
            x1=x0 + defect.length, y1=pipe.dimensions.wall_thickness,
            opacity=opacity, line=dict(color=DEFECT_COLOR, width=1),
            name=name, showlegend=len(pipe.defects) > 1,
        )

    fig.add_annotation(
        x=position_range * 0.25, y=thickness / 2,
        text=f"t = {thickness:.1f} mm",
        showarrow=False, font=dict(size=11, color="white"),
    )

    for index, defect in enumerate(pipe.defects):
        x_pos = (position_range * 0.5 + pipe.defects[0].length + defect.position + defect.length
                 if index == 1 else position_range * 0.5 + defect.length)
        fig.add_annotation(
            x=x_pos, y=thickness - defect.depth / 2,
            text=f"{defect.depth:.1f} mm",
            showarrow=True, ax=35, ay=0,
            arrowhead=2, arrowwidth=1.5,
            font=dict(size=10, color=DEFECT_COLOR),
        )

    first_defect = pipe.defects[0]
    remaining = thickness - first_defect.depth
    x_mid = position_range * 0.5 + first_defect.length / 2
    fig.add_annotation(
        x=x_mid, y=remaining / 2,
        text=f"Remaining: {remaining:.1f} mm",
        showarrow=False, font=dict(size=10, color="white"),
    )

    fig.update_xaxes(range=[-position_range * 0.3, position_range * 2],
                     showticklabels=False, showgrid=False)
    fig.update_yaxes(range=[-thickness * 0.1, thickness * 1.15],
                     showticklabels=False, showgrid=False)

    fig.update_layout(title_text="Defect Cross-Section", title_x=0.5,
                      margin=dict(l=20, r=20, t=40, b=20))
    return apply_theme(fig, theme)
