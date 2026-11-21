from dataclasses import dataclass, field
from loguru import logger

from src.utils.calculations.defect_calculations import (calculate_length_correction_factor,
                                                        calculate_relative_defect_depth_with_inaccuracies,
                                                        calculate_combined_length, calculate_combined_depth,
                                                        MAX_MEASURED_RELATIVE_DEPTH)
from src.utils.models.factors import Factors


@dataclass
class Defect:
    length: float = None                            # Defect length in mm
    width: float = None                             # Defect width in mm
    depth: float = None                             # Defect depth in mm
    relative_depth: float = None                    # Relative defect depth as measured
    relative_depth_with_uncertainty: float = None   # Relative defect depth accounting for measurement uncertainty

    defects: list = field(default_factory=list)     # List of defects to form a combined defect

    factors: Factors = None                         # Factors object
    length_correction_factor: float = field(init=False)
    pressure_resistance: float = field(init=False)
    measurement_timestamp: float = None
    position: float = 0                             # Position of the defect along the pipeline

    def __post_init__(self):
        if not (self.defects or self.length):
            raise ValueError('Either defects or length must be provided')
        if self.length and self.depth is None and self.relative_depth is None:
            raise ValueError('Either depth or relative depth must be provided')
        if self.length is not None and self.length <= 0:
            raise ValueError('Defect length must be positive')
        if self.depth is not None and self.depth < 0:
            raise ValueError('Defect depth cannot be negative')
        if self.relative_depth is not None and not (0 < self.relative_depth < 1):
            raise ValueError('Relative defect depth must be between 0 and 1 (exclusive)')
        if self.defects:
            logger.info('Calculating combined defect dimensions')
            inspection_method = self.defects[0].factors.inspection_method
            combined_length = calculate_combined_length(self.defects)
            combined_depth = calculate_combined_depth(self.defects, inspection_method)
            combined_stdev = (
                sum([defect.length * defect.factors.standard_deviation for defect in self.defects])
                / combined_length)
            factors = Factors(
                safety_class=self.defects[0].factors.safety_class,
                inspection_method=self.defects[0].factors.inspection_method,
                measurement_accuracy=self.defects[0].factors.measurement_accuracy,
                confidence_level=self.defects[0].factors.confidence_level,
                wall_thickness=self.defects[0].factors.wall_thickness,
                standard_deviation=combined_stdev
            )

            self.length = combined_length
            if inspection_method == 'relative':
                self.relative_depth = combined_depth
            else:
                self.depth = combined_depth
            self.factors = factors

        self.validate_measured_depth()

    def validate_measured_depth(self):
        """
        Enforce the acceptance criteria on defect depth, DNVGL-RP-F101 Section 3.7.2.1:
        measured defect depths shall not exceed 85% of the wall thickness.

        Raises:
            ValueError: if the measured relative defect depth exceeds 0.85
        """
        if self.relative_depth is None:
            return
        if self.relative_depth > MAX_MEASURED_RELATIVE_DEPTH:
            raise ValueError(
                f'Measured defect depth of {self.relative_depth:.3f}t exceeds the maximum '
                f'of {MAX_MEASURED_RELATIVE_DEPTH}t permitted by DNV-RP-F101 3.7.2.1 '
                f'(minimum remaining wall thickness is 15% of t)'
            )

    def complete_dimensions(self):
        if self.depth is None:
            self.depth = self.relative_depth * self.factors.wall_thickness
        if self.relative_depth is None:
            self.relative_depth = self.depth / self.factors.wall_thickness
        self.validate_measured_depth()

    def calculate_d_t_adjusted(self):
        """
        Calculate (d/t)*
        """
        self.relative_depth_with_uncertainty = calculate_relative_defect_depth_with_inaccuracies(
            self.relative_depth,
            self.factors.epsilon_d,
            self.factors.standard_deviation
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
