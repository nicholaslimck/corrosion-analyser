"""Chart labels must use theme colours, not the fill colour they sit on.

The defect depth label was drawn in DEFECT_COLOR (#E53E3E) over a tinted fill of
the same hue, which measured 2.63:1 in dark and 2.62:1 in light.
"""
import pytest

from src.utils.assessment import assess
from src.utils.graphing.pipe_plots import generate_defect_cross_section_plot
from src.utils.graphing.theme import get_palette
from tests.unittests.test_assessment import pipe_data


@pytest.fixture
def pipe():
    return assess(pipe_data())


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_the_defect_label_uses_the_theme_label_colour(pipe, theme):
    figure = generate_defect_cross_section_plot(pipe, theme=theme)
    colours = [annotation.font.color for annotation in figure.layout.annotations
               if annotation.font and annotation.font.color]
    assert get_palette(theme)['defect_text_color'] in colours


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_the_defect_label_is_not_the_fill_colour(pipe, theme):
    figure = generate_defect_cross_section_plot(pipe, theme=theme)
    colours = [annotation.font.color for annotation in figure.layout.annotations
               if annotation.font and annotation.font.color]
    assert '#E53E3E' not in colours
