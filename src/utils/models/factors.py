from dataclasses import dataclass, field

from loguru import logger

from src.utils.calculations.statistical_calculations import calculate_std_dev, calculate_partial_safety_factors, calculate_usage_factors


@dataclass
class Factors:
    safety_class: str
    inspection_method: str
    measurement_accuracy: float
    confidence_level: float
    wall_thickness: float

    standard_deviation: float = None                # Standard deviation of the defect depth measurement
    gamma_m: float = field(init=False)              # Partial safety factor for longitudinal corrosion model projection
    gamma_d: float = field(init=False)              # Partial safety factor for corrosion depth
    epsilon_d: float = field(init=False)            # Factor for defining a fractile value for corrosion depth
    xi: float = field(init=False)                   # Usage factor for longitudinal stress

    def __post_init__(self):
        if not self.standard_deviation:
            logger.debug("Calculating standard deviation")
            self.standard_deviation = calculate_std_dev(
                conf=self.confidence_level,
                acc=self.measurement_accuracy,
                measurement_method=self.inspection_method,
                t=self.wall_thickness
            )
        # self.__delattr__('wall_thickness')

        logger.debug("Calculating partial safety factors")
        safety_factors = calculate_partial_safety_factors(self.safety_class, self.inspection_method,
                                                          self.standard_deviation)
        self.gamma_m = safety_factors['gamma_m']
        self.gamma_d = safety_factors['gamma_d']
        self.epsilon_d = safety_factors['epsilon_d']

        logger.debug("Calculating usage factors based off safety class")
        self.xi = calculate_usage_factors(self.safety_class)
