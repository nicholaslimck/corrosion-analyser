"""
Tests for the analysis page's callbacks.

The callback functions are plain functions once the decorator has registered them, so
they can be called directly: this covers the interface glue that the unit tests above
it cannot reach, including the arity of the multi-output return.
"""
import json

import pytest

import src.app  # noqa: F401 - instantiates the Dash app so page callbacks can register
from src.pages.defect_analysis import (
    calculate_pipe_characteristics, download_json, download_markdown, update_input_units)
from tests.unittests.test_assessment import _input, pipe_data


def callback_args(data, clicks=1, theme='dark'):
    """Flatten the interface inputs into the callback's positional arguments."""
    value = lambda key: data[key]['Value']          # noqa: E731
    unit = lambda key: data[key]['Unit']            # noqa: E731
    return (
        clicks,
        value('Safety Class'),
        value('Sizing Accuracy Type'),
        value('Pipe Outer Diameter'), value('Pipe Wall Thickness'), value('SMTS'),
        value('Defect Length'), value('Defect Width'), value('Defect Depth'),
        unit('Defect Depth'),
        value('Defect Elevation'), value('Design Pressure'), value('Design Temperature'),
        value('Incidental to Design Pressure Ratio'),
        value('Accuracy'), value('Confidence Level'),
        value('Seawater Density'), value('Containment Density'), value('Elevation Reference'),
        value('Axial Stress'), value('Bending Stress'), value('Combined Stress'),
        value('Secondary Defect Length'), value('Secondary Defect Width'),
        value('Secondary Defect Depth'), unit('Secondary Defect Depth'),
        value('Secondary Defect Separation'),
        value('First Date'), value('Second Date'),
        theme,
    )


class TestAnalyseCallback:
    def test_returns_eight_outputs_with_a_report(self):
        result = calculate_pipe_characteristics(*callback_args(pipe_data()))
        assert len(result) == 8
        fig_depth, fig_pipe, fig_defect, analysis, evaluation, error_open, error, report = result

        assert fig_depth is not None and fig_pipe is not None and fig_defect is not None
        assert analysis is not None and evaluation is not None
        assert error_open is False and error == ''
        assert report is not None
        assert report['verdict']['acceptable'] is True
        assert report['results']['pressure_resistance_mpa'] == pytest.approx(17.172, abs=1e-3)

    def test_reports_the_interaction_when_defects_combine(self):
        result = calculate_pipe_characteristics(*callback_args(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Width': _input(50, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'Secondary Defect Separation': _input(100, 'mm'),
        })))
        report = result[-1]
        assert report['defects'][-1]['combined'] is True

    def test_validation_error_surfaces_in_the_modal_and_no_report(self):
        data = pipe_data(**{'SMTS': _input(None, 'MPa')})
        result = calculate_pipe_characteristics(*callback_args(data))
        error_open, error, report = result[5], result[6], result[7]

        assert error_open is True
        assert 'SMTS' in error
        assert report is not None  # no_update sentinel, not a report dict
        assert not isinstance(report, dict)


class TestDownloadCallbacks:
    def test_markdown_download(self):
        report = calculate_pipe_characteristics(*callback_args(pipe_data()))[-1]
        payload = download_markdown(1, report)
        assert payload['filename'].startswith('corrosion-assessment-')
        assert payload['filename'].endswith('.md')
        assert '# Pipeline Corrosion Assessment' in payload['content']

    def test_json_download_is_valid_json(self):
        report = calculate_pipe_characteristics(*callback_args(pipe_data()))[-1]
        payload = download_json(1, report)
        assert payload['filename'].endswith('.json')
        parsed = json.loads(payload['content'])
        assert parsed['verdict']['acceptable'] is True

    def test_downloads_do_nothing_without_a_report(self):
        # no_update is the sentinel that leaves the browser alone
        for download in (download_markdown, download_json):
            assert download(1, None) is not None
            assert not isinstance(download(1, None), dict)


class TestUnitCallback:
    @pytest.mark.parametrize('depth_unit,accuracy_type,expected', [
        ('relative', 'relative', ('t', 't', '')),
        ('relative', 'absolute', ('t', 't', 'mm')),
        ('absolute', 'relative', ('mm', 'mm', '')),
        ('absolute', 'absolute', ('mm', 'mm', 'mm')),
    ])
    def test_depth_and_accuracy_units_are_independent(self, depth_unit, accuracy_type, expected):
        assert update_input_units(depth_unit, accuracy_type) == expected
