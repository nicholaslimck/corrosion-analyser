import math

from loguru import logger
from scipy.optimize import brentq
from sympy import Symbol, Eq, sqrt, solve, pi

# DNVGL-RP-F101 §3.7.2.1 (p.37): "Measured defects depths shall not exceed 85% of
# the wall thickness, i.e. minimum remaining wall thickness >= 15% of t".
MAX_MEASURED_RELATIVE_DEPTH = 0.85


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
        # 0.31: length correction factor coefficient per DNV-RP-F101 Eq. (2)
        solution = math.sqrt(1 + 0.31 * math.pow(defect_length / (math.sqrt(d_nominal * wall_thickness)), 2))
    else:
        Q = Symbol('Q')
        l = Symbol('l')  # noqa: E741 — matches DNV-RP-F101 equation notation
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
        d_t_meas: Measured defect depth
        epsilon_d: Factor for defining a fractile value for corrosion depth
        st_dev: Standard deviation of the measured defect depth
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
    relative_defect_depth_with_uncertainty = (
            q * (-d_nominal * p_corr + 2 * f_u * gamma_m * t_nominal + p_corr * t_nominal) /
            (gamma_d * (-d_nominal * p_corr + 2 * f_u * gamma_m * q * t_nominal + p_corr * t_nominal))
    )
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
        st_dev: float) -> float:
    """
    Calculates the maximum defect depth by reversing the pressure resistance calculation from 3.7.4

    Pressure resistance decreases monotonically with defect depth, so the measured depth
    whose resistance equals the target resistance is bracketed between zero and the 85%
    acceptance limit and found by root finding on the forward equation. This replaces the
    explicit symbolic inverse, which had no discriminant guard and returned negative
    depths for large compressive stresses.

    Args:
        gamma_m: Partial Safety Factor for Longitudinal Corrosion Model Projection
        gamma_d: Partial Safety Factor for Corrosion Depth
        pipe_diameter: Nominal pipe diameter (mm)
        pipe_thickness: Nominal pipe wall thickness (mm)
        defect_length: Defect length (mm)
        defect_width: Defect width (mm)
        f_u: Tensile strength to be used in design (N/mm^2)
        p_corr_comp: Pressure resistance of a single longitudinal corrosion defect under internal pressure loading with a superimposed compressive load (N/mm^2)
        xi: Usage factor for longitudinal stress
        sigma_l: Combined nominal longitudinal stress (N/mm^2)
        epsilon_d: Factor for defining a fractile value for corrosion depth
        st_dev: Standard deviation of the measured defect depth

    Returns:
        maximum measured relative defect depth, between 0 and the 85% acceptance limit
    """
    def pressure_resistance(measured_depth: float) -> float:
        # Imported here: pressure_calculations imports this module, so a module level
        # import would be circular.
        from src.utils.calculations.pressure_calculations import (
            calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
        return calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
            gamma_m=gamma_m,
            gamma_d=gamma_d,
            t_nominal=pipe_thickness,
            d_nominal=pipe_diameter,
            defect_length=defect_length,
            defect_width=defect_width,
            defect_relative_depth_measured=measured_depth,
            relative_defect_depth_with_uncertainty=measured_depth + epsilon_d * st_dev,
            f_u=f_u,
            sigma_l=sigma_l,
            phi=xi,
        )

    minimum_depth = 1e-9   # a zero depth defect is the limit of the equation, not a solution
    maximum_depth = MAX_MEASURED_RELATIVE_DEPTH

    if pressure_resistance(minimum_depth) <= p_corr_comp:
        # Even an uncorroded pipe cannot carry the required pressure at this defect length
        return 0.0
    if pressure_resistance(maximum_depth) >= p_corr_comp:
        # The tolerable depth is beyond the acceptance limit of Section 3.7.2.1
        return maximum_depth

    return float(brentq(
        lambda measured_depth: pressure_resistance(measured_depth) - p_corr_comp,
        minimum_depth,
        maximum_depth,
        xtol=1e-10,
    ))


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
    # A measured depth above 85% of the wall thickness is outside the acceptance
    # criteria regardless of the calculated capacity, see Section 3.7.2.1
    return min(defect_depth, MAX_MEASURED_RELATIVE_DEPTH)


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
    if d_t_star is None and not all(value is not None for value in [d_t_meas, epsilon_d, st_dev]):
        raise ValueError("Must provide a value for d_t_star or (d_t_meas, epsilon_d and st_dev)")
    elif d_t_star is None:
        d_t_star = calculate_relative_defect_depth_with_inaccuracies(d_t_meas, epsilon_d, st_dev)
    p_0 = gamma_m * (2 * t * f_u) / (d - t)

    if not all([(1 - gamma_d * d_t_star) > 0,
                (p_0 * (1 - gamma_d * d_t_star) < p_li - p_le < p_0)]):
        logger.debug('Equation invalid for inputs')
        return None

    l_acc = math.sqrt((d * t / 0.31) * (((gamma_d * d_t_star) /
                                         (1 - (p_0 / (p_li - p_le)) * (1 - (gamma_d * d_t_star)))) ** 2 - 1))

    return l_acc


