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
    build_calculation_trace, calculate_pipe_characteristics, download_json, download_markdown,
    update_calculation_trace, update_input_units)
from tests.unittests.test_assessment import _input, pipe_data


def callback_args(data, clicks=1, theme='dark', pressure_unit='bar'):
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
        pressure_unit,
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


class TestCalculationTrace:
    def test_trace_lists_the_factors_with_their_clauses(self):
        report = calculate_pipe_characteristics(*callback_args(pipe_data()))[-1]
        trace = build_calculation_trace(report, 'MPa')

        assert len(trace.children) == 2
        rendered = str(trace)
        # the factors actually used, not just their names
        assert f"{report['assessment']['gamma_d']:.4f}" in rendered
        assert f"{report['results']['pressure_resistance_mpa']:.3f}" in rendered
        # each with the clause it comes from
        for clause in ('Table 3-2', 'Tables 3-7, 3-8', 'Table 3-10', 'Tables 3-3 to 3-6', '§3.7.3.1'):
            assert clause in rendered

    def test_trace_includes_each_defect(self):
        report = calculate_pipe_characteristics(*callback_args(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Width': _input(50, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'Secondary Defect Separation': _input(100, 'mm'),
        })))[-1]
        rendered = str(build_calculation_trace(report, 'MPa'))
        assert 'Defect 1 (measured)' in rendered
        assert 'Defect 2 (measured)' in rendered
        assert 'Defect 3 (combined)' in rendered

    def test_trace_before_an_analysis_prompts_the_user(self):
        trace = update_calculation_trace(None)
        assert 'Run an analysis' in str(trace)


class TestUnitConversion:
    """Changing the pressure unit must convert the entry, not re-read it.

    Reinterpreting the number silently changed the physics of an untouched field:
    an assessment failing at 150 bar passed once the selector moved to psi.
    """

    def test_switching_unit_converts_the_entered_pressure(self):
        from src.pages.defect_analysis import convert_design_pressure
        from src.utils.units import PSI_PER_BAR

        value, unit = convert_design_pressure('psi', 'bar', 150.0)
        assert unit == 'psi'
        assert value == pytest.approx(150.0 * PSI_PER_BAR, abs=0.01)

    def test_round_trip_restores_the_original_pressure(self):
        from src.pages.defect_analysis import convert_design_pressure

        to_psi, _ = convert_design_pressure('psi', 'bar', 150.0)
        back_to_bar, unit = convert_design_pressure('bar', 'psi', to_psi)
        assert unit == 'bar'
        assert back_to_bar == pytest.approx(150.0, rel=1e-5)

    def test_same_unit_keeps_the_entered_value(self):
        from dash import no_update
        from src.pages.defect_analysis import convert_design_pressure

        value, unit = convert_design_pressure('bar', 'bar', 150.0)
        assert value is no_update
        assert unit == 'bar'
