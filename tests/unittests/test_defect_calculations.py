import pytest

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor,
                                                        calculate_relative_defect_depth_with_inaccuracies,
                                                        calculate_circumferential_corroded_length_ratio,
                                                        calculate_max_defect_depth_longitudinal,
                                                        calculate_max_defect_depth_longitudinal_with_stress,
                                                        calculate_combined_length,
                                                        calculate_combined_depth,
                                                        verify_interaction,
                                                        calculate_maximum_defect_depth,
                                                        calculate_maximum_defect_length)
from src.utils.calculations.pressure_calculations import (
    calculate_pressure_resistance_longitudinal_defect,
    calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
from src.utils.models.defect import Defect


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


def test_calculate_max_defect_depth_longitudinal_with_stress_equivalence():
    gamma_m = 0.85
    gamma_d = 1.28
    pipe_thickness = 19.1
    defect_length = 200
    defect_width = 100
    pipe_diameter = 812.8
    relative_defect_depth = 0.34
    epsilon_d = 1.0
    st_dev = 0.08
    f_u = 495.264
    xi = 0.85
    sigma_l = -200

    relative_defect_depth_with_uncertainty = relative_defect_depth + epsilon_d * st_dev

    p_corr_comp = calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
        gamma_m=gamma_m,
        gamma_d=gamma_d,
        t_nominal=pipe_thickness,
        d_nominal=pipe_diameter,
        defect_length=defect_length,
        defect_width=defect_width,
        defect_relative_depth_measured=relative_defect_depth,
        relative_defect_depth_with_uncertainty=relative_defect_depth_with_uncertainty,
        f_u=f_u,
        sigma_l=sigma_l,
        phi=xi,
    )

    max_depth = calculate_max_defect_depth_longitudinal_with_stress(
        gamma_m=gamma_m,
        gamma_d=gamma_d,
        pipe_diameter=pipe_diameter,
        pipe_thickness=pipe_thickness,
        defect_length=defect_length,
        defect_width=defect_width,
        f_u=f_u,
        p_corr_comp=p_corr_comp,
        xi=xi,
        sigma_l=sigma_l,
        epsilon_d=epsilon_d,
        st_dev=st_dev,
    )

    assert max_depth == pytest.approx(relative_defect_depth, abs=1e-6)


# --- Defect depth formula ---

def test_calculate_maximum_defect_depth():
    # 1/1.28 - 1.0 * 0.08 = 0.70125
    result = calculate_maximum_defect_depth(gamma_d=1.28, epsilon_d=1.0, std_dev=0.08)
    assert result == pytest.approx(0.70125)


# --- Maximum defect length ---

def test_calculate_maximum_defect_length_valid():
    # DNV example: defect (l=200, d/t=0.25) passes → max allowable length > 200
    l_acc = calculate_maximum_defect_length(
        d=812.8, t=19.1,
        gamma_d=1.28, gamma_m=0.85,
        f_u=495.264,
        p_li=16.6962, p_le=1.005525,
        d_t_meas=0.25, epsilon_d=1.0, st_dev=0.08
    )
    assert l_acc is not None
    assert l_acc > 200


def test_calculate_maximum_defect_length_requires_depth_inputs():
    with pytest.raises(ValueError):
        calculate_maximum_defect_length(d=812.8, t=19.1, gamma_d=1.28, gamma_m=0.85,
                                        f_u=495.264, p_li=16.6962, p_le=1.005525)


# --- Defect interaction ---

def test_calculate_combined_length():
    d1 = Defect(length=100, relative_depth=0.3, position=0)
    d2 = Defect(length=80, relative_depth=0.5, position=50)
    # L1 + L2 + (pos2 - pos1) = 100 + 80 + 50
    assert calculate_combined_length([d1, d2]) == pytest.approx(230)


def test_calculate_combined_depth_relative():
    d1 = Defect(length=100, relative_depth=0.3, position=0)
    d2 = Defect(length=80, relative_depth=0.5, position=50)
    # (0.3*100 + 0.5*80) / 230 = 70/230
    expected = (0.3 * 100 + 0.5 * 80) / 230
    assert calculate_combined_depth([d1, d2], 'relative') == pytest.approx(expected)


def test_calculate_combined_depth_absolute():
    d1 = Defect(length=100, depth=5.0, position=0)
    d2 = Defect(length=80, depth=8.0, position=50)
    combined_len = 100 + 80 + 50
    expected = (5.0 * 100 + 8.0 * 80) / combined_len
    assert calculate_combined_depth([d1, d2], 'absolute') == pytest.approx(expected)


def test_verify_interaction_true():
    # separation + lengths = 50 + 100 + 100 = 250 < 5*sqrt(812.8*19.1) ≈ 623
    d1 = Defect(length=100, relative_depth=0.3, position=0)
    d2 = Defect(length=100, relative_depth=0.3, position=50)
    assert verify_interaction([d1, d2], pipe_diameter=812.8, pipe_thickness=19.1)


def test_verify_interaction_false():
    # separation + lengths = 500 + 100 + 100 = 700 > 623
    d1 = Defect(length=100, relative_depth=0.3, position=0)
    d2 = Defect(length=100, relative_depth=0.3, position=500)
    assert not verify_interaction([d1, d2], pipe_diameter=812.8, pipe_thickness=19.1)
