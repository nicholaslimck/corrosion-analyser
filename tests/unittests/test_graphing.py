import pytest
import plotly.graph_objects as go

from src.utils.graphing.defect_plots import generate_defect_depth_plot
from src.utils.graphing.pipe_plots import generate_pipe_cross_section_plot, generate_defect_cross_section_plot
from src.utils.graphing.theme import get_palette, apply_theme
from src.utils.models.pipe import Pipe
from src.utils.models.defect import Defect
from src.utils.models.environment import Environment


@pytest.fixture
def configured_pipe():
    config = {
        'outside_diameter': 812.8,
        'wall_thickness': 19.1,
        'smts': 530.9,
        'design_pressure': 150,
        'design_temperature': 75,
        'incidental_to_design_pressure_ratio': 1.1,
        'accuracy': 0.1,
        'confidence_level': 0.8,
        'safety_class': 'medium',
        'measurement_method': 'relative',
    }
    pipe = Pipe(config=config)
    env = Environment(seawater_density=1025, containment_density=200,
                      elevation_reference=0, elevation=-100)
    pipe.set_environment(env)
    pipe.add_defect(Defect(length=200, relative_depth=0.25))
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


# --- Pipe cross-section plot ---

def test_generate_pipe_cross_section_plot_returns_figure(configured_pipe):
    fig = generate_pipe_cross_section_plot(configured_pipe)
    assert isinstance(fig, go.Figure)


def test_generate_pipe_cross_section_plot_light_theme(configured_pipe):
    fig = generate_pipe_cross_section_plot(configured_pipe, theme='light')
    assert isinstance(fig, go.Figure)


# --- Defect cross-section plot ---

def test_generate_defect_cross_section_plot_returns_figure(configured_pipe):
    fig = generate_defect_cross_section_plot(configured_pipe)
    assert isinstance(fig, go.Figure)


# --- Defect depth plot ---

def test_generate_defect_depth_plot_returns_figure(configured_pipe):
    fig = generate_defect_depth_plot(configured_pipe)
    assert isinstance(fig, go.Figure)


def test_generate_defect_depth_plot_light_theme(configured_pipe):
    fig = generate_defect_depth_plot(configured_pipe, theme='light')
    assert isinstance(fig, go.Figure)


# --- Theme utilities ---

def test_get_palette_dark():
    palette = get_palette('dark')
    assert isinstance(palette, dict)
    assert 'plot_bgcolor' in palette
    assert 'font_color' in palette


def test_get_palette_light():
    palette = get_palette('light')
    assert isinstance(palette, dict)
    assert 'plot_bgcolor' in palette


def test_get_palette_unknown_returns_dark():
    palette = get_palette('nonexistent')
    dark = get_palette('dark')
    assert palette == dark


def test_apply_theme_returns_figure():
    fig = go.Figure()
    result = apply_theme(fig, theme='dark')
    assert isinstance(result, go.Figure)
