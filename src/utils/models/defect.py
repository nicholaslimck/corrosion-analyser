import math
from dataclasses import dataclass, field


@dataclass
class Defect:
    length: float
    elevation: float
    width: float = None
    depth: float = None
    relative_depth: float = None

    length_correction_factor: float = field(init=False)

    def __post_init__(self):
        if not (self.depth or self.relative_depth):
            raise ValueError('Either depth or relative depth must be provided')

    def calculate_d_t(self, epsilon_d, stdev):
        """
        Calculate (d/t)*
        Args:
            epsilon_d:
            stdev:

        Returns:

        """
        self.depth = self.relative_depth + epsilon_d * stdev

    def generate_length_correction_factor(self, d_nominal, t):
        """
        Generate the length correction factor of the defect
        Args:
            d_nominal: Nominal outside diameter in mm
            t: Nominal pipe wall thickness in mm

        Returns:

        """
        self.length_correction_factor = calculate_length_correction_factor(self.length, d_nominal, t)


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
