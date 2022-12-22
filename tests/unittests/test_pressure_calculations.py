from backend.calculations.pressure_calculations import calculate_pressure_resistance


def test_calculate_pressure_resistance(snapshot, example_a_1, pipe_a_1, defect_a_1):
    outside_diameter = pipe_a_1.dimensions.outside_diameter
    wall_thickness = pipe_a_1.dimensions.wall_thickness
    defect_length = defect_a_1.length
    gamma_m = example_a_1['gamma_m']['value']
    gamma_d = example_a_1['gamma_d']['value']

    f_u = pipe_a_1.material_properties.f_u

    measured_defect_depth = 0.25 + 1.0 * 0.08
    p_corr = calculate_pressure_resistance(
        gamma_m,
        gamma_d,
        wall_thickness,
        defect_length,
        outside_diameter,
        measured_defect_depth,
        f_u
    )
    assert p_corr == snapshot
