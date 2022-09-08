from core.calculations.defect_calculations import calculate_length_correction_factor


def test_calc_length_correction_factor(snapshot, example_1_pipe):
    q = calculate_length_correction_factor(example_1_pipe.defect_length,
                                           example_1_pipe.outside_diameter,
                                           example_1_pipe.wall_thickness)
    assert q == snapshot
