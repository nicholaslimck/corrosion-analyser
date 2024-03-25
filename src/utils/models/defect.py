import math
from datetime import datetime
from dataclasses import dataclass, field

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor,
                                                        calculate_relative_defect_depth_with_inaccuracies)


@dataclass
class Defect:
    length: float                                   # Defect length in mm
    elevation: float                                # Defect elevation in m
    width: float = None                             # Defect width in mm
    depth: float = None                             # Defect depth in mm
    relative_depth: float = None                    # Relative defect depth as measured
    relative_depth_with_uncertainty: float = None   # Relative defect depth accounting for measurement uncertainty

    length_correction_factor: float = field(init=False)
    pressure_resistance: float = field(init=False)
    measurement_timestamp: float = datetime.timestamp(datetime.now())

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
        self.relative_depth_with_uncertainty = calculate_relative_defect_depth_with_inaccuracies(
            self.relative_depth,
            epsilon_d,
            stdev
        )

    def generate_length_correction_factor(self, d_nominal, t):
        """
        Generate the length correction factor of the defect
        Args:
            d_nominal: Nominal outside diameter (mm)
            t: Nominal pipe wall thickness (mm)

        Returns:

        """
        self.length_correction_factor = calculate_length_correction_factor(self.length, d_nominal, t)
