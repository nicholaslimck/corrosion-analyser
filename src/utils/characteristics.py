from dataclasses import dataclass
from src.utils.calculations.material_calculations import calculate_strength


@dataclass
class PipeDimensions:
    """
    Pipe Dimensions in mm
    """
    outside_diameter: float
    wall_thickness: float


@dataclass
class MaterialProperties:
    """
    Material properties

    """
    alpha_u: float = 0.96  # Typically 0.96 as stated in Table 2-2
    smts: float = None
    smys: float = None
    f_u_temp: float = None
    f_y_temp: float = None

    def __post_init__(self):
        if self.smys:
            self.f_y = calculate_strength(self.smys, self.f_y_temp, self.alpha_u)
        if self.smts:
            self.f_u = calculate_strength(self.smts, self.f_u_temp, self.alpha_u)


@dataclass
class DesignLimits:
    """
    Design pressure in bar
    Design temperature in Degrees Celsius
    """
    design_pressure: float
    design_temperature: float


@dataclass
class Pipe:
    config: dict

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
        # self.measured_defect_depth = self.defect_depth * self.epsilon_d *


@dataclass
class Defect:
    length: float
    elevation: float
    measurement_tolerance: float
    measurement_confidence_interval: float
    depth: float = None
    relative_depth: float = None

    def __post_init__(self):
        if not (self.depth or self.relative_depth):
            raise ValueError('Either depth or relative depth must be provided')


@dataclass
class Environment:
    seawater_density: float
    containment_density: float


@dataclass
class Loading:
    loading_type: str
    loading_stress: float
