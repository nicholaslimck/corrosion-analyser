from src.utils.models import MaterialProperties


def test_calc_tensile_strength(snapshot):
    alpha_u = 0.96
    temperature = 75
    smts = 530.9
    f_u_temp = 15
    material_properties = MaterialProperties(alpha_u=alpha_u, temperature=temperature, smts=smts, f_u_temp=f_u_temp)
    f_u = material_properties.f_u
    assert f_u == snapshot
