from dataclasses import dataclass, field

from .material import MaterialProperties
from .defect import Defect
from ..calculations.misc_calculations import calculate_std_dev


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

    def add_defect(self, defect):
        self.defect = defect
        self.defect.calculate_d_t(
            epsilon_d=self.config['epsilon_d']['value'],
            stdev=calculate_std_dev(acc_rel=self.config['acc_rel']['value'],
                                    conf=self.config['conf']['value'])
        )
        self.defect.generate_length_correction_factor(d_nominal=self.dimensions.outside_diameter,
                                                      t=self.dimensions.wall_thickness)
