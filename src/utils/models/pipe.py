import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from loguru import logger

from src.utils.calculations.defect_calculations import (calculate_max_defect_depth_longitudinal,
                                                        calculate_max_defect_depth_longitudinal_with_stress,
                                                        calculate_maximum_defect_length, calculate_combined_length,
                                                        calculate_combined_depth, verify_interaction)
from src.utils.calculations.pressure_calculations import (calculate_pressure_resistance_longitudinal_defect,
                                                          calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
from src.utils.calculations.statistical_calculations import (calculate_std_dev, calculate_partial_safety_factors,
                                                             calculate_usage_factors)
from .material import MaterialProperties
from .defect import Defect
from .environment import Environment
from .factors import Factors


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
    maximum_allowable_defect_depth: list[pd.DataFrame] = field(default_factory=list)
    remaining_life: float = None


class Pipe:
    def __init__(
            self,
            config: dict
    ):
        self.config = config
        self.defect = None
        self.defects = []
        self.environment = None
        self.loading = None
        self.properties = Properties()

        logger.debug("Initialising pipe")
        logger.debug(f"Pipe dimensions: D={self.config['outside_diameter']} | t={self.config['wall_thickness']}")
        self.dimensions = PipeDimensions(self.config['outside_diameter'], self.config['wall_thickness'])
        alpha_u = self.config.get('alpha_u', 0.96)
        logger.debug(
            f"Material properties: alpha_u={alpha_u} | temperature={self.config['design_temperature']} | smts={self.config.get('smts')} | smys={self.config.get('smys')}")
        self.material_properties = MaterialProperties(
            alpha_u=alpha_u,
            temperature=self.config['design_temperature'],
            smts=self.config.get('smts'),
            smys=self.config.get('smys')
        )
        self.design_limits = DesignLimits(self.config['design_pressure'], self.config['design_temperature'],
                                          self.config['incidental_to_design_pressure_ratio'])

        self.factors = Factors(
            safety_class=self.config['safety_class'],
            inspection_method=self.config['measurement_method'],
            measurement_accuracy=self.config['accuracy'],
            confidence_level=self.config['confidence_level'],
            wall_thickness=self.dimensions.wall_thickness
        )

    def __repr__(self):
        return f"Pipe(D={self.dimensions.outside_diameter}, t={self.dimensions.wall_thickness})"

    def add_defect(self, defect: Defect):
        logger.info("Adding defect to pipe")
        if not defect.factors:
            defect.factors = self.factors
        defect.complete_dimensions()
        defect.calculate_d_t_adjusted()
        defect.generate_length_correction_factor(d_nominal=self.dimensions.outside_diameter,
                                                 t=self.dimensions.wall_thickness)

        if not self.defects:
            self.defect = defect
        self.defects.append(defect)

    def add_loading(self, axial_load: float = None, bending_load: float = None, combined_stress: float = None):
        if (axial_load or bending_load) and not combined_stress:
            if axial_load:
                logger.info(f"Adding axial loading to pipe: {axial_load}")
            if bending_load:
                logger.info(f"Adding bending loading to pipe: {bending_load}")
            self.loading = Loading(
                usage_factor=self.factors.xi,
                axial_stress=axial_load,
                bending_stress=bending_load
            )
        elif combined_stress:
            logger.info(f"Adding loading to pipe: {combined_stress}")
            self.loading = Loading(usage_factor=self.factors.xi, loading_stress=combined_stress)

    def set_environment(self, environment):
        logger.info(f"Setting environment")
        self.environment = environment
        self.environment.calculate_external_pressure()
        self.environment.calculate_incidental_pressure(design_limits=self.design_limits)

    def calculate_pressure_resistance(self):
        logger.info('Calculating pressure resistance')

        # Interacting Defects
        if any(defect.position for defect in self.defects):
            logger.info('Defect separation detected, checking for interaction')
            if verify_interaction(
                    defects=self.defects,
                    pipe_diameter=self.dimensions.outside_diameter,
                    pipe_thickness=self.dimensions.wall_thickness
            ):
                logger.info('Defects are interacting, adding combined defect')
                combined_defect = Defect(defects=self.defects)
                self.add_defect(combined_defect)

        for defect in self.defects:
            if not self.loading:
                p_corr = calculate_pressure_resistance_longitudinal_defect(
                    gamma_m=defect.factors.gamma_m,
                    gamma_d=defect.factors.gamma_d,
                    t_nominal=self.dimensions.wall_thickness,
                    defect_length=defect.length,
                    d_nominal=self.dimensions.outside_diameter,
                    relative_defect_depth_with_uncertainty=defect.relative_depth_with_uncertainty,
                    f_u=self.material_properties.f_u,
                    q=defect.length_correction_factor
                )
                logger.info(f'Pressure Resistance: {p_corr}')
                defect.pressure_resistance = p_corr
            else:
                logger.info('Loading detected')
                p_corr_comp = calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
                    gamma_m=defect.factors.gamma_m,
                    gamma_d=defect.factors.gamma_d,
                    t_nominal=self.dimensions.wall_thickness,
                    d_nominal=self.dimensions.outside_diameter,
                    defect_length=defect.length,
                    defect_relative_depth_measured=defect.relative_depth,
                    relative_defect_depth_with_uncertainty=defect.relative_depth_with_uncertainty,
                    defect_width=defect.width,
                    f_u=self.material_properties.f_u,
                    sigma_l=self.loading.loading_stress,
                    phi=self.loading.usage_factor,
                    q=defect.length_correction_factor
                )
                logger.info(f'Pressure Resistance: {p_corr_comp}')
                defect.pressure_resistance = p_corr_comp

        self.properties.pressure_resistance = min(defect.pressure_resistance for defect in self.defects)

    def calculate_effective_pressure(self):
        logger.info("Calculating effective pressure")
        self.properties.effective_pressure = self.environment.incidental_pressure - self.environment.external_pressure

    def calculate_maximum_allowable_defect_depth(self, resolution=0.001):
        """
        Calculate the maximum acceptable relative defect depth for a given defect length
        Returns:
            limits: pd.DataFrame representation of the maximum acceptable relative defect depth at each length
        """
        logger.info(f"Calculating limits for defect depth and length")

        defects = self.defects.copy()

        # Ignore the second defect
        if len(self.defects) > 1:
            del defects[1]

        for index, defect in enumerate(defects):
            rows = []
            if not self.loading:  # With no loading
                for relative_depth in np.arange(0, 1, resolution):
                    if not relative_depth:  # Depth must be greater than 0
                        continue
                    length = calculate_maximum_defect_length(
                        d=self.dimensions.outside_diameter,
                        t=self.dimensions.wall_thickness,
                        gamma_d=defect.factors.gamma_d,
                        gamma_m=defect.factors.gamma_m,
                        f_u=self.material_properties.f_u,
                        p_li=self.environment.incidental_pressure,
                        p_le=self.environment.external_pressure,
                        d_t_meas=relative_depth,
                        epsilon_d=defect.factors.epsilon_d,
                        st_dev=defect.factors.standard_deviation
                    )
                    logger.debug(f'Maximum length for relative depth {relative_depth}: {length}')
                    if all([relative_depth, length]):
                        rows.append(pd.DataFrame({'defect_length': length, 'defect_relative_depth': relative_depth}, index=[0]))
                minimum_values = {'defect_length': 0.0, 'defect_relative_depth': rows[-1]['defect_relative_depth']}
                rows.append(pd.DataFrame(minimum_values, index=[0]))
            else:  # Calculate with loading
                target_pressure = self.properties.effective_pressure
                depth_zeroed = False

                for defect_length in np.arange(0, 1000, resolution * 500):
                    if not depth_zeroed:
                        defect_relative_depth = calculate_max_defect_depth_longitudinal_with_stress(
                            gamma_m=self.factors.gamma_m,
                            gamma_d=self.factors.gamma_d,
                            pipe_thickness=self.dimensions.wall_thickness,
                            defect_length=defect_length,
                            defect_width=self.defect.width,
                            pipe_diameter=self.dimensions.outside_diameter,
                            f_u=self.material_properties.f_u,
                            p_corr_comp=target_pressure,
                            xi=self.factors.xi,
                            sigma_l=self.loading.loading_stress,
                            epsilon_d=self.factors.epsilon_d,
                            st_dev=self.factors.standard_deviation
                        )

                        if defect_relative_depth <= 0:
                            # If defect depth reaches 0, skip calculations for the rest of the lengths
                            depth_zeroed = True
                            defect_relative_depth = 0
                    else:
                        defect_relative_depth = 0
                    logger.debug(f"Max depth for defect length {defect_length} = {defect_relative_depth}")
                    rows.append(pd.DataFrame({'defect_length': defect_length, 'defect_relative_depth': defect_relative_depth}, index=[0]))

            limits = pd.concat(rows).reset_index(drop=True)
            limits = limits.sort_values('defect_length', ignore_index=True)  # Sort by defect length

            self.properties.maximum_allowable_defect_depth.append(limits)

    def estimate_remaining_life(self):
        """
        Estimate the remaining life of the pipe based on the current defect and loading based on 2.9.2

        d_t: defect depth after time T
        l_t: defect length after time T
        T: time
        r_corr: corrosion rate
        r_corr_length: corrosion rate for length
        d_0: initial defect depth
        l_0: initial defect length
        Returns:

        """
        if self.properties.pressure_resistance < self.properties.effective_pressure:
            logger.info('Pipe has already failed, skipping remaining life calculation')
            self.properties.remaining_life = 0
            return False

        d_0 = self.defects[1].relative_depth
        l_0 = self.defects[1].length
        w_0 = self.defects[1].width

        r_corr, r_corr_length = self.calculate_corrosion_rate()

        # Find the point where the defect depth and length reach the maximum allowable defect depth/length
        d_t = d_0
        l_t = l_0
        w_t = w_0
        failure = False
        maximum_allowable_defect_depth = self.properties.maximum_allowable_defect_depth[0]
        filtered_allowable_depth = maximum_allowable_defect_depth[
            (maximum_allowable_defect_depth['defect_length'] > l_t) &
            (maximum_allowable_defect_depth['defect_relative_depth'] > d_t)
        ]

        while not failure:
            d_t += r_corr
            l_t += r_corr_length

            for row in filtered_allowable_depth.itertuples():
                if math.isclose(l_t, row.defect_length, abs_tol=0.5):
                    if d_t >= row.defect_relative_depth:
                        failure = True
                        break
                    else:
                        break

        remaining_life = (d_t - d_0) / r_corr

        self.properties.remaining_life = remaining_life

    def calculate_corrosion_rate(self) -> tuple[float, float]:
        """
        Calculate the corrosion rate of the pipe based on the defects
        Returns:
            corrosion_rate_depth: Depth corrosion rate per day
            corrosion_rate_length: Length corrosion rate per day
        """
        if len(self.defects) < 2:
            raise ValueError("Multiple defects required to calculate corrosion rate")

        # Get defect measurements for first defect
        d_0 = self.defects[0].relative_depth
        l_0 = self.defects[0].length
        w_0 = self.defects[0].width
        ts_0 = self.defects[0].measurement_timestamp

        # Get defect measurements for second defect
        d_1 = self.defects[1].relative_depth
        l_1 = self.defects[1].length
        w_1 = self.defects[1].width
        ts_1 = self.defects[1].measurement_timestamp

        d_ts = ts_1 - ts_0

        if d_ts == 0:
            raise ValueError("Timestamps must be different to calculate corrosion rate")

        r_corr_depth = 86400 * (d_1 - d_0) / d_ts
        r_corr_length = 86400 * (l_1 - l_0) / d_ts
        if all([w_0, w_1]):
            r_corr_width = 86400 * (w_1 - w_0) / d_ts

        return r_corr_depth, r_corr_length


