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
