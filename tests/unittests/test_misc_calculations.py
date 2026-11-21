import pytest

from src.utils.calculations.statistical_calculations import (calculate_std_dev,
                                                             calculate_partial_safety_factors,
                                                             calculate_inv_cumulative_dist,
                                                             calculate_usage_factors)


def test_calculate_std_dev(snapshot):
    acc = 0.1
    conf = 0.8
    measurement_method = 'relative'
    assert calculate_std_dev(acc=acc, conf=conf, measurement_method=measurement_method) == snapshot


@pytest.mark.parametrize('safety_class,inspection_method,inspection_accuracy', [
    ('low', 'relative', 0.00),
    ('medium', 'relative', 0.00),
    ('high', 'relative', 0.00),
    ('very high', 'relative', 0.00),
    ('very high', 'relative', 0.04),
    ('very high', 'relative', 0.08),
    ('low', 'relative', 0.16),
    ('medium', 'relative', 0.16),
    ('high', 'relative', 0.16),
    ('very high', 'relative', 0.16)
])
def test_calculate_partial_safety_factors(safety_class, inspection_method, inspection_accuracy, snapshot):

    assert snapshot == calculate_partial_safety_factors(safety_class, inspection_method, inspection_accuracy)


def test_calculate_inv_cumulative_dist_median():
    assert calculate_inv_cumulative_dist(0.5) == pytest.approx(0.0, abs=1e-10)


# DNVGL-RP-F101 Table 3-7 (p.33): calibrated gamma_d and epsilon_d per safety class
# and inspection sizing accuracy. The polynomial curve fits of Table 3-8 shall
# reproduce these values.
TABLE_3_7 = [
    # (safety_class, StD[d/t], gamma_d, epsilon_d)
    ('low', 0.00, 1.00, 0.0),
    ('medium', 0.00, 1.00, 0.0),
    ('high', 0.00, 1.00, 0.0),
    ('very high', 0.00, 1.00, 0.0),
    ('low', 0.04, 1.16, 0.0),
    ('medium', 0.04, 1.16, 0.0),
    ('high', 0.04, 1.16, 0.0),
    ('very high', 0.04, 1.19, 0.0),
    ('low', 0.08, 1.20, 1.0),
    ('medium', 0.08, 1.28, 1.0),
    ('high', 0.08, 1.32, 1.0),
    ('very high', 0.08, 1.43, 1.0),
    ('low', 0.16, 1.20, 2.0),
    ('medium', 0.16, 1.38, 2.0),
    ('high', 0.16, 1.58, 2.0),
    ('very high', 0.16, 1.84, 2.0),
]


@pytest.mark.parametrize('safety_class,accuracy,gamma_d,epsilon_d', TABLE_3_7)
def test_partial_safety_factors_match_table_3_7(safety_class, accuracy, gamma_d, epsilon_d):
    factors = calculate_partial_safety_factors(safety_class, 'relative', accuracy)
    assert factors['gamma_d'] == pytest.approx(gamma_d, abs=6e-3)
    assert factors['epsilon_d'] == pytest.approx(epsilon_d, abs=6e-3)


def test_very_high_safety_factor_never_below_unity():
    """gamma_d is a safety factor on depth: it must reduce, never amplify, capacity."""
    for accuracy in [0.0, 0.01, 0.02, 0.029, 0.03, 0.08, 0.16]:
        factors = calculate_partial_safety_factors('very high', 'relative', accuracy)
        assert factors['gamma_d'] is not None, f'gamma_d unset at StD={accuracy}'
        assert factors['gamma_d'] >= 1.0, f'gamma_d={factors["gamma_d"]} < 1.0 at StD={accuracy}'


def test_very_high_safety_factor_is_continuous():
    below = calculate_partial_safety_factors('very high', 'relative', 0.0299)['gamma_d']
    above = calculate_partial_safety_factors('very high', 'relative', 0.0300)['gamma_d']
    assert above - below == pytest.approx(0.0, abs=0.01)


def test_calculate_inv_cumulative_dist_95th_percentile():
    assert calculate_inv_cumulative_dist(0.975) == pytest.approx(1.96, abs=1e-2)


@pytest.mark.parametrize('safety_class,expected_xi', [
    ('low', 0.9),
    ('medium', 0.85),
    ('high', 0.8),
    ('very high', 0.75),
])
def test_calculate_usage_factors(safety_class, expected_xi):
    assert calculate_usage_factors(safety_class) == pytest.approx(expected_xi)


def test_calculate_usage_factors_invalid_raises():
    with pytest.raises(ValueError):
        calculate_usage_factors('extreme')


def test_calculate_std_dev_absolute():
    std_dev = calculate_std_dev(acc=1.0, conf=0.8, measurement_method='absolute', t=19.1)
    assert std_dev > 0


def test_calculate_std_dev_absolute_without_t_raises():
    with pytest.raises(ValueError, match="wall thickness"):
        calculate_std_dev(acc=1.0, conf=0.8, measurement_method='absolute')


def test_calculate_std_dev_invalid_method_raises():
    with pytest.raises(ValueError):
        calculate_std_dev(acc=0.1, conf=0.8, measurement_method='unknown')


def test_calculate_partial_safety_factors_invalid_safety_class_raises():
    with pytest.raises(ValueError):
        calculate_partial_safety_factors('extreme', 'relative', 0.05)


def test_calculate_partial_safety_factors_invalid_method_raises():
    with pytest.raises(ValueError):
        calculate_partial_safety_factors('medium', 'ultrasonic', 0.05)


def test_calculate_partial_safety_factors_accuracy_too_high_raises():
    with pytest.raises(ValueError):
        calculate_partial_safety_factors('medium', 'relative', 0.20)


def test_calculate_partial_safety_factors_very_high_absolute():
    result = calculate_partial_safety_factors('very high', 'absolute', 0.05)
    assert result['gamma_m'] == pytest.approx(0.77)
    assert result['gamma_d'] is not None
    assert result['epsilon_d'] is not None


def test_calculate_partial_safety_factors_low_mid_accuracy():
    # Covers the 0.04 <= acc < 0.08 branch for 'low' safety class
    result = calculate_partial_safety_factors('low', 'relative', 0.06)
    assert result['gamma_m'] == pytest.approx(0.90)
    # gamma_d = 1.0 + 5.5*0.06 - 37.5*0.06^2
    assert result['gamma_d'] == pytest.approx(1.0 + 5.5 * 0.06 - 37.5 * 0.06 ** 2)
