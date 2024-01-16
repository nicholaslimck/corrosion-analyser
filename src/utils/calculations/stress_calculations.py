import math


def calculate_axial_longitudinal_stress(d, t, f_x):
    """
    Calculate the longitudinal stress due to external applied axial force, based on nominal wall thickness
    Args:
        d: nominal outside diameter (mm)
        t: uncorroded, measured pipe wall thickness (mm)
        f_x:

    Returns:
        sigma_a: Stress (N/mm^2)
    """
    sigma_a = f_x / (math.pi * (d - t) * t)
    return sigma_a


def calculate_bending_longitudinal_stress(d, t, m_y):
    """
    Calculate the longitudinal stress due to external applied bending moment, based on nominal wall thickness
    Args:
        d: nominal outside diameter (mm)
        t: uncorroded, measured pipe wall thickness (mm)
        m_y: external applied bending moment (Nmm)

    Returns:
        sigma_b: Stress (N/mm^2)

    """
    sigma_b = (4 * m_y) / (math.pi * (d - t) ** 2 * t)
    return sigma_b


def calculate_nominal_longitudinal_stress(f_x, m_y, d, t) -> float:
    """
    Calculate the longitudinal stress as per section 3.7.4
    Args:
        f_x: external applied longitudinal force (N)
        m_y: external applied bending moment (Nmm)
        d: nominal outside diameter (mm)
        t: uncorroded, measured pipe wall thickness (mm)
    Returns:
        sigma_l: Combined nominal longitudinal stress (N/mm^2)
    """
    sigma_a = calculate_axial_longitudinal_stress(d, t, f_x)
    sigma_b = calculate_bending_longitudinal_stress(d, t, m_y)
    sigma_l = sigma_a + sigma_b
    return sigma_l
