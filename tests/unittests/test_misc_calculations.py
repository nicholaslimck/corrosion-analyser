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
