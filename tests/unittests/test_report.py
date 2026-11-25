import datetime
import json

import pytest

from src.utils.assessment import assess
from src.utils.report import STANDARD, build_report, filename, render_markdown
from tests.unittests.test_assessment import _input, pipe_data

GENERATED_AT = datetime.datetime(2026, 11, 22, 9, 30, 0)


@pytest.fixture
def report():
    return build_report(assess(pipe_data()), generated_at=GENERATED_AT)


class TestBuildReport:
    def test_identifies_the_standard(self, report):
        assert report['standard'] == STANDARD
        assert '2019' in report['standard']

    def test_verdict_and_margin(self, report):
        # DNV example geometry: resistance 17.17 MPa against an effective pressure of 15.75
        assert report['verdict']['acceptable'] is True
        assert report['verdict']['pressure_margin_mpa'] == pytest.approx(1.42, abs=0.01)

    def test_results_are_quoted_in_mpa_and_bar(self, report):
        assert report['results']['pressure_resistance_mpa'] == pytest.approx(17.172, abs=1e-3)
        assert report['results']['pressure_resistance_bar'] == pytest.approx(171.72, abs=1e-2)
        assert report['results']['effective_pressure_mpa'] == pytest.approx(15.75, abs=1e-3)

    def test_records_the_safety_factors_used(self, report):
        assessment = report['assessment']
        assert assessment['safety_class'] == 'medium'
        assert assessment['gamma_m'] == pytest.approx(0.85)
        assert assessment['gamma_d'] == pytest.approx(1.2743, abs=1e-3)
        assert assessment['standard_deviation'] == pytest.approx(0.078, abs=1e-3)

    def test_records_the_material_and_de_rating(self, report):
        assert report['material']['smts_mpa'] == pytest.approx(530.9)
        assert report['material']['de_rating_mpa'] == pytest.approx(15.0)
        assert report['material']['f_u_mpa'] == pytest.approx(495.264, abs=1e-3)

    def test_is_json_serialisable(self, report):
        """The calculation layer returns numpy scalars, which json cannot encode."""
        encoded = json.dumps(report)
        assert json.loads(encoded)['verdict']['acceptable'] is True

    def test_includes_the_allowable_depth_curve(self, report):
        curves = report['allowable_depth_curves']
        assert len(curves) == 1
        assert curves[0]['label'] == 'measured'
        assert len(curves[0]['points']) > 100
        length, depth = curves[0]['points'][0]
        assert isinstance(length, float) and isinstance(depth, float)

    def test_curve_can_be_omitted(self):
        report = build_report(assess(pipe_data()), generated_at=GENERATED_AT, include_curve=False)
        assert report['allowable_depth_curves'] == []

    def test_unacceptable_assessment(self):
        """DNV Example 3 geometry: resistance 34.8 bar against 142.5 bar."""
        report = build_report(
            assess(pipe_data(**{
                'Pipe Outer Diameter': _input(219.0, 'mm'),
                'Pipe Wall Thickness': _input(14.5, 'mm'),
                'SMTS': _input(455.1, 'MPa'),
                'Defect Width': _input(100, 'mm'),
                'Defect Depth': _input(0.62, 't'),
                'Design Temperature': _input(100, 'C'),
                'Incidental to Design Pressure Ratio': _input(1.0),
                'Combined Stress': _input(200, 'MPa'),
            })),
            generated_at=GENERATED_AT)
        assert report['verdict']['acceptable'] is False
        assert report['verdict']['pressure_margin_mpa'] < 0

    def test_records_corrosion_rate_and_remaining_life(self):
        report = build_report(
            assess(pipe_data(**{
                'Defect Length': _input(210, 'mm'),
                'Defect Depth': _input(0.26, 't'),
                'Secondary Defect Length': _input(200, 'mm'),
                'Secondary Defect Depth': _input(0.25, 't'),
                'First Date': _input('2025-01-01', 'date'),
                'Second Date': _input('2024-01-01', 'date'),
            })),
            generated_at=GENERATED_AT)
        assert report['results']['corrosion_rate_per_day'] > 0
        assert report['results']['corrosion_rate_length_per_day'] > 0
        assert report['results']['remaining_life_days'] > 0

    def test_interacting_defects_report_a_combined_entry(self):
        report = build_report(
            assess(pipe_data(**{
                'Secondary Defect Length': _input(150, 'mm'),
                'Secondary Defect Width': _input(50, 'mm'),
                'Secondary Defect Depth': _input(0.30, 't'),
                'Secondary Defect Separation': _input(100, 'mm'),
            })),
            generated_at=GENERATED_AT)
        assert len(report['defects']) == 3
        assert report['defects'][-1]['combined'] is True
        assert len(report['allowable_depth_curves']) == 2
        assert report['allowable_depth_curves'][1]['label'] == 'combined'


class TestRenderMarkdown:
    def test_headings_and_verdict(self, report):
        markdown = render_markdown(report)
        assert markdown.startswith('# Pipeline Corrosion Assessment')
        assert STANDARD in markdown
        assert 'Acceptable.' in markdown
        assert '## Partial' not in markdown  # sections are geometry, parameters, defects, results

    def test_quotes_the_key_numbers(self, report):
        markdown = render_markdown(report)
        assert '17.172 MPa' in markdown
        assert '171.72 bar' in markdown
        assert '15.749 MPa' in markdown
        assert '1.2743' in markdown          # gamma_d actually used
        assert '0.0780' in markdown          # StD actually used

    def test_tables_are_pipe_tables(self, report):
        markdown = render_markdown(report)
        assert '| Parameter | Value | Clause |' in markdown
        assert '|------|-------|' in markdown
        assert '| Quantity | Value |' in markdown

    def test_states_when_not_acceptable(self):
        report = build_report(
            assess(pipe_data(**{
                'Pipe Outer Diameter': _input(219.0, 'mm'),
                'Pipe Wall Thickness': _input(14.5, 'mm'),
                'SMTS': _input(455.1, 'MPa'),
                'Defect Width': _input(100, 'mm'),
                'Defect Depth': _input(0.62, 't'),
                'Design Temperature': _input(100, 'C'),
                'Incidental to Design Pressure Ratio': _input(1.0),
                'Combined Stress': _input(200, 'MPa'),
            })),
            generated_at=GENERATED_AT)
        assert 'NOT acceptable' in render_markdown(report)


class TestFilename:
    def test_is_stamped_and_sortable(self, report):
        assert filename(report, 'json') == 'corrosion-assessment-20261122T0930.json'
        assert filename(report, '.md') == 'corrosion-assessment-20261122T0930.md'
