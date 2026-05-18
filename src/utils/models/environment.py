from dataclasses import dataclass, field

_GRAVITY = 9.81           # m/s²
_PA_TO_MPA = 1_000_000
_BAR_TO_MPA = 0.1


@dataclass
class Environment:
    seawater_density: float
    containment_density: float
    elevation_reference: float
    elevation: float
    external_pressure: float = field(init=False)
    incidental_pressure: float = field(init=False)

    def calculate_external_pressure(self):
        self.external_pressure = (-1 * self.seawater_density * _GRAVITY * self.elevation) / _PA_TO_MPA

    def calculate_incidental_pressure(self, design_limits):
        self.incidental_pressure = (_BAR_TO_MPA * design_limits.design_pressure * design_limits.incidental_to_design_pressure_ratio
                                    + (self.containment_density * _GRAVITY * (self.elevation_reference - self.elevation)) / _PA_TO_MPA)
