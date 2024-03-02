import math

from loguru import logger
from sympy import *


def calculate_length_correction_factor(defect_length: float,
                                       d_nominal: float,
                                       wall_thickness: float,
                                       symbolic: bool = False) -> float:
    """
    Calculates the length correction factor Q as defined in Section 2.1
    Q = sqrt((1+0.31(l/sqrt(D*t))^2))
    l = measured defect length
    t = uncorroded, measured, pipe wall thickness, or t_nom (mm)
    D = nominal outside diameter (mm)
    Args:
        defect_length: Defect length in mm.
        d_nominal: Nominal outside diameter in mm
        wall_thickness: Nominal pipe wall thickness in mm
        symbolic: Use symbolic mode

    Returns:
        q: length correction factor
    """
    if not symbolic:
        solution = math.sqrt(1 + 0.31 * math.pow(defect_length / (math.sqrt(d_nominal * wall_thickness)), 2))
    else:
        Q = Symbol('Q')
        l = Symbol('l')
        t = Symbol('t')
        D = Symbol('D')

        eqn = Eq(sqrt((1 + 0.31 * (l / sqrt(D * t)) ** 2)), Q)
        solution = solve(eqn.subs({l: defect_length, t: wall_thickness, D: d_nominal}), Q)[0]
    return solution


def calculate_relative_defect_depth_with_inaccuracies(
        d_t_meas: float,
        epsilon_d: float,
        st_dev: float):
    """
    Calculate the Relative Measured Defect Depth accounting for measurement inaccuracies as defined in Section 3.7.3.1
    (d/t)* = (d/t)meas + epsilon_d * StD[d/t]
    Args:
        d_t_meas:
        epsilon_d:
        st_dev:
    Returns:
        (d/t)*: Relative Measured Defect Depth, adjusted for measurement inaccuracies
    """
    d_t_star = d_t_meas + epsilon_d * st_dev
    return d_t_star


def calculate_circumferential_corroded_length_ratio(circumference: float,
                                                    diameter: float,
                                                    symbolic: bool = False) -> float:
    """
    Ratio of circumferential length of corroded region to the nominal outside circumference of the pipe, (c/pi*D)
    Args:
        circumference: circumferential length of corroded region (usually defect width)
        diameter: nominal outer diameter of the pipe
        symbolic: Use symbolic mode

    Returns:

    """
    if not symbolic:
        solution = circumference / (math.pi * diameter)
    else:
        theta = Symbol('theta')
        c = Symbol('c')
        d = Symbol('d')

        eqn = Eq(c / (pi * d), theta)
        solution = solve(eqn.subs({c: circumference, d: diameter}), theta)[0]
    return solution


