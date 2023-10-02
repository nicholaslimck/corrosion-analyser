import math


def calculate_length_correction_factor(defect_length: float,
                                       d_nominal: float,
                                       t: float) -> float:
    """
    Calculates the length correction factor Q as defined in Section 2.1
    Q = sqrt((1+0.31(l/sqrt(D*t))^2)
    l = measured defect length
    t = uncorroded, measured, pipe wall thickness, or t_nom (mm)
    D = nominal outside diameter (mm)
    Args:
        defect_length: Defect length in mm.
        d_nominal: Nominal outside diameter in mm
        t: Nominal pipe wall thickness in mm

    Returns:
        q: length correction factor
    """
    q = math.sqrt(1 + 0.31 * math.pow(defect_length / (math.sqrt(d_nominal * t)), 2))
    return q