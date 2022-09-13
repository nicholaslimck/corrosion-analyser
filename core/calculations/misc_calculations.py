from scipy.special import ndtri


def calculate_std_dev(acc_rel, conf):
    """
    Calculates the standard deviation where Normal distribution is assumed.
    Args:
        acc_rel: Relative accuracy
        conf: Confidence Interval

    Returns:
        std_dev: Standard deviation
    """
    std_dev = acc_rel / calculate_inv_cumulative_dist(0.5 + conf / 2)
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