def calculate_combined_length(defects: list):
    """
    Total axial length of a combined defect, DNVGL-RP-F101 Section 3.8.2 Step 7:
    the length of the combined defect includes the spacing between the defects.

    Args:
        defects: two adjacent defects, ordered by axial position

    Returns:
        combined_length: total length including spacing (mm)
    """
    defect_1 = defects[0]
    defect_2 = defects[1]

    combined_length = defect_1.length + defect_2.length + (defect_2.position - defect_1.position)
    return combined_length


def calculate_combined_depth(defects: list, measurement_method: str):
    """
    Effective depth of a combined defect, DNVGL-RP-F101 Section 3.8.2 Step 8:
    a rectangular approximation to the corroded area over the total length.

    Args:
        defects: two adjacent defects, ordered by axial position
        measurement_method: 'relative' or 'absolute'

    Returns:
        combined_depth: length weighted depth, relative (d/t) or absolute (mm)
    """
    defect_1 = defects[0]
    defect_2 = defects[1]

    if measurement_method == 'relative':
        combined_depth = ((defect_1.relative_depth * defect_1.length + defect_2.relative_depth * defect_2.length)
                          / (calculate_combined_length(defects)))
    else:
        combined_depth = ((defect_1.depth * defect_1.length + defect_2.depth * defect_2.length)
                          / (calculate_combined_length(defects)))

    return combined_depth


def verify_interaction(defects: list, pipe_diameter, pipe_thickness):
    """
    Approximate test for axial interaction between two adjacent defects.

    DNVGL-RP-F101 Section 3.8.2 defines interaction through a projection line
    procedure: the corroded section is divided into sections of a minimum length of
    5.0 sqrt(D t) with a minimum overlap of 2.5 sqrt(D t) (Steps 1-2), defects are
    projected onto axial lines at Z = 360 sqrt(t / D) degrees (Steps 3-4), and the
    pressure resistance of all combinations of adjacent defects n to m is calculated
    with the minimum governing the assessment (Steps 6-9).

    This is a two-defect approximation of that procedure: defects are treated as
    interacting when their combined axial extent, including the separation between
    them, fits within one minimum section length of 5.0 sqrt(D t). Circumferential
    projection is not implemented, so all defects are assumed to share a projection
    line. Only the first two defects are considered - see Known limitations.

    Args:
        defects: adjacent defects, ordered by axial position
        pipe_diameter: nominal outside diameter (mm)
        pipe_thickness: nominal wall thickness (mm)

    Returns:
        True if the defects should be combined into a single defect
    """
    if len(defects) != 2:
        raise ValueError(
            f'Interaction is assessed between exactly two defects; {len(defects)} were '
            f'supplied - see Known limitations in the README'
        )
    separation = defects[1].position - defects[0].position
    # DNVGL-RP-F101 Section 3.8.2 Step 1: minimum length of a sectioned assessment
    minimum_length = 5.0 * math.sqrt(pipe_diameter * pipe_thickness)
    if separation + sum([defect.length for defect in defects]) < minimum_length:
        return True
    else:
        return False
