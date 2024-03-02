from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from loguru import logger

from src.utils.calculations.defect_calculations import (calculate_max_defect_depth_longitudinal,
                                                        calculate_max_defect_depth_longitudinal_with_stress,
                                                        calculate_maximum_defect_length)
from src.utils.calculations.pressure_calculations import (calculate_pressure_resistance_longitudinal_defect,
                                                          calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
from src.utils.calculations.statistical_calculations import (calculate_std_dev, calculate_partial_safety_factors,
                                                             calculate_usage_factors)
from . import MaterialProperties, Defect, Environment


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
    """
    Accuracy can be in absolute or relative units
    Confidence percentage in decimal representation
    """
    accuracy: float
    measurement_method: str
    confidence_level: float
    wall_thickness: float
    standard_deviation: float = field(init=False)

    def __post_init__(self):
        logger.debug("Calculating measurement factors")
        self.standard_deviation = calculate_std_dev(
            conf=self.confidence_level,
            acc=self.accuracy,
            measurement_method=self.measurement_method,
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
        logger.debug("Calculating partial safety factors")
        safety_factors = calculate_partial_safety_factors(self.safety_class, self.inspection_method,
                                                          self.measurement_accuracy)
        self.gamma_m = safety_factors['gamma_m']
        self.gamma_d = safety_factors['gamma_d']
        self.epsilon_d = safety_factors['epsilon_d']


@dataclass
class UsageFactors:
    safety_class: str
    xi: float = field(init=False)

    def __post_init__(self):
        logger.debug("Calculating usage factors based off safety class")
        self.xi = calculate_usage_factors(self.safety_class)


@dataclass
class Loading:
    usage_factor: float
    axial_stress: float = 0
    bending_stress: float = 0
    loading_stress: float = 0

    def __post_init__(self):
        if self.axial_stress or self.bending_stress and not self.loading_stress:
            self.loading_stress = self.axial_stress + self.bending_stress


@dataclass
class Properties:
    pressure_resistance: float = None
    effective_pressure: float = None
    maximum_allowable_defect_depth: pd.DataFrame = None


@dataclass
class Pipe:
    config: dict = field(repr=False)
    dimensions: PipeDimensions = field(init=False)
    material_properties: MaterialProperties = field(init=False)
    design_limits: DesignLimits = field(init=False)
    measurement_factors: MeasurementFactors = field(init=False)
    safety_factors: SafetyFactors = field(init=False)
    usage_factors: UsageFactors = field(init=False)
    defect: Defect = field(init=False)
    loading: Loading = field(init=False)
    environment: Environment = field(init=False)
    properties: Properties = field(default_factory=Properties)

    def __post_init__(self):
        logger.debug("Initialising pipe")
        logger.debug(f"Pipe dimensions: D={self.config['outside_diameter']} | T={self.config['wall_thickness']}")
        self.dimensions = PipeDimensions(self.config['outside_diameter'], self.config['wall_thickness'])
        alpha_u = self.config.get('alpha_u', 0.96)
        logger.debug(f"Material properties: alpha_u={alpha_u} | temperature={self.config['design_temperature']} | smts={self.config.get('smts')} | smys={self.config.get('smys')}")
        self.material_properties = MaterialProperties(
            alpha_u=alpha_u,
            temperature=self.config['design_temperature'],
            smts=self.config.get('smts'),
            smys=self.config.get('smys')
        )
        self.design_limits = DesignLimits(self.config['design_pressure'], self.config['design_temperature'],
                                          self.config['incidental_to_design_pressure_ratio'])
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
        self.usage_factors = UsageFactors(
            self.config['safety_class']
        )

    def add_defect(self, defect: Defect):
        logger.info("Adding defect to pipe")
        self.defect = defect
        self.defect.complete_dimensions(self.dimensions.wall_thickness)
        self.defect.calculate_d_t_adjusted(
            epsilon_d=self.safety_factors.epsilon_d,
            stdev=self.measurement_factors.standard_deviation
        )
        self.defect.generate_length_correction_factor(d_nominal=self.dimensions.outside_diameter,
                                                      t=self.dimensions.wall_thickness)

    def add_loading(self, axial_load: float = None, bending_load: float = None, combined_stress: float = None):
        if (axial_load or bending_load) and not combined_stress:
            if axial_load:
                logger.info(f"Adding axial loading to pipe: {axial_load}")
            if bending_load:
                logger.info(f"Adding bending loading to pipe: {bending_load}")
            self.loading = Loading(
                usage_factor=self.usage_factors.xi,
                axial_stress=axial_load,
                bending_stress=bending_load
            )
        elif combined_stress:
            logger.info(f"Adding loading to pipe: {combined_stress}")
            self.loading = Loading(usage_factor=self.usage_factors.xi, loading_stress=combined_stress)

    def set_environment(self, environment):
        logger.info(f"Setting environment")
        self.environment = environment
        if self.defect:
            self.environment.elevation = self.defect.elevation
            self.environment.calculate_external_pressure()
            self.environment.calculate_incidental_pressure(design_limits=self.design_limits)

    def calculate_pressure_resistance(self):
        logger.info('Calculating pressure resistance')
        if hasattr(self, 'loading'):
            logger.info('Loading detected')
            p_corr_comp = calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
                gamma_m=self.safety_factors.gamma_m,
                gamma_d=self.safety_factors.gamma_d,
                t_nominal=self.dimensions.wall_thickness,
                d_nominal=self.dimensions.outside_diameter,
                defect_length=self.defect.length,
                defect_relative_depth_measured=self.defect.relative_depth,
                relative_defect_depth_with_uncertainty=self.defect.relative_depth_with_uncertainty,
                defect_width=self.defect.width,
                f_u=self.material_properties.f_u,
                sigma_l=self.loading.loading_stress,
                phi=self.loading.usage_factor,
                q=self.defect.length_correction_factor
            )
            logger.info(f'Pressure Resistance: {p_corr_comp}')
            self.properties.pressure_resistance = p_corr_comp
        else:
            p_corr = calculate_pressure_resistance_longitudinal_defect(
                gamma_m=self.safety_factors.gamma_m,
                gamma_d=self.safety_factors.gamma_d,
                t_nominal=self.dimensions.wall_thickness,
                defect_length=self.defect.length,
                d_nominal=self.dimensions.outside_diameter,
                relative_defect_depth_with_uncertainty=self.defect.relative_depth_with_uncertainty,
                f_u=self.material_properties.f_u,
                q=self.defect.length_correction_factor
            )
            logger.info(f'Pressure Resistance: {p_corr}')
            self.properties.pressure_resistance = p_corr

    def calculate_effective_pressure(self):
        logger.info("Calculating effective pressure")
        self.properties.effective_pressure = self.environment.incidental_pressure - self.environment.external_pressure

    def calculate_maximum_allowable_defect_depth(self, resolution=0.001):
        """
        Calculate the maximum acceptable relative defect depth for a given defect depth
        Returns:
            limits: pd.DataFrame representation of the maximum acceptable relative defect depth at each length
        """
        logger.info(f"Calculating limits for defect depth and length")
        rows = []
        if not hasattr(self, 'loading'):  # With no loading
            for relative_depth in np.arange(0, 1, resolution):
                if not relative_depth:  # Depth must be greater than 0
                    continue
                length = calculate_maximum_defect_length(
                    d=self.dimensions.outside_diameter,
                    t=self.dimensions.wall_thickness,
                    gamma_d=self.safety_factors.gamma_d,
                    gamma_m=self.safety_factors.gamma_m,
                    f_u=self.material_properties.f_u,
                    p_li=self.environment.incidental_pressure,
                    p_le=self.environment.external_pressure,
                    d_t_meas=relative_depth,
                    epsilon_d=self.safety_factors.epsilon_d,
                    st_dev=self.measurement_factors.standard_deviation
                )
                logger.debug(f'Maximum length for relative depth {relative_depth}: {length}')
                if all([relative_depth, length]):
                    rows.append(pd.DataFrame({'defect_length': length, 'defect_depth': relative_depth}, index=[0]))
            minimum_values = {'defect_length': 0.0, 'defect_depth': rows[-1]['defect_depth']}
            rows.append(pd.DataFrame(minimum_values, index=[0]))
        else:  # Calculate with loading
            target_pressure = self.properties.effective_pressure
            depth_zeroed = False

            for defect_length in np.arange(0, 1000, resolution*500):
                if not depth_zeroed:
                    defect_depth = calculate_max_defect_depth_longitudinal_with_stress(
                                gamma_m=self.safety_factors.gamma_m,
                                gamma_d=self.safety_factors.gamma_d,
                                pipe_thickness=self.dimensions.wall_thickness,
                                defect_length=defect_length,
                                defect_width=self.defect.width,
                                pipe_diameter=self.dimensions.outside_diameter,
                                f_u=self.material_properties.f_u,
                                p_corr_comp=target_pressure,
                                xi=self.usage_factors.xi,
                                sigma_l=self.loading.loading_stress,
                                epsilon_d=self.safety_factors.epsilon_d,
                                st_dev=self.measurement_factors.standard_deviation
                            )

                    if defect_depth <= 0:
                        # If defect depth reaches 0, skip calculations for the rest of the lengths
                        depth_zeroed = True
                        defect_depth = 0
                else:
                    defect_depth = 0
                logger.debug(f"Max depth for defect length {defect_length} = {defect_depth}")
                rows.append(pd.DataFrame({'defect_length': defect_length, 'defect_depth': defect_depth}, index=[0]))

        limits = pd.concat(rows).reset_index(drop=True)
        limits = limits.sort_values('defect_length', ignore_index=True)  # Sort by defect length

        self.properties.maximum_allowable_defect_depth = limits
