import pytest

from src.utils.assessment import assess
from src.utils.layout import build_evaluation_alert, build_result_items
from tests.unittests.test_assessment import _input, pipe_data


@pytest.fixture
def pipe():
    return assess(pipe_data())


def rendered(component) -> str:
    return str(component)


class TestResultItems:
    @pytest.mark.parametrize('unit,needle', [('bar', 'bar'), ('MPa', 'MPa'), ('psi', 'psi')])
    def test_pressures_follow_the_selected_unit(self, pipe, unit, needle):
        items = build_result_items(pipe, unit)
        text = rendered(items)
        assert needle in text

    def test_reports_both_pressures(self, pipe):
        text = rendered(build_result_items(pipe, 'bar'))
        assert 'Effective Pressure' in text
        assert 'Pressure Resistance' in text
        assert '171.72 bar' in text      # 17.172 MPa
        assert '157.50 bar' in text      # 15.750 MPa

    def test_remaining_life_only_when_available(self, pipe):
        assert 'Remaining Life' not in rendered(build_result_items(pipe, 'bar'))

    def test_interaction_line_only_when_positions_are_given(self, pipe):
        assert 'Interaction' not in rendered(build_result_items(pipe, 'bar'))
        interacting = assess(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Width': _input(50, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'Secondary Defect Separation': _input(100, 'mm'),
        }))
        assert 'Defect interaction found' in rendered(build_result_items(interacting, 'bar'))


class TestEvaluationAlert:
    def test_quotes_the_selected_unit(self):
        alert = build_evaluation_alert(15.75, 17.172, 'MPa')
        text = rendered(alert)
        assert '17.17 MPa' in text
        assert '15.75 MPa' in text
        assert 'Corrosion is acceptable' in text

    def test_compares_in_the_selected_unit_without_changing_the_verdict(self):
        # psi representation of the same pair: resistance still exceeds effective
        alert_bar = build_evaluation_alert(15.75, 17.172, 'bar')
        alert_psi = build_evaluation_alert(15.75, 17.172, 'psi')
        assert 'Corrosion is acceptable' in rendered(alert_bar)
        assert 'Corrosion is acceptable' in rendered(alert_psi)

    def test_unacceptable_pair(self):
        alert = build_evaluation_alert(14.25, 3.48, 'bar')
        text = rendered(alert)
        assert 'Corrosion is unacceptable' in text
        assert '>' in text
