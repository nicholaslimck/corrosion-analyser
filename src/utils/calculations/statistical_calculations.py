import math

from scipy.special import ndtri


def calculate_std_dev(conf, acc, measurement_method: str, t=None):
    """
    Calculates the standard deviation where Normal distribution is assumed.
    Args:
        conf: Confidence Interval
        acc: Relative/Absolute accuracy
        measurement_method: Relative/Absolute
        t: Wall thickness, only used with absolute measurements

    Returns:
        std_dev: Standard deviation
    """
    if measurement_method == 'relative':
        std_dev = acc / calculate_inv_cumulative_dist(0.5 + conf / 2)
    elif measurement_method == 'absolute':
        if not t:
            raise ValueError('Cannot calculate absolute accuracy without wall thickness')
        std_dev = (math.sqrt(2) * acc) / (t * calculate_inv_cumulative_dist(0.5 + conf / 2))
    else:
        raise ValueError('Must define either relative or absolute accuracy')
    return std_dev


def calculate_inv_cumulative_dist(x):
    """
    Calculates the inverse cumulative distribution function of a standard normal variable
    Args:
        x: Input variable
    Returns:
        Inverse cumulative distribution of a standard normal variable
    """
    return ndtri(x)


def calculate_partial_safety_factors(safety_class, inspection_method, inspection_accuracy):
    """
    Returns the partial safety factor (gamma_m) based off the safety class as stated in Table 3-2
    Returns the partial safety factor (gamma_d) and fractile (epsilon_d) value per Table 3-8
    Args:
        safety_class: Safety class, must be 'low', 'medium', 'high' or 'very high'
        inspection_method: Must be 'relative' or 'absolute'
        inspection_accuracy: Must be smaller than 0.16

    Returns:
        partial_safety_factors: {"gamma_m", "gamma_d", "epsilon_d"}
    """
    safety_class = safety_class.lower()
    if safety_class not in ['low', 'medium', 'high', 'very high']:
        raise ValueError(f"Invalid safety class provided: {safety_class}")
    if inspection_method not in ['relative', 'absolute']:
        raise ValueError(f"Invalid inspection method provided: {inspection_method}")
    if inspection_accuracy > 0.16:
        raise ValueError(f'Invalid inspection sizing accuracy (StD[d/t]) provided: {inspection_accuracy}')

    # Calculate gamma_m
    gamma_m = None
    if safety_class == "low":
        if inspection_method == "relative":
            gamma_m = 0.90
        else:
            gamma_m = 0.94
    elif safety_class == "medium":
        if inspection_method == "relative":
            gamma_m = 0.85
        else:
            gamma_m = 0.88
    elif safety_class == "high":
        if inspection_method == "relative":
            gamma_m = 0.80
        else:
            gamma_m = 0.82
    elif safety_class == "very high":
        if inspection_method == "relative":
            gamma_m = 0.76
        else:
            gamma_m = 0.77

    # Calculate gamma_d
    gamma_d = None
    if safety_class == "low":
        if inspection_accuracy < 0.04:
            gamma_d = 1.0 + 4.0 * inspection_accuracy
        elif 0.04 <= inspection_accuracy < 0.08:
            gamma_d = 1.0 + 5.5 * inspection_accuracy - 37.5 * pow(inspection_accuracy, 2)
        elif 0.08 <= inspection_accuracy <= 0.16:
            gamma_d = 1.2
    elif safety_class == "medium":
        if inspection_accuracy <= 0.16:
            gamma_d = 1.0 + 4.6 * inspection_accuracy - 13.9 * pow(inspection_accuracy, 2)
    elif safety_class == "high":
        if inspection_accuracy <= 0.16:
            gamma_d = 1.0 + 4.3 * inspection_accuracy - 4.1 * pow(inspection_accuracy, 2)
    elif safety_class == "very high":
        if inspection_accuracy < 0.03:
            gamma_d = 1.0 * 4.0 * inspection_accuracy
        elif 0.03 <= inspection_accuracy < 0.16:
            gamma_d = 0.92 + 7.1 * inspection_accuracy - 8.3 * pow(inspection_accuracy, 2)

    # Calculate epsilon_d
    epsilon_d = None
    if inspection_accuracy <= 0.04:
        epsilon_d = 0
    elif 0.04 < inspection_accuracy <= 0.16:
        epsilon_d = -1.33 + 37.5 * inspection_accuracy - 104.2 * pow(inspection_accuracy, 2)

    partial_safety_factors = {
        "gamma_m": gamma_m,
        "gamma_d": gamma_d,
        "epsilon_d": epsilon_d
    }

    return partial_safety_factors


def calculate_usage_factors(safety_class: str) -> float:
    if safety_class == 'low':
        return 0.9
    elif safety_class == 'medium':
        return 0.85
    elif safety_class == 'high':
        return 0.8
    elif safety_class == 'very_high':
        return 0.75
