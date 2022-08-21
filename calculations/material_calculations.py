def calculate_tensile_strength(smts, f_u_temp, alpha_u):
    """
    Calculates tensile strength as defined in Section 2.6
    f_u = (SMTS - f_u_temp) * alpha_u
    Args:
        smts:
        f_u_temp:
        alpha_u:

    Returns:
        f_u: tensile strength of the material
    """
    f_u = (smts - f_u_temp)*alpha_u
    return f_u
