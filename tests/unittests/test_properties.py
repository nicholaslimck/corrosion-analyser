"""
Property based tests for the invariants the assessment equations must satisfy.

These complement the table driven tests: the tables pin individual values, these
assert the shape of the functions across their domain. Both of the calculation bugs
found during the compliance audit (a safety factor that fell to zero, and an inverse
that returned a root which did not satisfy its own equation) are violations of the
properties below rather than of any single tabulated value.
"""
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.utils.calculations.defect_calculations import (
    calculate_max_defect_depth_longitudinal_with_stress, calculate_maximum_defect_length)
from src.utils.calculations.pressure_calculations import (
    calculate_pressure_resistance_longitudinal_defect,
    calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
from src.utils.calculations.statistical_calculations import calculate_partial_safety_factors
from src.utils.models.factors import Factors

SETTINGS = settings(max_examples=60, deadline=None,
                    suppress_health_check=[HealthCheck.filter_too_much])

# DNV example geometry (A.1): D = 812.8 mm, t = 19.1 mm, SMTS 530.9
DIAMETER = 812.8
THICKNESS = 19.1
F_U = (530.9 - 15) * 0.96
GAMMA_M = 0.85
GAMMA_D = 1.28
EPSILON_D = 0.9616
STD = 0.078


@SETTINGS
@given(depth=st.floats(0.01, 0.50), increment=st.floats(0.001, 0.10))
def test_pressure_resistance_decreases_with_depth(depth, increment):
    """Deeper is weaker. Kept inside the range where gamma_d (d/t)* < 1, i.e. unclamped."""
    shallow = depth
    deep = depth + increment

    p_shallow = calculate_pressure_resistance_longitudinal_defect(
        GAMMA_M, GAMMA_D, THICKNESS, 200, DIAMETER, shallow + EPSILON_D * STD, F_U)
    p_deep = calculate_pressure_resistance_longitudinal_defect(
        GAMMA_M, GAMMA_D, THICKNESS, 200, DIAMETER, deep + EPSILON_D * STD, F_U)

    assert p_shallow > p_deep > 0


@SETTINGS
@given(length=st.floats(10, 2000), increment=st.floats(1, 1000))
def test_pressure_resistance_decreases_with_length(length, increment):
    """Longer is weaker at constant depth."""
    p_short = calculate_pressure_resistance_longitudinal_defect(
        GAMMA_M, GAMMA_D, THICKNESS, length, DIAMETER, 0.25, F_U)
    p_long = calculate_pressure_resistance_longitudinal_defect(
        GAMMA_M, GAMMA_D, THICKNESS, length + increment, DIAMETER, 0.25, F_U)

    assert p_short > p_long > 0


@SETTINGS
@given(depth=st.floats(0.15, 0.50), increment=st.floats(0.001, 0.10))
def test_maximum_allowable_length_decreases_with_depth(depth, increment):
    """Section 3.7.3.2: the allowable length curve must fall as depth rises."""
    def allowable(d):
        return calculate_maximum_defect_length(
            d=DIAMETER, t=THICKNESS, gamma_d=GAMMA_D, gamma_m=GAMMA_M, f_u=F_U,
            p_li=16.95, p_le=1.20, d_t_meas=d, epsilon_d=EPSILON_D, st_dev=STD)

    shallow = allowable(depth)
    deep = allowable(depth + increment)

    assert shallow is not None and deep is not None
    assert shallow > deep > 0


@SETTINGS
@given(accuracy=st.floats(0.0, 0.16),
       safety_class=st.sampled_from(['low', 'medium', 'high', 'very high']))
def test_safety_factors_are_never_unsafe(accuracy, safety_class):
    """gamma_d reduces capacity and must never fall below 1; epsilon_d adds uncertainty.

    The very high class previously returned gamma_d = 0.0 at exact sizing, which is
    neither of these.
    """
    factors = calculate_partial_safety_factors(safety_class, 'relative', accuracy)

    assert factors['gamma_d'] is not None
    assert factors['gamma_d'] >= 1.0
    assert factors['epsilon_d'] is not None
    assert factors['epsilon_d'] >= 0.0
    assert 0.0 < factors['gamma_m'] <= 1.0


@SETTINGS
@given(accuracy=st.floats(0.0, 0.16),
       safety_class=st.sampled_from(['low', 'medium', 'high', 'very high']))
def test_standard_deviation_is_monotonic_in_accuracy(accuracy, safety_class):
    """A sloppier inspection cannot yield a smaller standard deviation."""
    loose = Factors(safety_class=safety_class, inspection_method='relative',
                    measurement_accuracy=accuracy, confidence_level=0.8, wall_thickness=THICKNESS)
    tighter = Factors(safety_class=safety_class, inspection_method='relative',
                      measurement_accuracy=max(accuracy - 0.01, 0.0),
                      confidence_level=0.8, wall_thickness=THICKNESS)
    assert loose.standard_deviation >= tighter.standard_deviation


@SETTINGS
@given(target=st.floats(1.0, 18.0), sigma_l=st.floats(-400.0, -10.0),
       length=st.floats(50.0, 1000.0))
def test_compressive_inverse_satisfies_its_own_equation(target, sigma_l, length):
    """Substituting the returned depth back must reproduce the target resistance."""
    def resistance(depth):
        return calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
            gamma_m=GAMMA_M, gamma_d=GAMMA_D, t_nominal=THICKNESS, d_nominal=DIAMETER,
            defect_length=length, defect_width=100.0,
            defect_relative_depth_measured=depth,
            relative_defect_depth_with_uncertainty=depth + EPSILON_D * STD,
            f_u=F_U, sigma_l=sigma_l, phi=0.85)

    depth = calculate_max_defect_depth_longitudinal_with_stress(
        gamma_m=GAMMA_M, gamma_d=GAMMA_D, pipe_diameter=DIAMETER, pipe_thickness=THICKNESS,
        defect_length=length, defect_width=100.0, f_u=F_U, p_corr_comp=target,
        xi=0.85, sigma_l=sigma_l, epsilon_d=EPSILON_D, st_dev=STD)

    assert 0.0 <= depth <= 0.85
    if depth == 0.0:
        # No depth is tolerable: even an uncorroded pipe misses the target
        assert resistance(1e-9) <= target
    else:
        assert resistance(depth) == pytest.approx(target, rel=1e-6)
