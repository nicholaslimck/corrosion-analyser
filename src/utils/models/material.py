from dataclasses import dataclass


@dataclass
class MaterialProperties:
    """
    Material properties

    """
    alpha_u: float = 0.96  # Typically 0.96 as stated in Table 2-2
    temperature: float = None
    smts: float = None
    smys: float = None
    f_u_temp: float = None
    f_y_temp: float = None

    def __post_init__(self):
        if self.smys:
            self.f_y = calculate_strength(self.smys, self.f_y_temp, self.alpha_u)
        if self.smts:
            self.f_u_temp = estimate_de_rating_yield_stress(self.temperature)
            self.f_u = calculate_strength(self.smts, self.f_u_temp, self.alpha_u)


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


def estimate_de_rating_yield_stress(temperature):
    """
    Estimate the de-rating yield stress as defined in Figure 2-3
    Args:
        temperature:

    Returns:

    """
    if 50 < temperature <= 100:
        f_u_temp = 0.6 * temperature - 30
    elif 100 < temperature < 200:
        f_u_temp = 0.4 * temperature - 10
    else:
        raise ValueError('Temperature must be between 50 and 200 C')
    return f_u_temp