from core.calculations.material_calculations import calculate_strength


def test_calc_tensile_strength(snapshot):
    alpha_u = 0.96
    smts = 530.9
    f_u_temp = 15
    f_u = calculate_strength(smts, f_u_temp, alpha_u)
    assert f_u == snapshot
