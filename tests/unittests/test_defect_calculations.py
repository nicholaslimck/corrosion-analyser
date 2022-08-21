from calculations.defect_calculations import calculate_length_correction_factor


def test_calc_length_correction_factor(snapshot):
    outside_diameter = 812.8
    wall_thickness = 19.10
    defect_length = 200
    q = calculate_length_correction_factor(defect_length, outside_diameter, wall_thickness)
    assert q == snapshot
