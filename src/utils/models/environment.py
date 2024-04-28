from dataclasses import dataclass, field


@dataclass
class Environment:
    seawater_density: float
    containment_density: float
    elevation_reference: float
    elevation: float
    external_pressure: float = field(init=False)
    incidental_pressure: float = field(init=False)

    def calculate_external_pressure(self):
        self.external_pressure = (-1 * self.seawater_density * 9.81 * self.elevation) / 1000000

    def calculate_incidental_pressure(self, design_limits):
        self.incidental_pressure = 0.1*design_limits.design_pressure*design_limits.incidental_to_design_pressure_ratio + (self.containment_density * 9.81*(self.elevation_reference-self.elevation)) / 1000000
