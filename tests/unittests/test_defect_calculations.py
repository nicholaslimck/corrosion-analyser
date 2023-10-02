from src.utils.calculations.defect_calculations import calculate_length_correction_factor


def test_calc_length_correction_factor(pipe_a_1, defect_a_1, snapshot):
    q = calculate_length_correction_factor(defect_a_1.length,
                                           pipe_a_1.dimensions.outside_diameter,
                                           pipe_a_1.dimensions.wall_thickness)
    assert q == snapshot
