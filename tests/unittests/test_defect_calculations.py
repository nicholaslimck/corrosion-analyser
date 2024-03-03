from src.utils.calculations.defect_calculations import calculate_length_correction_factor, \
    calculate_relative_defect_depth_with_inaccuracies, calculate_circumferential_corroded_length_ratio


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


# def test_calculate_max_defect_depth_longitudinal(snapshot):
#     assert False


# def test_calculate_max_defect_depth_longitudinal_with_stress(snapshot):
#     assert False
