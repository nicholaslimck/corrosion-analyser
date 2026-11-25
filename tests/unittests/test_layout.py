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

    def test_quantifies_utilisation_and_margin(self):
        text = rendered(build_evaluation_alert(15.75, 17.172, 'bar'))
        assert '91.7% of capacity' in text
        assert 'Margin: 14.22 bar' in text

    def test_margin_follows_the_selected_unit(self):
        assert 'Margin: 1.42 MPa' in rendered(build_evaluation_alert(15.75, 17.172, 'MPa'))

    def test_names_the_governing_clause_when_factors_are_supplied(self):
        text = rendered(build_evaluation_alert(15.75, 17.172, 'bar',
                                               safety_class='medium', design_factor=0.96))
        assert 'DNVGL-RP-F101' in text
        assert 'Safety Class Medium' in text
        assert 'γm = 0.96' in text

    def test_omits_the_clause_when_factors_are_not_supplied(self):
        # The three-argument call sites still work and stay clause-free.
        assert 'Safety Class' not in rendered(build_evaluation_alert(15.75, 17.172, 'bar'))

    def test_rejection_names_the_next_steps(self):
        text = rendered(build_evaluation_alert(14.25, 3.48, 'bar'))
        assert 'Reduce the operating pressure below' in text
        assert 'Re-inspect the defect' in text
        assert 'Repair or replace' in text

    def test_outcome_is_not_carried_by_colour_alone(self):
        assert '✔' in rendered(build_evaluation_alert(15.75, 17.172, 'bar'))
        assert '✖' in rendered(build_evaluation_alert(14.25, 3.48, 'bar'))

    def test_zero_resistance_does_not_advise_a_zero_pressure_target(self):
        # A defect outside the acceptance limits has no pressure lever.
        text = rendered(build_evaluation_alert(157.5, 0.0, 'bar'))
        assert 'outside the RP-F101 acceptance limits' in text
        assert 'below 0.00 bar' not in text

    def test_capacity_is_a_labelled_range_not_a_percentage_bar(self):
        # A fill-to-100% bar reads "nearly finished"; full here means "at the
        # limit", so both ends of the range are labelled and the Bootstrap
        # progress bar is gone.
        text = rendered(build_evaluation_alert(15.75, 17.172, 'bar'))
        assert 'capacity-track' in text
        assert 'capacity-scale' in text
        assert '171.72 bar limit' in text
        assert 'progress-bar' not in text
        assert '91.7% of capacity' in text


class TestVerdictEdgeCases:
    """The verdict card is what a reviewer reads to accept or reject a pipeline."""

    def test_tiny_positive_resistance_does_not_advise_a_zero_target(self):
        from src.utils.layout import build_evaluation_alert

        # 1e-05 MPa is positive but renders as 0.00 bar, so "reduce the pressure
        # below 0.00 bar" would be unactionable nonsense.
        rendered = str(build_evaluation_alert(157.5, 1e-05, 'bar'))
        assert 'below 0.00' not in rendered
        assert 'outside the RP-F101 acceptance limits' in rendered

    def test_clause_cites_the_partial_safety_factor_clause(self):
        from src.utils.layout import build_evaluation_alert

        rendered = str(build_evaluation_alert(10.0, 20.0, 'bar',
                                              safety_class='medium',
                                              design_factor=0.85))
        assert '§3.3' in rendered
        assert 'Table 3-2' in rendered
        assert '§2.3' not in rendered

    def test_absurd_utilisation_is_not_printed_as_a_ratio(self):
        from src.utils.layout import build_evaluation_alert

        rendered = str(build_evaluation_alert(157.5, 1e-05, 'bar'))
        assert '1575000000' not in rendered
        assert 'over 999% of capacity' in rendered
