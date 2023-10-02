import pytest

from src.utils.calculations.statistical_calculations import calculate_std_dev, calculate_partial_safety_factors


def test_calculate_std_dev(snapshot):
    acc_rel = 0.1
    conf = 0.8
    assert calculate_std_dev(acc_rel=acc_rel, conf=conf) == snapshot


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
