from dataclasses import dataclass, field

from . import MaterialProperties, Defect
from ..calculations.statistical_calculations import calculate_std_dev, calculate_partial_safety_factors
from ..calculations.pressure_calculations import calculate_pressure_resistance


@dataclass
class PipeDimensions:
    """
    Pipe Dimensions in mm
    """
    outside_diameter: float
    wall_thickness: float


@dataclass
class DesignLimits:
    """
    Design pressure in bar
    Design temperature in Degrees Celsius
    """
    design_pressure: float
    design_temperature: float


@dataclass
class MeasurementFactors:
    tolerance: float
    confidence_level: float
    standard_deviation: float = field(init=False)

    def __post_init__(self):
        self.standard_deviation = calculate_std_dev(
            acc=self.tolerance,
            conf=self.confidence_level
        )


@dataclass
class SafetyFactors:
    safety_class: str
    measurement_accuracy: float
    gamma_m: float = field(init=False)
    gamma_d: float = field(init=False)
    epsilon_d: float = field(init=False)

    def __post_init__(self):
        safety_factors = calculate_partial_safety_factors(self.safety_class, 'relative', self.measurement_accuracy)
        self.gamma_m = safety_factors['gamma_m']
        self.gamma_d = safety_factors['gamma_d']
        self.epsilon_d = safety_factors['epsilon_d']


@dataclass
class Loading:
    loading_type: str
    loading_stress: float


@dataclass
class Pipe:
    config: dict
    dimensions: PipeDimensions = field(init=False)
    material_properties: MaterialProperties = field(init=False)
    design_limits: DesignLimits = field(init=False)
    defect: Defect = field(init=False)

    def __post_init__(self):
        self.dimensions = PipeDimensions(self.config['outside_diameter'], self.config['wall_thickness'])
        self.material_properties = MaterialProperties(
            self.config['alpha_u'],
            self.config.get('smts'),
            self.config.get('smys'),
            self.config.get('f_u_temp'),
            self.config.get('f_y_temp')
        )
        self.design_limits = DesignLimits(self.config['design_pressure'], self.config['design_temperature'])
        self.measurement_factors = MeasurementFactors(self.config['accuracy_relative'], self.config['confidence_level'])
        self.safety_factors = SafetyFactors(self.config['safety_class'], self.measurement_factors.standard_deviation)

    def add_defect(self, defect):
        self.defect = defect
        self.defect.calculate_d_t(
            epsilon_d=self.safety_factors.epsilon_d,
            stdev=self.measurement_factors.standard_deviation
        )
        self.defect.generate_length_correction_factor(d_nominal=self.dimensions.outside_diameter,
                                                      t=self.dimensions.wall_thickness)

    def calculate_pressure_resistance(self):
        p_corr = calculate_pressure_resistance(
            gamma_m=self.safety_factors.gamma_m,
            gamma_d=self.safety_factors.gamma_d,
            t_nominal=self.dimensions.wall_thickness,
            defect_length=self.defect.length,
            d_nominal=self.dimensions.outside_diameter,
            defect_depth=self.defect.depth,
            f_u=self.material_properties.f_u
        )
        return p_corr
