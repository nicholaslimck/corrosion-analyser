import math
from dataclasses import dataclass, field


@dataclass
class Defect:
    length: float                                   # Defect length in mm
    elevation: float                                # Defect elevation in m
    width: float = None                             # Defect width in mm
    depth: float = None                             # Defect depth in mm
    relative_depth: float = None                    # Relative defect depth as measured
    relative_depth_with_uncertainty: float = None   # Relative defect depth accounting for measurement uncertainty

    length_correction_factor: float = field(init=False)

    def __post_init__(self):
        if not (self.depth or self.relative_depth):
            raise ValueError('Either depth or relative depth must be provided')

    def complete_dimensions(self, wall_thickness):
        if not self.depth:
            self.depth = self.relative_depth * wall_thickness
        if not self.relative_depth:
            self.relative_depth = self.depth / wall_thickness

    def calculate_d_t_adjusted(self, epsilon_d, stdev):
        """
        Calculate (d/t)*
        Args:
            epsilon_d:
            stdev:

        Returns:

        """
        self.relative_depth_with_uncertainty = self.relative_depth + epsilon_d * stdev

    def generate_length_correction_factor(self, d_nominal, t):
        """
        Generate the length correction factor of the defect
        Args:
            d_nominal: Nominal outside diameter (mm)
            t: Nominal pipe wall thickness (mm)

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
