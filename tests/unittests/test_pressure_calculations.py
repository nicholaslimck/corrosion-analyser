from calculations.pressure_calculations import calculate_pressure_resistance


def test_calculate_pressure_resistance(snapshot):
    outside_diameter = 812.8
    wall_thickness = 19.10
    defect_length = 200
    gamma_m = 0.85
    gamma_d = 1.28

    f_u = 495.26399999999995

    measured_defect_depth = 0.25 + 1.0 * 0.08
    p_corr = calculate_pressure_resistance(gamma_m, gamma_d, wall_thickness, defect_length, outside_diameter, measured_defect_depth, f_u)
    assert p_corr == snapshot
