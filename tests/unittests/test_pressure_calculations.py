import pytest

from src.utils.calculations.pressure_calculations import calculate_pressure_resistance_longitudinal_defect
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
