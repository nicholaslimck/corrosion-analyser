from src.utils.calculations.pressure_calculations import calculate_pressure_resistance


def test_calculate_pressure_resistance(snapshot, example_a_1):
    outside_diameter = example_a_1['outside_diameter']['value']
    wall_thickness = example_a_1['wall_thickness']['value']
    defect_length = example_a_1['defect_length']['value']
    gamma_m = example_a_1['gamma_m']['value']
    gamma_d = example_a_1['gamma_d']['value']

    f_u_temp = (example_a_1['smts']['value'] - example_a_1['f_u_temp']['value']) * 0.96

    measured_defect_depth = 0.25 + 1.0 * 0.08
    p_corr = calculate_pressure_resistance(
        gamma_m,
        gamma_d,
        wall_thickness,
        defect_length,
        outside_diameter,
        measured_defect_depth,
        f_u_temp
    )
    assert p_corr == snapshot
