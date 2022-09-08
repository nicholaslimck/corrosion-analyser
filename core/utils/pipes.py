from dataclasses import dataclass
from core.calculations.material_calculations import calculate_strength


@dataclass
class Pipe:
    outside_diameter: float
    wall_thickness: float
    smts: float
    defect_length: float
    defect_depth: float
    defect_elevation: float
    elevation_reference: float
    seawater_density: float
    containment_density: float
    design_pressure: float
    design_temperature: float
    gamma_inc: float
    alpha_u: float
    gamma_m: float
    gamma_d: float
    epsilon_d: float
    f_u_temp: float

    def __post_init__(self):
        self.f_u = calculate_strength(self.smts, self.f_u_temp, self.alpha_u)
        # self.measured_defect_depth = self.defect_depth * self.epsilon_d *


@dataclass
class Defect:
    length: float
    depth: float
    elevation: float
