from src.utils.calculations.defect_calculations import calculate_length_correction_factor


def test_calc_length_correction_factor(example_a_1, snapshot):
    q = calculate_length_correction_factor(example_a_1['defect_length']['value'],
                                           example_a_1['outside_diameter']['value'],
                                           example_a_1['wall_thickness']['value'])
    assert q == snapshot
