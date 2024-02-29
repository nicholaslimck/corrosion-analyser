import pytest

from src.utils.calculations.stress_calculations import *


@pytest.mark.parametrize("d, t, f_x", [
    (219, 14.5, 100),
    (219, 14.5, 200),
    (219, 14.5, 300),
    (219, 14.5, 400),
])
def test_calculate_axial_longitudinal_stress(d, t, f_x, snapshot):
    sigma_a = calculate_axial_longitudinal_stress(d, t, f_x)
    assert sigma_a == snapshot


@pytest.mark.parametrize("d, t, m_y", [
    (219, 14.5, 100),
    (219, 14.5, 200),
    (219, 14.5, 300),
    (219, 14.5, 400),
])
def test_calculate_bending_longitudinal_stress(d, t, m_y, snapshot):
    sigma_b = calculate_bending_longitudinal_stress(d, t, m_y)
    assert sigma_b == snapshot

@pytest.mark.parametrize("f_x, m_y, d, t", [
    (-200, 0, 219, 14.5),
    (200, 0, 219, 14.5),
    (0, 200, 219, 14.5),
    (0, -200, 219, 14.5),
])
def test_calculate_nominal_longitudinal_stress(f_x, m_y, d, t, snapshot):
    sigma_l = calculate_nominal_longitudinal_stress(f_x, m_y, d, t)
    assert sigma_l == snapshot
