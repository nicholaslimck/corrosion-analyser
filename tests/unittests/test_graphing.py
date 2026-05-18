import pytest
import plotly.graph_objects as go

from src.utils.graphing.defect_plots import generate_defect_depth_plot
from src.utils.graphing.pipe_plots import generate_pipe_cross_section_plot, generate_defect_cross_section_plot
from src.utils.graphing.theme import get_palette, apply_theme
from src.utils.models.pipe import Pipe, PipeConfig
from src.utils.models.defect import Defect
from src.utils.models.environment import Environment


_BASE_CONFIG = PipeConfig(
    outside_diameter=812.8,
    wall_thickness=19.1,
    smts=530.9,
    design_pressure=150,
    design_temperature=75,
    incidental_to_design_pressure_ratio=1.1,
    accuracy=0.1,
    confidence_level=0.8,
    safety_class='medium',
    measurement_method='relative',
)


def _make_env():
    return Environment(seawater_density=1025, containment_density=200,
                       elevation_reference=0, elevation=-100)


@pytest.fixture
def configured_pipe():
    pipe = Pipe(config=_BASE_CONFIG)
    pipe.set_environment(_make_env())
    pipe.add_defect(Defect(length=200, relative_depth=0.25))
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


@pytest.fixture
def two_defect_pipe():
    """Two non-interacting defects — produces a 3-trace depth plot."""
    pipe = Pipe(config=_BASE_CONFIG)
    pipe.set_environment(_make_env())
    # separation + lengths = 600 + 200 = 800 > 623 → no interaction
    pipe.add_defect(Defect(length=100, relative_depth=0.25, position=0))
    pipe.add_defect(Defect(length=100, relative_depth=0.30, position=600))
    pipe.calculate_pressure_resistance()
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()
    return pipe


@pytest.fixture
def interacting_pipe():
    """Two interacting defects — produces a 5-trace depth plot and combined defect."""
    pipe = Pipe(config=_BASE_CONFIG)
    pipe.set_environment(_make_env())
    # separation + lengths = 50 + 200 = 250 < 623 → interacting
    pipe.add_defect(Defect(length=100, relative_depth=0.25, position=0))
    pipe.add_defect(Defect(length=100, relative_depth=0.30, position=50))
    pipe.calculate_pressure_resistance()   # adds combined_defect → 3 defects
    pipe.calculate_effective_pressure()
    pipe.calculate_maximum_allowable_defect_depth()  # [d1, combined] → 2 DataFrames
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


# --- Multi-defect depth plots ---

def test_generate_defect_depth_plot_two_defects(two_defect_pipe):
    fig = generate_defect_depth_plot(two_defect_pipe)
    assert isinstance(fig, go.Figure)
    # 1 limit curve + 2 defect markers = 3 traces
    assert len(fig.data) == 3


def test_generate_defect_depth_plot_interacting_defects(interacting_pipe):
    fig = generate_defect_depth_plot(interacting_pipe)
    assert isinstance(fig, go.Figure)
    # 2 limit curves + 3 defect markers (d1, d2, combined) = 5 traces
    assert len(fig.data) == 5


# --- Multi-defect cross-section plots ---

def test_generate_defect_cross_section_plot_two_defects(two_defect_pipe):
    fig = generate_defect_cross_section_plot(two_defect_pipe)
    assert isinstance(fig, go.Figure)


def test_generate_defect_cross_section_plot_combined_defect(interacting_pipe):
    # 3 defects (d1, d2, combined): exercises "Combined Defect" label path
    fig = generate_defect_cross_section_plot(interacting_pipe)
    assert isinstance(fig, go.Figure)
