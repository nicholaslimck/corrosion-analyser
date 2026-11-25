"""The adequacy chart must label the defect pressure in the displayed unit.

The shipped code passed the raw model value (megapascals) straight into the
marker label, so a screen denominated in bar showed 17.17 beside a verdict
reading 171.72 bar. These tests pin the label to the formatted value.
"""
import pytest

from src.utils.assessment import assess
from src.utils.graphing.defect_plots import generate_defect_depth_plot
from src.utils.units import format_pressure
from tests.unittests.test_assessment import pipe_data


@pytest.fixture
def pipe():
    return assess(pipe_data())


def marker_text(fig) -> str:
    return fig['data'][-1]['text'][0]


@pytest.mark.parametrize('unit', ['bar', 'MPa', 'psi'])
def test_marker_label_is_formatted_in_the_displayed_unit(pipe, unit):
    fig = generate_defect_depth_plot(pipe, pressure_unit=unit)
    resistance = pipe.assessment_defects[0].pressure_resistance
    assert marker_text(fig) == format_pressure(resistance, unit)
    assert unit in marker_text(fig)


def test_bar_label_is_ten_times_the_megapascal_label(pipe):
    # 1 MPa = 10 bar. If the unit argument were ignored, these would be equal.
    bar = float(marker_text(generate_defect_depth_plot(pipe, pressure_unit='bar')).split()[0])
    mpa = float(marker_text(generate_defect_depth_plot(pipe, pressure_unit='MPa')).split()[0])
    assert bar == pytest.approx(mpa * 10, rel=1e-2)
