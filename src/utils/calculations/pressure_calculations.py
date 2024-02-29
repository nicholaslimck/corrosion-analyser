import math

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor,
                                                        calculate_circumferential_corroded_length_ratio)


def calculate_pressure_capacity(
        t_nominal: float,
        sigma_u: float,
        d_nominal: float,
        defect_depth: float,
        defect_length: float):
    """
    Calculates the burst pressure capacity using the equation defined in Section 2.1 Capacity equation
    Pcap = 1.05[(2t*sigma_u)/(D-t)] * [(1-(d/t))/(1-(d/t)/Q)]

    t = uncorroded, measured, pipe wall thickness, or t_nom (mm)
    sigma_u = ultimate tensile strength (N/mm^2)
    D = nominal outside diameter (mm)

    (d/t) = measured defect depth
    Q = length correction factor
    Args:
        t_nominal: Nominal pipe wall thickness (mm)
        sigma_u: Ultimate tensile strength (N/mm^2)
        d_nominal: Nominal Pipe Diameter (mm)
        defect_depth: Defect Depth (mm)
        defect_length: Defect Length (mm)

    Returns:
        p_cap: Pressure Capacity
    """
    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_cap = 1.05 * ((2 * t_nominal * sigma_u) / (d_nominal - t_nominal)) * ((1 - defect_depth) / (1 - defect_depth / q))
    return p_cap


def calculate_pressure_resistance_longitudinal_defect(
        gamma_m,
        gamma_d,
        t_nominal,
        defect_length,
        d_nominal,
        relative_defect_depth_with_uncertainty,
        f_u,
        q=None):
    """
    Calculates pressure resistance p_corr using the equation defined in Section 3.7.3
    (longitudinal corrosion defect, internal pressure loading only)
    p_corr = gamma_m * (2*t_nom*f_u)/(d_nom - t_nom)
    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        t_nominal: Nominal pipe wall thickness
        defect_length: Defect Length (mm)
        d_nominal: Nominal Pipe Diameter (mm)
        relative_defect_depth_with_uncertainty:
        f_u: Tensile strength to be used in design (N/mm^2)
        q: Length Correction Factor

    Returns:
        p_corr: Pressure Resistance
    """
    if not q:
        q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_corr = (gamma_m * ((2 * t_nominal * f_u) / (d_nominal - t_nominal)) *
              ((1 - gamma_d * relative_defect_depth_with_uncertainty) /
               (1 - gamma_d * relative_defect_depth_with_uncertainty / q)))
    return p_corr


def calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
        gamma_m: float,
        gamma_d: float,
        t_nominal: float,
        d_nominal: float,
        defect_length: float,
        defect_width: float,
        defect_relative_depth_measured: float,
        relative_defect_depth_with_uncertainty: float,
        f_u: float,
        sigma_l: float,
        phi: float,
        q: float = None):
    """
    Calculates pressure resistance p_corr using the equation defined in Section 3.7.4
    (longitudinal corrosion defect, internal pressure loading with superimposed longitudinal compressive stresses)
    p_corr = gamma_m * (2*t_nom*f_u)/(d_nom - t_nom)
    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        t_nominal: Nominal pipe wall thickness (mm)
        d_nominal: Nominal Pipe Diameter
        defect_length: Defect Length (mm)
        defect_width: Defect Width (mm)
        defect_relative_depth_measured:
        relative_defect_depth_with_uncertainty:
        f_u: Tensile strength to be used in design (N/mm^2)
        sigma_l: combined nominal longitudinal stress due to external applied loads (N/mm^2)
        phi: usage factor for longitudinal stress
        q: Length correction factor

    Returns:
        p_corr: Pressure Resistance
    """
    if not q:
        q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_corr = calculate_pressure_resistance_longitudinal_defect(
        gamma_m=gamma_m, gamma_d=gamma_d, t_nominal=t_nominal, defect_length=defect_length, d_nominal=d_nominal,
        relative_defect_depth_with_uncertainty=relative_defect_depth_with_uncertainty, f_u=f_u, q=q)
    theta = calculate_circumferential_corroded_length_ratio(defect_width, d_nominal)
    a_r = 1 - defect_relative_depth_measured * theta
    # h1 cannot be greater than 1
    h1 = min(1.0, (1 + (sigma_l / (phi * f_u)) * (1 / a_r)) / (1 - (gamma_m / (2 * phi * a_r)) *
                                                      ((1 - gamma_d * relative_defect_depth_with_uncertainty) /
                                                       (1 - (gamma_d * relative_defect_depth_with_uncertainty / q)))))

    p_corr_comp = p_corr * h1

    return p_corr_comp
