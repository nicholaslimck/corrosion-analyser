from ..calculations.defect_calculations import calculate_length_correction_factor


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
        t_nominal:
        sigma_u:
        d_nominal:
        defect_depth:
        defect_length:

    Returns:
        p_cap: Pressure Capacity
    """
    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_cap = 1.05 * ((2*t_nominal*sigma_u) / (d_nominal - t_nominal)) * ((1 - defect_depth)/(1 - defect_depth/q))
    return p_cap


def calculate_pressure_resistance(gamma_m, gamma_d, t_nominal, defect_length, d_nominal, defect_depth, f_u):
    """
    Calculates pressure resistance p_corr using the equation defined in Section 3.7.3
    p_corr = gamma_m * (2*t_nom*f_u)/(d_nom - t_nom)
    Args:
        gamma_m: Partial safety factor
        gamma_d:
        t_nominal:
        defect_length:
        d_nominal:
        defect_depth:
        f_u:

    Returns:
        p_corr: Pressure Resistance
    """
    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    p_corr = gamma_m * ((2*t_nominal*f_u)/(d_nominal - t_nominal)) * ((1 - gamma_d*defect_depth)/(1-gamma_d*defect_depth/q))
    return p_corr


def calculate_max_defect_depth(gamma_m, gamma_d, t_nominal, defect_length, d_nominal, f_u, p_corr):
    """
    Calculates the maximum defect depth
    Args:
        gamma_m:
        gamma_d:
        t_nominal:
        defect_length:
        d_nominal:
        f_u:
        p_corr:

    Returns:

    """

    q = calculate_length_correction_factor(defect_length, d_nominal, t_nominal)
    defect_depth = q*(-d_nominal*p_corr + 2*f_u*gamma_m*t_nominal + p_corr*t_nominal)/(gamma_d*(-d_nominal*p_corr + 2*f_u*gamma_m*q*t_nominal + p_corr*t_nominal))
    return defect_depth


def calculate_max_defect_depth_alt(gamma_d, epsilon_d, std_dev):
    """
    Calculates the maximum defect depth based on Section 3.7.3.3
    Args:
        gamma_d:
        epsilon_d:
        std_dev:

    Returns:

    """
    defect_depth = (1/gamma_d) - epsilon_d * std_dev
    return defect_depth