def calculate_max_defect_depth_longitudinal(
        gamma_m: float,
        gamma_d: float,
        t_nominal: float,
        defect_length: float,
        d_nominal: float,
        f_u: float,
        p_corr: float,
        epsilon_d: float,
        st_dev: float
):
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
        epsilon_d:
        st_dev:

    Returns:

    """

    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    relative_defect_depth_with_uncertainty = (q * (-d_nominal * p_corr + 2 * f_u * gamma_m * t_nominal + p_corr * t_nominal) /
                    (gamma_d * (-d_nominal * p_corr + 2 * f_u * gamma_m * q * t_nominal + p_corr * t_nominal)))
    relative_defect_depth = relative_defect_depth_with_uncertainty - (epsilon_d * st_dev)
    return relative_defect_depth


def calculate_max_defect_depth_longitudinal_with_stress(
        gamma_m: float,
        gamma_d: float,
        pipe_diameter: float,
        pipe_thickness: float,
        defect_length: float,
        defect_width: float,
        f_u: float,
        p_corr_comp: float,
        xi: float,
        sigma_l: float,
        epsilon_d: float,
        st_dev: float):
    """
    Calculates the maximum defect depth by reversing the pressure resistance calculation from 3.7.4
    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        pipe_diameter: Nominal pipe diameter (mm)
        pipe_thickness: Nominal pipe wall thickness (mm)
        defect_length: Defect length (mm)
        defect_width: Defect length (mm)
        f_u: Tensile strength to be used in design (N/mm^2)
        p_corr_comp: Pressure resistance of a single longitudinal corrosion defect under internal pressure loading with a superimposed compressive load (N/mm^2)
        xi: Usage factor for longitudinal stress
        sigma_l: Combined nominal longitudinal stress (N/mm^2)
        epsilon_d:
        st_dev:

    Returns:

    """
    q = calculate_length_correction_factor(defect_length, pipe_diameter, pipe_thickness)
    theta = calculate_circumferential_corroded_length_ratio(defect_width, pipe_diameter)

    relative_defect_depth = (-epsilon_d*f_u*gamma_d*gamma_m*pipe_thickness*q*st_dev*theta*xi + epsilon_d*gamma_d*p_corr_comp*pipe_diameter*st_dev*theta*xi/2 - epsilon_d*gamma_d*p_corr_comp*pipe_thickness*st_dev*theta*xi/2 + f_u*gamma_d*gamma_m*pipe_thickness*q*xi + f_u*gamma_m*pipe_thickness*q*theta*xi + gamma_d*gamma_m*p_corr_comp*pipe_diameter*q/4 - gamma_d*gamma_m*p_corr_comp*pipe_thickness*q/4 + gamma_d*gamma_m*pipe_thickness*q*sigma_l - gamma_d*p_corr_comp*pipe_diameter*xi/2 + gamma_d*p_corr_comp*pipe_thickness*xi/2 - p_corr_comp*pipe_diameter*q*theta*xi/2 + p_corr_comp*pipe_thickness*q*theta*xi/2 - sqrt(16*epsilon_d**2*f_u**2*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*st_dev**2*theta**2*xi**2 - 16*epsilon_d**2*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*st_dev**2*theta**2*xi**2 + 16*epsilon_d**2*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_thickness**2*q*st_dev**2*theta**2*xi**2 + 4*epsilon_d**2*gamma_d**2*p_corr_comp**2*pipe_diameter**2*st_dev**2*theta**2*xi**2 - 8*epsilon_d**2*gamma_d**2*p_corr_comp**2*pipe_diameter*pipe_thickness*st_dev**2*theta**2*xi**2 + 4*epsilon_d**2*gamma_d**2*p_corr_comp**2*pipe_thickness**2*st_dev**2*theta**2*xi**2 + 32*epsilon_d*f_u**2*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*st_dev*theta*xi**2 - 32*epsilon_d*f_u**2*gamma_d*gamma_m**2*pipe_thickness**2*q**2*st_dev*theta**2*xi**2 + 8*epsilon_d*f_u*gamma_d**2*gamma_m**2*p_corr_comp*pipe_diameter*pipe_thickness*q**2*st_dev*theta*xi - 8*epsilon_d*f_u*gamma_d**2*gamma_m**2*p_corr_comp*pipe_thickness**2*q**2*st_dev*theta*xi + 32*epsilon_d*f_u*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*sigma_l*st_dev*theta*xi - 32*epsilon_d*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*st_dev*theta*xi**2 + 32*epsilon_d*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_thickness**2*q*st_dev*theta*xi**2 + 16*epsilon_d*f_u*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q**2*st_dev*theta**2*xi**2 + 16*epsilon_d*f_u*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*st_dev*theta**2*xi**2 - 16*epsilon_d*f_u*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q**2*st_dev*theta**2*xi**2 - 16*epsilon_d*f_u*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q*st_dev*theta**2*xi**2 - 4*epsilon_d*gamma_d**2*gamma_m*p_corr_comp**2*pipe_diameter**2*q*st_dev*theta*xi + 8*epsilon_d*gamma_d**2*gamma_m*p_corr_comp**2*pipe_diameter*pipe_thickness*q*st_dev*theta*xi - 4*epsilon_d*gamma_d**2*gamma_m*p_corr_comp**2*pipe_thickness**2*q*st_dev*theta*xi - 16*epsilon_d*gamma_d**2*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*sigma_l*st_dev*theta*xi + 16*epsilon_d*gamma_d**2*gamma_m*p_corr_comp*pipe_thickness**2*q*sigma_l*st_dev*theta*xi + 8*epsilon_d*gamma_d**2*p_corr_comp**2*pipe_diameter**2*st_dev*theta*xi**2 - 16*epsilon_d*gamma_d**2*p_corr_comp**2*pipe_diameter*pipe_thickness*st_dev*theta*xi**2 + 8*epsilon_d*gamma_d**2*p_corr_comp**2*pipe_thickness**2*st_dev*theta*xi**2 - 8*epsilon_d*gamma_d*p_corr_comp**2*pipe_diameter**2*q*st_dev*theta**2*xi**2 + 16*epsilon_d*gamma_d*p_corr_comp**2*pipe_diameter*pipe_thickness*q*st_dev*theta**2*xi**2 - 8*epsilon_d*gamma_d*p_corr_comp**2*pipe_thickness**2*q*st_dev*theta**2*xi**2 + 16*f_u**2*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*xi**2 - 32*f_u**2*gamma_d*gamma_m**2*pipe_thickness**2*q**2*theta*xi**2 + 16*f_u**2*gamma_m**2*pipe_thickness**2*q**2*theta**2*xi**2 + 8*f_u*gamma_d**2*gamma_m**2*p_corr_comp*pipe_diameter*pipe_thickness*q**2*xi - 8*f_u*gamma_d**2*gamma_m**2*p_corr_comp*pipe_thickness**2*q**2*xi + 32*f_u*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*sigma_l*xi - 16*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*xi**2 + 16*f_u*gamma_d**2*gamma_m*p_corr_comp*pipe_thickness**2*q*xi**2 - 8*f_u*gamma_d*gamma_m**2*p_corr_comp*pipe_diameter*pipe_thickness*q**2*theta*xi + 8*f_u*gamma_d*gamma_m**2*p_corr_comp*pipe_thickness**2*q**2*theta*xi - 32*f_u*gamma_d*gamma_m**2*pipe_thickness**2*q**2*sigma_l*theta*xi + 16*f_u*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q**2*theta*xi**2 + 16*f_u*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*theta*xi**2 - 16*f_u*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q**2*theta*xi**2 - 16*f_u*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q*theta*xi**2 - 16*f_u*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q**2*theta**2*xi**2 + 16*f_u*gamma_m*p_corr_comp*pipe_thickness**2*q**2*theta**2*xi**2 + gamma_d**2*gamma_m**2*p_corr_comp**2*pipe_diameter**2*q**2 - 2*gamma_d**2*gamma_m**2*p_corr_comp**2*pipe_diameter*pipe_thickness*q**2 + gamma_d**2*gamma_m**2*p_corr_comp**2*pipe_thickness**2*q**2 + 8*gamma_d**2*gamma_m**2*p_corr_comp*pipe_diameter*pipe_thickness*q**2*sigma_l - 8*gamma_d**2*gamma_m**2*p_corr_comp*pipe_thickness**2*q**2*sigma_l + 16*gamma_d**2*gamma_m**2*pipe_thickness**2*q**2*sigma_l**2 - 4*gamma_d**2*gamma_m*p_corr_comp**2*pipe_diameter**2*q*xi + 8*gamma_d**2*gamma_m*p_corr_comp**2*pipe_diameter*pipe_thickness*q*xi - 4*gamma_d**2*gamma_m*p_corr_comp**2*pipe_thickness**2*q*xi - 16*gamma_d**2*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*sigma_l*xi + 16*gamma_d**2*gamma_m*p_corr_comp*pipe_thickness**2*q*sigma_l*xi + 4*gamma_d**2*p_corr_comp**2*pipe_diameter**2*xi**2 - 8*gamma_d**2*p_corr_comp**2*pipe_diameter*pipe_thickness*xi**2 + 4*gamma_d**2*p_corr_comp**2*pipe_thickness**2*xi**2 - 4*gamma_d*gamma_m*p_corr_comp**2*pipe_diameter**2*q**2*theta*xi + 8*gamma_d*gamma_m*p_corr_comp**2*pipe_diameter**2*q*theta*xi + 8*gamma_d*gamma_m*p_corr_comp**2*pipe_diameter*pipe_thickness*q**2*theta*xi - 16*gamma_d*gamma_m*p_corr_comp**2*pipe_diameter*pipe_thickness*q*theta*xi - 4*gamma_d*gamma_m*p_corr_comp**2*pipe_thickness**2*q**2*theta*xi + 8*gamma_d*gamma_m*p_corr_comp**2*pipe_thickness**2*q*theta*xi - 16*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q**2*sigma_l*theta*xi + 32*gamma_d*gamma_m*p_corr_comp*pipe_diameter*pipe_thickness*q*sigma_l*theta*xi + 16*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q**2*sigma_l*theta*xi - 32*gamma_d*gamma_m*p_corr_comp*pipe_thickness**2*q*sigma_l*theta*xi - 8*gamma_d*p_corr_comp**2*pipe_diameter**2*q*theta*xi**2 + 16*gamma_d*p_corr_comp**2*pipe_diameter*pipe_thickness*q*theta*xi**2 - 8*gamma_d*p_corr_comp**2*pipe_thickness**2*q*theta*xi**2 + 4*p_corr_comp**2*pipe_diameter**2*q**2*theta**2*xi**2 - 8*p_corr_comp**2*pipe_diameter*pipe_thickness*q**2*theta**2*xi**2 + 4*p_corr_comp**2*pipe_thickness**2*q**2*theta**2*xi**2)/4)/(gamma_d*theta*xi*(2*f_u*gamma_m*pipe_thickness*q - p_corr_comp*pipe_diameter + p_corr_comp*pipe_thickness))
    relative_defect_depth = float(round(relative_defect_depth, 5))

    return relative_defect_depth


def calculate_maximum_defect_depth(gamma_d, epsilon_d, std_dev):
    """
    Calculates the maximum defect depth based on Section 3.7.3.3
    Args:
        gamma_d: Partial Safety Factor for Corrosion Depth
        epsilon_d:
        std_dev:

    Returns:

    """
    defect_depth = (1 / gamma_d) - epsilon_d * std_dev
    return defect_depth


def calculate_maximum_defect_length(
        d: float,
        t: float,
        gamma_d: float,
        gamma_m: float,
        f_u: float,
        p_li: float,
        p_le: float,
        d_t_star: float = None,
        d_t_meas: float = None,
        epsilon_d: float = None,
        st_dev: float = None
):
    """
    Calculates the maximum defect length based on Section 3.7.3.2
    Args:
        d: Pipe Diameter (mm)
        t: Pipe Thickness (mm)
        gamma_d: Partial Safety Factor for Corrosion Depth
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        f_u: Tensile strength to be used in design (N/mm^2)
        p_li: Local Incidental Pressure (N/mm^2)
        p_le: Local External Pressure (N/mm^2)

        d_t_star: Relative Measured Defect Depth, adjusted for measurement inaccuracies
        d_t_meas: Relative Measured Defect Depth
        epsilon_d:
        st_dev:

    Returns:

    """
    if not d_t_star and not all(value is not None for value in [d_t_meas, epsilon_d, st_dev]):
        raise ValueError("Must provide a value for d_t_star or (d_t_meas, epsilon_d and st_dev)")
    elif not d_t_star:
        d_t_star = calculate_relative_defect_depth_with_inaccuracies(d_t_meas, epsilon_d, st_dev)
    p_0 = gamma_m * (2 * t * f_u) / (d - t)

    if not all([(1 - gamma_d * d_t_star) > 0,
                (p_0 * (1 - gamma_d * d_t_star) < p_li-p_le < p_0)]):
        logger.debug('Equation invalid for inputs')
        return None

    l_acc = math.sqrt((d * t / 0.31) * (((gamma_d * d_t_star) /
                                         (1 - (p_0 / (p_li - p_le)) * (1 - (gamma_d * d_t_star)))) ** 2 - 1))

    return l_acc
