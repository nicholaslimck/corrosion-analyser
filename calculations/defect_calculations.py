import math


def calculate_length_correction_factor(defect_length, d_nominal, t):
    """
    Calculates the length correction factor Q
    Q = sqrt((1+0.31(l/sqrt(D*t))^2)
    l = measured defect length
    t = uncorroded, measured, pipe wall thickness, or t_nom (mm)
    D = nominal outside diameter (mm)
    Args:
        defect_length:
        d_nominal:
        t:

    Returns:
        q: length correction factor
    """
    q = math.sqrt(1 + 0.31 * math.pow(defect_length / (math.sqrt(d_nominal * t)), 2))
    return q
