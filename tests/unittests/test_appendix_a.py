"""
Regression tests against the worked examples of DNVGL-RP-F101 Appendix A.1.

Example 1 (relative depth measurements, p.68) is covered by
test_pressure_calculations.test_calculate_pressure_resistance; this module covers the
absolute measurement and superimposed compressive stress examples.

The partial safety factors and standard deviations are taken from the RP's own worked
steps rather than recomputed, so the tests pin the equations to the published answers.
Note that the RP quotes StD[d/t] to three decimals and gamma_d to two, so the pressure
resistance it publishes is rounded; the tolerances below absorb that.
"""
import pytest

from src.utils.calculations.pressure_calculations import (
    calculate_pressure_resistance_longitudinal_defect,
    calculate_pressure_resistance_longitudinal_defect_w_compressive_load)
from src.utils.calculations.statistical_calculations import calculate_inv_cumulative_dist
from src.utils.models.defect import Defect
from src.utils.models.environment import Environment
from src.utils.models.pipe import DesignLimits, Pipe, PipeConfig


def _environment(elevation, containment_density, ratio, design_pressure):
    env = Environment(seawater_density=1025, containment_density=containment_density,
                      elevation_reference=30, elevation=elevation)
    env.calculate_external_pressure()
    env.calculate_incidental_pressure(DesignLimits(design_pressure, 75, ratio))
    return env


class TestExample2AbsoluteMeasurement:
    """A.1 Example 2 (p.69): isolated defect, absolute depth measurement."""

    def test_effective_pressure(self):
        # "The value of local incidental pressure minus local external pressure is 149.4 bar"
        env = _environment(elevation=-200, containment_density=200, ratio=1.1, design_pressure=150)
        assert env.incidental_pressure * 10 == pytest.approx(169.51, abs=0.01)
        assert env.external_pressure * 10 == pytest.approx(20.11, abs=0.01)
        assert (env.incidental_pressure - env.external_pressure) * 10 == pytest.approx(149.4, abs=0.01)

    def test_pressure_resistance(self):
        # RP: StD[d/t] = 0.058, gamma_m = 0.88, d/t = 4.8/19.1, "pressure resistance (185.5 bar)"
        std_dev = 0.058
        gamma_d = 1.0 + 4.6 * std_dev - 13.9 * std_dev ** 2
        epsilon_d = -1.33 + 37.5 * std_dev - 104.2 * std_dev ** 2
        d_t_star = 4.8 / 19.1 + epsilon_d * std_dev

        p_corr = calculate_pressure_resistance_longitudinal_defect(
            gamma_m=0.88, gamma_d=gamma_d, t_nominal=19.1, defect_length=200,
            d_nominal=812.8, relative_defect_depth_with_uncertainty=d_t_star,
            f_u=(530.9 - 15) * 0.96)

        assert p_corr * 10 == pytest.approx(185.5, abs=0.5)

    def test_end_to_end_through_the_models(self):
        """The same case built from model objects, to cover the wiring as well."""
        pipe = Pipe(config=PipeConfig(
            outside_diameter=812.8, wall_thickness=19.1, smts=530.9,
            design_pressure=150, design_temperature=75,
            incidental_to_design_pressure_ratio=1.1, accuracy=1.0, confidence_level=0.8,
            safety_class='medium', measurement_method='absolute'))
        pipe.add_defect(Defect(length=200, depth=4.8))
        pipe.set_environment(_environment(elevation=-200, containment_density=200,
                                          ratio=1.1, design_pressure=150))
        pipe.analyze()

        assert pipe.properties.effective_pressure * 10 == pytest.approx(149.4, abs=0.01)
        assert pipe.properties.pressure_resistance * 10 == pytest.approx(185.5, abs=0.6)


class TestExample3CompressiveStress:
    """A.1 Example 3 (p.71): longitudinal defect with superimposed compressive stress."""

    def test_effective_pressure(self):
        # "The value of local incidental pressure minus local external pressure is 142.5 bar"
        env = _environment(elevation=-100, containment_density=200, ratio=1.0, design_pressure=150)
        assert (env.incidental_pressure - env.external_pressure) * 10 == pytest.approx(142.5, abs=0.01)

    def test_pressure_resistance_with_compressive_stress(self):
        # RP: gamma_m 0.85, gamma_d 1.28, epsilon_d 1.0, xi 0.85, f_u,temp 30,
        # "pressure resistance under internal pressure corrected ... is 34.8 bar"
        p_corr_comp = calculate_pressure_resistance_longitudinal_defect_w_compressive_load(
            gamma_m=0.85, gamma_d=1.28, t_nominal=14.5, d_nominal=219.0,
            defect_length=200, defect_width=100,
            defect_relative_depth_measured=0.62,
            relative_defect_depth_with_uncertainty=0.62 + 1.0 * 0.08,
            f_u=(455.1 - 30) * 0.96, sigma_l=-200.0, phi=0.85)

        assert p_corr_comp * 10 == pytest.approx(34.8, abs=0.1)

    def test_end_to_end_through_the_models(self):
        # The quoted accuracy is chosen so that the derived StD[d/t] equals the RP's
        # tabulated 0.08, otherwise the model derives 0.0780 from a quoted 10% and the
        # resistance comes out ~10% higher than the published value.
        accuracy = 0.08 * calculate_inv_cumulative_dist(0.5 + 0.8 / 2)
        pipe = Pipe(config=PipeConfig(
            outside_diameter=219.0, wall_thickness=14.5, smts=455.1,
            design_pressure=150, design_temperature=100,
            incidental_to_design_pressure_ratio=1.0, accuracy=accuracy, confidence_level=0.8,
            safety_class='medium', measurement_method='relative'))
        pipe.add_defect(Defect(length=200, width=100, relative_depth=0.62))
        pipe.add_loading(combined_stress=-200)
        pipe.set_environment(_environment(elevation=-100, containment_density=200,
                                          ratio=1.0, design_pressure=150))
        pipe.analyze()

        assert pipe.factors.standard_deviation == pytest.approx(0.08, abs=1e-9)
        assert pipe.properties.effective_pressure * 10 == pytest.approx(142.5, abs=0.01)
        assert pipe.properties.pressure_resistance * 10 == pytest.approx(34.8, abs=0.6)
        # Higher than the resistance, so the defect is not acceptable (as the RP states)
        assert pipe.properties.pressure_resistance < pipe.properties.effective_pressure
