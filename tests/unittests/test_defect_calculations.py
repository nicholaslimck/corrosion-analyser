import pytest

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor, \
                                                        calculate_relative_defect_depth_with_inaccuracies,
                                                        calculate_circumferential_corroded_length_ratio,
                                                        calculate_max_defect_depth_longitudinal)
from src.utils.calculations.pressure_calculations import calculate_pressure_resistance_longitudinal_defect


def test_calc_length_correction_factor(example_a_1, snapshot):
    q = calculate_length_correction_factor(example_a_1['defect_length']['value'],
                                           example_a_1['outside_diameter']['value'],
                                           example_a_1['wall_thickness']['value'])
    assert q == snapshot


def test_calc_relative_defect_depth_with_inaccuracies(snapshot):
    d_t_star = calculate_relative_defect_depth_with_inaccuracies(0.25,
                                                                 1.0,
                                                                 0.08)
    assert d_t_star == snapshot


def test_calc_circumferential_corroded_length_ratio(snapshot):
    ar = calculate_circumferential_corroded_length_ratio(100,
                                                         219.0)
    assert ar == snapshot


def test_calculate_max_defect_depth_longitudinal_equivalence():
    gamma_m = 0.85
    gamma_d = 1.28
    t_nominal = 19.1
    defect_length = 200
    d_nominal = 812.8
    relative_defect_depth = 0.34
    epsilon_d = 1.0
    st_dev = 0.08
    relative_defect_depth_with_uncertainty = relative_defect_depth + epsilon_d * st_dev
    f_u = 495.3

    p_corr = calculate_pressure_resistance_longitudinal_defect(
        gamma_m=gamma_m,
        gamma_d=gamma_d,
        t_nominal=t_nominal,
        defect_length=defect_length,
        d_nominal=d_nominal,
        relative_defect_depth_with_uncertainty=relative_defect_depth_with_uncertainty,
        f_u=f_u
    )

    max_defect_depth = calculate_max_defect_depth_longitudinal(
        gamma_m=gamma_m,
        gamma_d=gamma_d,
        t_nominal=t_nominal,
        defect_length=defect_length,
        d_nominal=d_nominal,
        f_u=f_u,
        p_corr=p_corr,
        epsilon_d=1.0,
        st_dev=0.08
    )
    assert max_defect_depth == pytest.approx(relative_defect_depth)

# def test_calculate_max_defect_depth_longitudinal_with_stress(snapshot):
#     assert False
