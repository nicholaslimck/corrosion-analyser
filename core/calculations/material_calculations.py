def calculate_strength(sms, f_temp, alpha_u):
    """
    Calculates strength as defined in Section 2.6
    f_y = (SMYS - f_y_temp) * alpha_u
    f_u = (SMTS - f_u_temp) * alpha_u
    Args:
        sms: Specified minimum yield stress (SMYS) or tensile strength (SMTS)
        f_temp: De-rating value of the yield stress or tensile strength
        alpha_u: Material strength factor

    Returns:
        strength: tensile strength of the material
    """
    strength = (sms - f_temp) * alpha_u
    return strength
