import math

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor,
                                                        calculate_circumferential_corroded_length_ratio)


def calculate_pressure_capacity(t_nominal, sigma_u, d_nominal, defect_depth, defect_length):
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
    p_cap = 1.05 * ((2*t_nominal*sigma_u) / (d_nominal - t_nominal)) * ((1 - defect_depth)/(1 - defect_depth/q))
    return p_cap


def calculate_pressure_resistance_long_defect(gamma_m, gamma_d, t_nominal, defect_length, d_nominal,
                                              relative_defect_depth_with_uncertainty, f_u):
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

    Returns:
        p_corr: Pressure Resistance
    """
    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_corr = (gamma_m * ((2*t_nominal*f_u)/(d_nominal - t_nominal)) *
              ((1 - gamma_d * relative_defect_depth_with_uncertainty) /
               (1 - gamma_d * relative_defect_depth_with_uncertainty / q)))
    return p_corr


def calculate_pressure_resistance_long_defect_w_compressive(gamma_m, gamma_d, t_nominal, defect_length,
                                                            defect_width, defect_relative_depth_measured,
                                                            defect_relative_depth_normalised, d_nominal,
                                                            f_u, sigma_l, phi):
    """
    Calculates pressure resistance p_corr using the equation defined in Section 3.7.4
    (longitudinal corrosion defect, internal pressure loading with superimposed longitudinal compressive stresses)
    p_corr = gamma_m * (2*t_nom*f_u)/(d_nom - t_nom)
    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        t_nominal: Nominal pipe wall thickness (mm)
        defect_length: Defect Length (mm)
        defect_width: Defect Width (mm)
        defect_relative_depth_measured:
        defect_relative_depth_normalised:
        d_nominal: Nominal Pipe Diameter
        f_u: Tensile strength to be used in design (N/mm^2)
        sigma_l: combined nominal longitudinal stress due to external applied loads (N/mm^2)
        phi: usage factor for longitudinal stress

    Returns:
        p_corr: Pressure Resistance
    """
    p_corr = calculate_pressure_resistance_long_defect(gamma_m, gamma_d, t_nominal, defect_length, d_nominal, 
                                                       defect_relative_depth_normalised, f_u)
    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    theta = calculate_circumferential_corroded_length_ratio(defect_width, d_nominal)
    a_r = 1 - defect_relative_depth_measured * theta
    h1 = (1 + (sigma_l / (phi * f_u)) * (1/a_r)) / (1 - (gamma_m/(2 * phi * a_r)) * 
                                                    ((1 - gamma_d * defect_relative_depth_normalised) / 
                                                     (1 - (gamma_d * defect_relative_depth_normalised / q))))

    p_corr_comp = p_corr * h1

    return p_corr_comp


def calculate_max_defect_depth(gamma_m, gamma_d, t_nominal, defect_length, d_nominal, f_u, p_corr):
    """
    Calculates the maximum defect depth by reversing the pressure resistance calculation from 3.7.3
    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        t_nominal: Nominal pipe wall thickness (mm)
        defect_length: Defect length (mm)
        d_nominal: Nominal pipe diameter (mm)
        f_u: Tensile strength to be used in design (N/mm^2)
        p_corr: Pressure resistance of a single longitudinal corrosion defect under internal pressure loading (N/mm^2)

    Returns:

    """

    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    defect_depth = (q*(-d_nominal*p_corr + 2*f_u*gamma_m*t_nominal + p_corr*t_nominal) /
                    (gamma_d*(-d_nominal*p_corr + 2*f_u*gamma_m*q*t_nominal + p_corr*t_nominal)))
    return defect_depth


def calculate_maximum_defect_depth(gamma_d, epsilon_d, std_dev):
    """
    Calculates the maximum defect depth based on Section 3.7.3.3
    Args:
        gamma_d: Partial Safety Factor for Corrosion Depth
        epsilon_d:
        std_dev:

    Returns:

    """
    defect_depth = (1/gamma_d) - epsilon_d * std_dev
    return defect_depth


def calculate_maximum_defect_length(d, t, gamma_d, gamma_m, f_u, dt_star, p_li, p_le):
    """
    Calculates the maximum defect length based on Section 3.7.3.2
    Args:
        d: Pipe Diameter (mm)
        t: Pipe Thickness (mm)
        gamma_d: Partial Safety Factor for Corrosion Depth
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        f_u: Tensile strength to be used in design (N/mm^2)
        dt_star: Relative Measured Defect Depth
        p_li: Local Incidental Pressure (N/mm^2)
        p_le: Local External Pressure (N/mm^2)

    Returns:

    """
    p_0 = gamma_m * (2 * t * f_u) / (d - t)
    l_acc = math.sqrt((d*t/0.31) * (((gamma_d * dt_star) /
                                     (1 - (p_0 / (p_li - p_le)) * (1 - (gamma_d * dt_star))))**2 - 1))

    return l_acc
