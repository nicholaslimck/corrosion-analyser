import pytest

from src.utils.calculations.pressure_calculations import (calculate_pressure_resistance_longitudinal_defect,
                                                          calculate_pressure_capacity)
from src.utils.calculations.defect_calculations import calculate_max_defect_depth_longitudinal


def test_calculate_pressure_resistance(example_a_1):
    outside_diameter = example_a_1['outside_diameter']['value']
    wall_thickness = example_a_1['wall_thickness']['value']
    defect_length = example_a_1['defect_length']['value']
    gamma_m = example_a_1['gamma_m']['value']
    gamma_d = example_a_1['gamma_d']['value']

    f_u_temp = (example_a_1['smts']['value'] - example_a_1['f_u_temp']['value']) * 0.96

    measured_defect_depth = 0.25 + 1.0 * 0.08
    p_corr = calculate_pressure_resistance_longitudinal_defect(
        gamma_m,
        gamma_d,
        wall_thickness,
        defect_length,
        outside_diameter,
        measured_defect_depth,
        f_u_temp
    )
    assert p_corr == pytest.approx(expected=17.08, rel=1e-3)


def test_validate_max_defect_depth_longitudinal(example_a_1):
    outside_diameter = example_a_1['outside_diameter']['value']
    wall_thickness = example_a_1['wall_thickness']['value']
    defect_length = example_a_1['defect_length']['value']
    gamma_m = example_a_1['gamma_m']['value']
    gamma_d = example_a_1['gamma_d']['value']
    epsilon_d = example_a_1['epsilon_d']['value']
    st_dev = 0.0780

    f_u_temp = (example_a_1['smts']['value'] - example_a_1['f_u_temp']['value']) * 0.96
    measured_defect_depth = 0.25
    measured_defect_depth_with_uncertainty = measured_defect_depth + 1.0 * 0.08

    p_corr = calculate_pressure_resistance_longitudinal_defect(
        gamma_m,
        gamma_d,
        wall_thickness,
        defect_length,
        outside_diameter,
        measured_defect_depth_with_uncertainty,
        f_u_temp
    )

    defect_depth = calculate_max_defect_depth_longitudinal(
        gamma_m,
        gamma_d,
        wall_thickness,
        defect_length,
        outside_diameter,
        f_u_temp,
        p_corr,
        epsilon_d,
        st_dev
    )

    assert defect_depth == pytest.approx(measured_defect_depth, rel=1e-2)


def test_calculate_pressure_capacity():
    # DNV example: D=812.8, t=19.1, f_u=495.264, d/t=0.25, l=200
    p_cap = calculate_pressure_capacity(
        t_nominal=19.1,
        sigma_u=495.264,
        d_nominal=812.8,
        defect_depth=0.25,
        defect_length=200
    )
    # Capacity (no safety factors) must exceed design resistance (~17.08 MPa)
    assert p_cap > 17.08
    assert p_cap == pytest.approx(23.07, rel=1e-2)


def test_pressure_resistance_decreases_with_depth(example_a_1):
    outside_diameter = example_a_1['outside_diameter']['value']
    wall_thickness = example_a_1['wall_thickness']['value']
    defect_length = example_a_1['defect_length']['value']
    gamma_m = example_a_1['gamma_m']['value']
    gamma_d = example_a_1['gamma_d']['value']
    f_u = (example_a_1['smts']['value'] - example_a_1['f_u_temp']['value']) * 0.96

    depths = [0.1, 0.2, 0.3, 0.4]
    resistances = [
        calculate_pressure_resistance_longitudinal_defect(
            gamma_m, gamma_d, wall_thickness, defect_length, outside_diameter,
            d + 1.0 * 0.08, f_u
        )
        for d in depths
    ]
    assert all(r1 > r2 for r1, r2 in zip(resistances, resistances[1:]))
