from dataclasses import dataclass, field

import pandas as pd

from . import MaterialProperties, Defect, Environment
from ..calculations.statistical_calculations import calculate_std_dev, calculate_partial_safety_factors, calculate_usage_factors
from ..calculations.pressure_calculations import (calculate_pressure_resistance_long_defect,
                                                  calculate_pressure_resistance_long_defect_w_compressive,
                                                  calculate_max_defect_depth, calculate_maximum_defect_depth)
from ..calculations.stress_calculations import calculate_nominal_longitudinal_stress


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
    incidental_to_design_pressure_ratio: float


@dataclass
class MeasurementFactors:
    accuracy: float
    measurement_method: str
    # accuracy_relative: float
    # accuracy_absolute: float
    confidence_level: float
    wall_thickness: float
    standard_deviation: float = field(init=False)

    def __post_init__(self):
        self.standard_deviation = calculate_std_dev(
            conf=self.confidence_level,
            acc=self.accuracy,
            measurement_method=self.measurement_method,
            # acc_rel=self.accuracy_relative,
            # acc_abs=self.accuracy_absolute,
            t=self.wall_thickness
        )


@dataclass
class SafetyFactors:
    safety_class: str
    inspection_method: str
    measurement_accuracy: float
    gamma_m: float = field(init=False)
    gamma_d: float = field(init=False)
    epsilon_d: float = field(init=False)

    def __post_init__(self):
        safety_factors = calculate_partial_safety_factors(self.safety_class, self.inspection_method, self.measurement_accuracy)
        self.gamma_m = safety_factors['gamma_m']
        self.gamma_d = safety_factors['gamma_d']
        self.epsilon_d = safety_factors['epsilon_d']


@dataclass
class UsageFactors:
    safety_class: str
    phi: float = field(init=False)

    def __post_init__(self):
        self.phi = calculate_usage_factors(self.safety_class)


@dataclass
class Loading:
    loading_type: str
    loading_stress: float
    usage_factor: float
    sigma_l: float = field(init=False)

    def __post_init__(self):
        self.sigma_l = self.loading_stress if self.loading_type != 'compressive' else -1 * self.loading_stress


@dataclass
class Properties:
    pressure_resistance: float = None
    effective_pressure: float = None


@dataclass
class Pipe:
    config: dict = field(repr=False)
    dimensions: PipeDimensions = field(init=False)
    material_properties: MaterialProperties = field(init=False)
    design_limits: DesignLimits = field(init=False)
    measurement_factors: MeasurementFactors = field(init=False)
    safety_factors: SafetyFactors = field(init=False)
    defect: Defect = field(init=False)
    loading: Loading = field(init=False)
    environment: Environment = field(init=False)
    properties: Properties = field(default_factory=Properties)

    def __post_init__(self):
        self.dimensions = PipeDimensions(self.config['outside_diameter'], self.config['wall_thickness'])
        self.material_properties = MaterialProperties(
            alpha_u=self.config['alpha_u'],
            temperature=self.config['design_temperature'],
            smts=self.config.get('smts'),
            smys=self.config.get('smys')
        )
        self.design_limits = DesignLimits(self.config['design_pressure'], self.config['design_temperature'], self.config['incidental_to_design_pressure_ratio'])
        self.measurement_factors = MeasurementFactors(
            accuracy=self.config.get('accuracy'),
            measurement_method=self.config.get('measurement_method'),
            confidence_level=self.config['confidence_level'],
            wall_thickness=self.dimensions.wall_thickness
        )
        self.safety_factors = SafetyFactors(
            self.config['safety_class'],
            self.config['measurement_method'],
            self.measurement_factors.standard_deviation
        )

    def add_defect(self, defect):
        self.defect = defect
        self.defect.complete_dimensions(self.dimensions.wall_thickness)
        self.defect.calculate_d_t_adjusted(
            epsilon_d=self.safety_factors.epsilon_d,
            stdev=self.measurement_factors.standard_deviation
        )
        self.defect.generate_length_correction_factor(d_nominal=self.dimensions.outside_diameter,
                                                      t=self.dimensions.wall_thickness)

    def add_loading(self, loading_type, magnitude):
        usage_factor = calculate_usage_factors(self.safety_factors.safety_class)
        self.loading = Loading(loading_type, magnitude, usage_factor)

    def set_environment(self, environment):
        self.environment = environment
        if self.defect:
            self.environment.elevation = self.defect.elevation
            self.environment.calculate_external_pressure()
            self.environment.calculate_incidental_pressure(design_limits=self.design_limits)

    def calculate_pressure_resistance(self):
        if hasattr(self, 'loading'):
            p_corr_comp = calculate_pressure_resistance_long_defect_w_compressive(
                gamma_m=self.safety_factors.gamma_m,
                gamma_d=self.safety_factors.gamma_d,
                t_nominal=self.dimensions.wall_thickness,
                defect_length=self.defect.length,
                defect_relative_depth_measured=self.defect.relative_depth,
                defect_relative_depth_normalised=self.defect.relative_depth_with_uncertainty,
                defect_width=self.defect.width,
                d_nominal=self.dimensions.outside_diameter,
                f_u=self.material_properties.f_u,
                sigma_l=self.loading.sigma_l,
                phi=self.loading.usage_factor
            )
            self.properties.pressure_resistance = p_corr_comp
        else:
            p_corr = calculate_pressure_resistance_long_defect(
                gamma_m=self.safety_factors.gamma_m,
                gamma_d=self.safety_factors.gamma_d,
                t_nominal=self.dimensions.wall_thickness,
                defect_length=self.defect.length,
                d_nominal=self.dimensions.outside_diameter,
                relative_defect_depth_with_uncertainty=self.defect.relative_depth_with_uncertainty,
                f_u=self.material_properties.f_u
            )

            self.properties.pressure_resistance = p_corr

    def calculate_effective_pressure(self):
        self.properties.effective_pressure = self.environment.incidental_pressure - self.environment.external_pressure

    def calculate_acceptable_limits(self, start_length=1, end_length=1000, step=1):
        """
        Calculate the maximum acceptable relative defect depth for a given defect length
        Returns:
            limits: pd.DataFrame representation of the maximum acceptable relative defect depth at each length
        """
        target_pressure = self.environment.incidental_pressure - self.environment.external_pressure

        rows = []
        for defect_length in range(start_length, end_length+1, step):
            if not hasattr(self, 'loading'):
                defect_depth = calculate_max_defect_depth(
                    gamma_m=self.safety_factors.gamma_m,
                    gamma_d=self.safety_factors.gamma_d,
                    t_nominal=self.dimensions.wall_thickness,
                    defect_length=defect_length,
                    d_nominal=self.dimensions.outside_diameter,
                    f_u=self.material_properties.f_u,
                    p_corr=target_pressure
                )
            else:
                defect_depth = 0.85
            # defect_depth = calculate_maximum_defect_depth(
            #     gamma_d=self.safety_factors.gamma_d,
            #     epsilon_d=self.safety_factors.epsilon_d,
            #     std_dev=self.measurement_factors.standard_deviation
            # )
            rows.append(pd.DataFrame({'defect_length': defect_length, 'defect_depth': defect_depth}, index=[0]))
        limits = pd.concat(rows).reset_index(drop=True)
        return limits
