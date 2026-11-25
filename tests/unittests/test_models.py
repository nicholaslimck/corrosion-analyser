import pandas as pd
import numpy as np
import pytest

from src.utils.models.pipe import Pipe, PipeConfig, Loading, DesignLimits
from src.utils.models.defect import Defect
from src.utils.models.material import MaterialProperties, estimate_de_rating_stress_or_strength
from src.utils.models.environment import Environment
from src.utils.models.factors import Factors
from src.utils.models.parameter import Parameter
from src.utils.calculations.pressure_calculations import calculate_pressure_resistance_longitudinal_defect


# --- MaterialProperties ---

class TestMaterialProperties:
    def test_strength_calculation(self):
        mat = MaterialProperties(temperature=75, smts=530.9)
        # f_u_temp at 75C = 0.6*75 - 30 = 15
        # f_u = (530.9 - 15) * 0.96 = 495.264
        assert mat.f_u == pytest.approx(495.264)
        assert mat.f_u_temp == pytest.approx(15.0)

    def test_smys_calculation(self):
        mat = MaterialProperties(temperature=75, smys=450.0)
        assert mat.f_y == pytest.approx((450.0 - 15.0) * 0.96)

    def test_de_rating_boundary_50(self):
        assert estimate_de_rating_stress_or_strength(50.001) == pytest.approx(0.6 * 50.001 - 30)

    def test_de_rating_at_100(self):
        assert estimate_de_rating_stress_or_strength(100) == pytest.approx(0.6 * 100 - 30)

    def test_de_rating_above_100(self):
        assert estimate_de_rating_stress_or_strength(150) == pytest.approx(0.4 * 150 - 10)

    def test_de_rating_below_50_raises(self):
        with pytest.raises(ValueError):
            estimate_de_rating_stress_or_strength(25)

    def test_de_rating_above_200_raises(self):
        with pytest.raises(ValueError):
            estimate_de_rating_stress_or_strength(250)


# --- Loading ---

class TestLoading:
    def test_combined_stress_calculated(self):
        loading = Loading(usage_factor=0.85, axial_stress=100, bending_stress=50)
        assert loading.loading_stress == 150

    def test_loading_stress_not_overwritten(self):
        loading = Loading(usage_factor=0.85, axial_stress=100, bending_stress=50, loading_stress=200)
        assert loading.loading_stress == 200

    def test_only_axial_with_loading_stress(self):
        loading = Loading(usage_factor=0.85, axial_stress=100, loading_stress=75)
        assert loading.loading_stress == 75

    def test_zero_stresses(self):
        loading = Loading(usage_factor=0.85)
        assert loading.loading_stress == 0


# --- Parameter ---

class TestParameter:
    def test_with_value_and_unit(self):
        p = Parameter(value=42.0, unit='mm')
        assert p.value == 42.0
        assert p.unit == 'mm'

    def test_without_unit(self):
        p = Parameter(value=100)
        assert p.value == 100
        assert p.unit is None

    def test_int_value(self):
        p = Parameter(value=5, unit='bar')
        assert p.value == 5

    def test_float_value(self):
        p = Parameter(value=3.14, unit='MPa')
        assert p.value == pytest.approx(3.14)


# --- Factors ---

class TestFactors:
    def test_medium_relative(self):
        factors = Factors(
            safety_class='medium',
            inspection_method='relative',
            measurement_accuracy=0.1,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        assert factors.gamma_m == 0.85
        assert factors.xi == 0.85
        assert factors.gamma_d is not None
        assert factors.epsilon_d is not None
        assert factors.standard_deviation is not None

    @pytest.mark.parametrize('safety_class,inspection_method,expected_gamma_m,expected_xi', [
        ('low', 'relative', 0.90, 0.9),
        ('low', 'absolute', 0.94, 0.9),
        ('medium', 'relative', 0.85, 0.85),
        ('medium', 'absolute', 0.88, 0.85),
        ('high', 'relative', 0.80, 0.8),
        ('high', 'absolute', 0.82, 0.8),
        ('very high', 'relative', 0.76, 0.75),
        ('very high', 'absolute', 0.77, 0.75),
    ])
    def test_all_safety_class_combinations(self, safety_class, inspection_method, expected_gamma_m, expected_xi):
        factors = Factors(
            safety_class=safety_class,
            inspection_method=inspection_method,
            measurement_accuracy=0.05,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        assert factors.gamma_m == expected_gamma_m
        assert factors.xi == expected_xi
        assert factors.gamma_d is not None
        assert factors.epsilon_d is not None


# --- Environment ---

class TestEnvironment:
    def test_external_pressure(self):
        env = Environment(
            seawater_density=1025,
            containment_density=200,
            elevation_reference=30,
            elevation=-100
        )
        env.calculate_external_pressure()
        # (-1 * 1025 * 9.81 * -100) / 1e6 = 1.005525
        assert env.external_pressure == pytest.approx(1.005525)

    def test_incidental_pressure(self):
        env = Environment(
            seawater_density=1025,
            containment_density=200,
            elevation_reference=30,
            elevation=-100
        )
        env.calculate_external_pressure()
        design_limits = DesignLimits(
            design_pressure=150,
            design_temperature=75,
            incidental_to_design_pressure_ratio=1.1
        )
        env.calculate_incidental_pressure(design_limits)
        # 0.1 * 150 * 1.1 + (200 * 9.81 * (30 - (-100))) / 1e6
        expected = 0.1 * 150 * 1.1 + (200 * 9.81 * 130) / 1e6
        assert env.incidental_pressure == pytest.approx(expected)


# --- Defect ---

class TestDefect:
    def test_basic_creation(self):
        defect = Defect(length=200, relative_depth=0.25)
        assert defect.length == 200
        assert defect.relative_depth == 0.25

    def test_negative_length_raises(self):
        with pytest.raises(ValueError, match="length must be positive"):
            Defect(length=-10, relative_depth=0.25)

    def test_negative_depth_raises(self):
        with pytest.raises(ValueError, match="depth cannot be negative"):
            Defect(length=200, depth=-5)

    def test_relative_depth_out_of_range_raises(self):
        with pytest.raises(ValueError, match="between 0 and 1"):
            Defect(length=200, relative_depth=1.5)

    def test_measured_depth_above_85_percent_raises(self):
        """DNVGL-RP-F101 3.7.2.1: measured depth shall not exceed 85% of t."""
        with pytest.raises(ValueError, match="85% of the wall thickness|exceeds the maximum"):
            Defect(length=200, relative_depth=0.9)

    def test_measured_depth_above_85_percent_from_absolute_depth_raises(self):
        factors = Factors(
            safety_class='medium',
            inspection_method='absolute',
            measurement_accuracy=0.5,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        defect = Defect(length=200, depth=17.0, factors=factors)  # 17.0 / 19.1 = 0.89
        with pytest.raises(ValueError, match="exceeds the maximum"):
            defect.complete_dimensions()

    def test_measured_depth_of_exactly_85_percent_is_allowed(self):
        defect = Defect(length=200, relative_depth=0.85)
        assert defect.relative_depth == 0.85

    def test_relative_depth_zero_raises(self):
        with pytest.raises(ValueError):
            Defect(length=200, relative_depth=0)

    def test_no_length_or_defects_raises(self):
        with pytest.raises(ValueError, match="Either defects or length"):
            Defect(relative_depth=0.25)

    def test_no_depth_raises(self):
        with pytest.raises(ValueError, match="Either depth or relative depth"):
            Defect(length=200)

    def test_complete_dimensions_from_relative(self):
        factors = Factors(
            safety_class='medium',
            inspection_method='relative',
            measurement_accuracy=0.1,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        defect = Defect(length=200, relative_depth=0.25, factors=factors)
        defect.complete_dimensions()
        assert defect.depth == pytest.approx(0.25 * 19.1)

    def test_complete_dimensions_from_absolute_depth(self):
        factors = Factors(
            safety_class='medium',
            inspection_method='relative',
            measurement_accuracy=0.1,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        defect = Defect(length=200, depth=4.775, factors=factors)
        defect.complete_dimensions()
        assert defect.relative_depth == pytest.approx(4.775 / 19.1)

    def test_combined_defect_creation(self):
        factors = Factors(
            safety_class='medium',
            inspection_method='relative',
            measurement_accuracy=0.1,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        d1 = Defect(length=100, relative_depth=0.3, position=0, factors=factors)
        d2 = Defect(length=80, relative_depth=0.5, position=50, factors=factors)
        combined = Defect(defects=[d1, d2])
        # L1 + L2 + (pos2 - pos1) = 100 + 80 + 50 = 230
        assert combined.length == pytest.approx(230)
        # Weighted average over combined length: (0.3*100 + 0.5*80) / 230
        assert combined.relative_depth == pytest.approx((0.3 * 100 + 0.5 * 80) / 230)
        assert combined.factors is not None

    def test_combined_defect_creation_absolute(self):
        # Covers the absolute-method branch: self.depth = combined_depth
        factors = Factors(
            safety_class='medium',
            inspection_method='absolute',
            measurement_accuracy=0.05,
            confidence_level=0.8,
            wall_thickness=19.1
        )
        d1 = Defect(length=100, depth=5.0, position=0, factors=factors)
        d2 = Defect(length=80, depth=8.0, position=50, factors=factors)
        combined = Defect(defects=[d1, d2])
        assert combined.length == pytest.approx(230)
        assert combined.depth == pytest.approx((5.0 * 100 + 8.0 * 80) / 230)


# --- Pipe ---

class TestPipeConfig:
    @pytest.fixture
    def valid_config(self):
        return PipeConfig(
            outside_diameter=812.8,
            wall_thickness=19.1,
            smts=530.9,
            design_pressure=150,
            design_temperature=75,
            incidental_to_design_pressure_ratio=1.1,
            accuracy=0.1,
            confidence_level=0.8,
            safety_class='medium',
            measurement_method='relative'
        )

    def test_zero_diameter_raises(self):
        with pytest.raises(ValueError, match="Outside diameter must be positive"):
            PipeConfig(outside_diameter=0, wall_thickness=19.1, design_pressure=150,
                       design_temperature=75, incidental_to_design_pressure_ratio=1.1,
                       accuracy=0.1, confidence_level=0.8, safety_class='medium',
                       measurement_method='relative')

    def test_negative_diameter_raises(self):
        with pytest.raises(ValueError, match="Outside diameter must be positive"):
            PipeConfig(outside_diameter=-100, wall_thickness=19.1, design_pressure=150,
                       design_temperature=75, incidental_to_design_pressure_ratio=1.1,
                       accuracy=0.1, confidence_level=0.8, safety_class='medium',
                       measurement_method='relative')

    def test_zero_wall_thickness_raises(self):
        with pytest.raises(ValueError, match="Wall thickness must be positive"):
            PipeConfig(outside_diameter=812.8, wall_thickness=0, design_pressure=150,
                       design_temperature=75, incidental_to_design_pressure_ratio=1.1,
                       accuracy=0.1, confidence_level=0.8, safety_class='medium',
                       measurement_method='relative')

    def test_wall_thickness_too_large_raises(self):
        with pytest.raises(ValueError, match="Wall thickness must be less than half"):
            PipeConfig(outside_diameter=812.8, wall_thickness=500, design_pressure=150,
                       design_temperature=75, incidental_to_design_pressure_ratio=1.1,
                       accuracy=0.1, confidence_level=0.8, safety_class='medium',
                       measurement_method='relative')

    def test_zero_design_pressure_raises(self):
        with pytest.raises(ValueError, match="Design pressure must be positive"):
            PipeConfig(outside_diameter=812.8, wall_thickness=19.1, design_pressure=0,
                       design_temperature=75, incidental_to_design_pressure_ratio=1.1,
                       accuracy=0.1, confidence_level=0.8, safety_class='medium',
                       measurement_method='relative')


class TestPipe:
    @pytest.fixture
    def valid_config(self):
        return PipeConfig(
            outside_diameter=812.8,
            wall_thickness=19.1,
            smts=530.9,
            design_pressure=150,
            design_temperature=75,
            incidental_to_design_pressure_ratio=1.1,
            accuracy=0.1,
            confidence_level=0.8,
            safety_class='medium',
            measurement_method='relative'
        )

    def test_valid_construction(self, valid_config):
        pipe = Pipe(config=valid_config)
        assert pipe.dimensions.outside_diameter == 812.8
        assert pipe.dimensions.wall_thickness == 19.1
        assert pipe.material_properties.f_u is not None
        assert pipe.factors.gamma_m == 0.85

    def test_analyze_no_defects_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=30, elevation=-100)
        pipe.set_environment(env)
        with pytest.raises(ValueError, match="At least one defect"):
            pipe.analyze()

    def test_analyze_no_environment_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        with pytest.raises(ValueError, match="Environment must be set"):
            pipe.analyze()

    def test_estimate_remaining_life_single_defect_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        defect = Defect(length=200, relative_depth=0.25)
        pipe.add_defect(defect)
        with pytest.raises(ValueError, match="Two defect measurements required"):
            pipe.estimate_remaining_life()

    def test_add_defect(self, valid_config):
        pipe = Pipe(config=valid_config)
        defect = Defect(length=200, relative_depth=0.25)
        pipe.add_defect(defect)
        assert pipe.defect is defect
        assert defect.depth == pytest.approx(0.25 * 19.1)
        assert defect.relative_depth_with_uncertainty is not None
        assert defect.length_correction_factor > 1.0

    def test_add_loading_axial_and_bending(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_loading(axial_load=100, bending_load=50)
        assert pipe.loading is not None
        assert pipe.loading.loading_stress == pytest.approx(150)
        assert pipe.loading.usage_factor == pipe.factors.xi

    def test_add_loading_combined_stress(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_loading(combined_stress=200)
        assert pipe.loading.loading_stress == pytest.approx(200)

    def test_set_environment(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        assert pipe.environment is not None
        assert pipe.environment.external_pressure == pytest.approx(1.005525)
        assert pipe.environment.incidental_pressure > 0

    def test_calculate_pressure_resistance(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        defect = Defect(length=200, relative_depth=0.25)
        pipe.add_defect(defect)
        pipe.calculate_pressure_resistance()
        assert pipe.properties.pressure_resistance > 0
        # Round-trip: must match direct calculation with the same factors
        expected = calculate_pressure_resistance_longitudinal_defect(
            gamma_m=pipe.factors.gamma_m,
            gamma_d=pipe.factors.gamma_d,
            t_nominal=pipe.dimensions.wall_thickness,
            defect_length=defect.length,
            d_nominal=pipe.dimensions.outside_diameter,
            relative_defect_depth_with_uncertainty=defect.relative_depth_with_uncertainty,
            f_u=pipe.material_properties.f_u,
            q=defect.length_correction_factor
        )
        assert pipe.properties.pressure_resistance == pytest.approx(expected)

    def test_calculate_pressure_resistance_dnv_example(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=30, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.calculate_pressure_resistance()
        # DNV-RP-F101 Appendix A example A.1 expects ~17.08 MPa
        assert pipe.properties.pressure_resistance == pytest.approx(17.08, rel=1e-2)

    def test_calculate_effective_pressure(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.calculate_effective_pressure()
        expected = env.incidental_pressure - env.external_pressure
        assert pipe.properties.effective_pressure == pytest.approx(expected)

    def test_calculate_effective_pressure_less_than_resistance(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=30, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.calculate_pressure_resistance()
        pipe.calculate_effective_pressure()
        assert pipe.properties.effective_pressure < pipe.properties.pressure_resistance

    def test_calculate_maximum_allowable_defect_depth(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.calculate_maximum_allowable_defect_depth()
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1
        df = pipe.properties.maximum_allowable_defect_depth[0]
        assert 'defect_length' in df.columns
        assert 'defect_relative_depth' in df.columns
        assert len(df) > 0

    def test_calculate_corrosion_rate(self, valid_config):
        pipe = Pipe(config=valid_config)
        # defect2 measured 1 day after defect1, with increased depth and length
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=0))
        pipe.add_defect(Defect(length=220, relative_depth=0.30, measurement_timestamp=86400))
        r_depth, r_length = pipe.calculate_corrosion_rate()
        # 86400 * (0.30 - 0.25) / 86400 = 0.05/day; 86400 * 20 / 86400 = 20 mm/day
        assert r_depth == pytest.approx(0.05)
        assert r_length == pytest.approx(20.0)

    def test_estimate_remaining_life_already_failed(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=0))
        pipe.add_defect(Defect(length=220, relative_depth=0.30, measurement_timestamp=86400))
        pipe.properties.pressure_resistance = 1.0
        pipe.properties.effective_pressure = 20.0
        pipe.estimate_remaining_life()
        assert pipe.properties.remaining_life == 0

    def test_repr(self, valid_config):
        pipe = Pipe(config=valid_config)
        assert repr(pipe) == "Pipe(D=812.8, t=19.1)"

    def test_calculate_pressure_resistance_with_loading(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, width=50, relative_depth=0.25))
        pipe.add_loading(combined_stress=-200)
        pipe.calculate_pressure_resistance()
        assert pipe.properties.pressure_resistance > 0

    def test_calculate_pressure_resistance_with_interacting_defects(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        # separation + lengths = 50 + 100 + 100 = 250 < 5*sqrt(812.8*19.1) ≈ 623 → interact
        d1 = Defect(length=100, relative_depth=0.25, position=0)
        d2 = Defect(length=100, relative_depth=0.30, position=50)
        pipe.add_defect(d1)
        pipe.add_defect(d2)
        pipe.calculate_pressure_resistance()
        # The combined defect is derived, not measured: it stays out of pipe.defects
        assert len(pipe.defects) == 2
        assert pipe.combined_defect is not None
        assert len(pipe.assessment_defects) == 3
        assert pipe.properties.pressure_resistance > 0

    def test_calculate_pressure_resistance_is_repeatable(self, valid_config):
        """Re-running the calculation must not accumulate derived defects."""
        pipe = Pipe(config=valid_config)
        pipe.set_environment(Environment(seawater_density=1025, containment_density=200,
                                         elevation_reference=0, elevation=-100))
        pipe.add_defect(Defect(length=100, relative_depth=0.25, position=0))
        pipe.add_defect(Defect(length=100, relative_depth=0.30, position=50))
        pipe.calculate_pressure_resistance()
        first = pipe.properties.pressure_resistance
        pipe.calculate_pressure_resistance()
        pipe.calculate_pressure_resistance()
        assert len(pipe.defects) == 2
        assert len(pipe.assessment_defects) == 3
        assert pipe.properties.pressure_resistance == pytest.approx(first)

    def _two_inspection_pipe(self, valid_config, length_2=210.0, depth_2=0.26, days=365):
        """Two measurements of the same defect, `days` apart."""
        pipe = Pipe(config=valid_config)
        pipe.set_environment(Environment(seawater_density=1025, containment_density=200,
                                         elevation_reference=0, elevation=-100))
        t0 = 1_600_000_000.0
        pipe.add_defect(Defect(length=200, width=50, relative_depth=0.25, measurement_timestamp=t0))
        pipe.add_defect(Defect(length=length_2, width=50, relative_depth=depth_2,
                               measurement_timestamp=t0 + days * 86400))
        return pipe

    def test_curve_covers_the_later_measurement_when_it_is_longer(self, valid_config):
        """Regression: the curve was sized from the primary defect only, so a
        longer later measurement fell outside the sampled domain and remaining
        life silently became None."""
        pipe = self._two_inspection_pipe(valid_config, length_2=1200.0, depth_2=0.30)
        pipe.add_loading(combined_stress=-50)
        pipe.analyze()

        limits = pipe.properties.maximum_allowable_defect_depth[0]
        assert limits['defect_length'].max() >= 1200.0
        assert pipe.properties.remaining_life is not None

    def test_corrosion_rate_is_order_independent(self, valid_config):
        """Measurements may be added in either order: the rate is derived from the
        dates, not from the order the defects were supplied."""
        pipe = Pipe(config=valid_config)
        t0 = 1_600_000_000.0
        # later measurement added first
        pipe.add_defect(Defect(length=210, relative_depth=0.26,
                               measurement_timestamp=t0 + 365 * 86400))
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=t0))
        r_corr, r_corr_length = pipe.calculate_corrosion_rate()
        assert r_corr == pytest.approx((0.26 - 0.25) / 365)
        assert r_corr_length == pytest.approx((210 - 200) / 365)

    def test_corrosion_rate_from_two_measurements(self, valid_config):
        pipe = self._two_inspection_pipe(valid_config)
        r_corr, r_corr_length = pipe.calculate_corrosion_rate()
        assert r_corr == pytest.approx((0.26 - 0.25) / 365)
        assert r_corr_length == pytest.approx((210 - 200) / 365)

    def test_remaining_life_is_finite_and_consistent(self, valid_config):
        pipe = self._two_inspection_pipe(valid_config)
        pipe.analyze()
        life = pipe.properties.remaining_life
        assert life is not None and life > 0

        # At the reported time the predicted depth must equal the allowable depth
        # for the predicted length, which is what the root find converged on.
        r_corr, r_corr_length = pipe.calculate_corrosion_rate()
        limits = pipe.properties.maximum_allowable_defect_depth[0].sort_values('defect_length')
        predicted = 0.26 + r_corr * life
        allowable = np.interp(210 + r_corr_length * life,
                              limits['defect_length'].to_numpy(float),
                              limits['defect_relative_depth'].to_numpy(float))
        assert predicted == pytest.approx(allowable, abs=1e-6)

    def test_remaining_life_handles_fast_length_growth(self, valid_config):
        """A high length corrosion rate must not stall the calculation."""
        pipe = self._two_inspection_pipe(valid_config, length_2=600.0, depth_2=0.26)
        pipe.analyze()
        assert pipe.properties.remaining_life is not None
        assert pipe.properties.remaining_life >= 0

    def test_remaining_life_zero_when_already_failed(self, valid_config):
        pipe = self._two_inspection_pipe(valid_config)
        pipe.calculate_pressure_resistance()
        pipe.calculate_effective_pressure()
        pipe.properties.pressure_resistance = 1.0
        pipe.properties.effective_pressure = 10.0
        pipe.calculate_maximum_allowable_defect_depth()
        assert pipe.estimate_remaining_life() == 0

    def test_remaining_life_none_when_no_corrosion(self, valid_config):
        pipe = self._two_inspection_pipe(valid_config, length_2=200.0, depth_2=0.25)
        pipe.calculate_pressure_resistance()
        pipe.calculate_effective_pressure()
        pipe.calculate_maximum_allowable_defect_depth()
        assert pipe.estimate_remaining_life() is None

    def test_remaining_life_requires_allowable_depth_curve(self, valid_config):
        pipe = self._two_inspection_pipe(valid_config)
        pipe.properties.pressure_resistance = 20.0
        pipe.properties.effective_pressure = 15.0
        with pytest.raises(ValueError, match="Maximum allowable defect depth"):
            pipe.estimate_remaining_life()

    def test_allowable_depth_curve_covers_long_defects_with_loading(self, valid_config):
        """The curve must extend past the reported defect, not stop at a fixed 1000 mm."""
        pipe = Pipe(config=valid_config)
        pipe.set_environment(Environment(seawater_density=1025, containment_density=200,
                                         elevation_reference=0, elevation=-100))
        pipe.add_defect(Defect(length=1200, width=50, relative_depth=0.25))
        pipe.add_loading(combined_stress=-50)
        pipe.calculate_pressure_resistance()
        pipe.calculate_effective_pressure()
        pipe.calculate_maximum_allowable_defect_depth()
        curve = pipe.properties.maximum_allowable_defect_depth[0]
        assert curve['defect_length'].max() >= 1200

    def test_allowable_depth_curve_is_bounded_without_loading(self, valid_config):
        """The no-loading curve must not run off to tens of metres of length."""
        pipe = Pipe(config=valid_config)
        pipe.set_environment(Environment(seawater_density=1025, containment_density=200,
                                         elevation_reference=0, elevation=-100))
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.calculate_pressure_resistance()
        pipe.calculate_effective_pressure()
        pipe.calculate_maximum_allowable_defect_depth()
        curve = pipe.properties.maximum_allowable_defect_depth[0]
        assert curve['defect_length'].max() <= 1000

    def test_analyze_is_idempotent(self, valid_config):
        """analyze() must reset derived state rather than append to it."""
        pipe = Pipe(config=valid_config)
        pipe.set_environment(Environment(seawater_density=1025, containment_density=200,
                                         elevation_reference=0, elevation=-100))
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.analyze()
        first = pipe.properties.pressure_resistance
        pipe.analyze()
        pipe.analyze()
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1
        assert pipe.properties.pressure_resistance == pytest.approx(first)

    def test_calculate_maximum_allowable_defect_depth_ignores_second_defect(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.add_defect(Defect(length=220, relative_depth=0.30, measurement_timestamp=86400))
        pipe.calculate_maximum_allowable_defect_depth()
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1

    def test_calculate_maximum_allowable_defect_depth_with_loading(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, width=50, relative_depth=0.25))
        pipe.add_loading(combined_stress=-200)
        pipe.calculate_effective_pressure()
        pipe.calculate_maximum_allowable_defect_depth()
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1
        assert len(pipe.properties.maximum_allowable_defect_depth[0]) > 0

    def test_calculate_corrosion_rate_single_defect_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=0))
        with pytest.raises(ValueError, match="Multiple defects"):
            pipe.calculate_corrosion_rate()

    def test_calculate_corrosion_rate_timestamps_too_close_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=0))
        pipe.add_defect(Defect(length=220, relative_depth=0.30, measurement_timestamp=0.5))
        with pytest.raises(ValueError, match="Timestamps must be different"):
            pipe.calculate_corrosion_rate()

    def test_calculate_maximum_allowable_defect_depth_no_valid_rows(self, valid_config):
        # Extreme pressure (p_li - p_le >> p_0) makes every depth invalid → empty DataFrame
        from dataclasses import replace
        pipe = Pipe(config=replace(valid_config, design_pressure=5000))
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        pipe.add_defect(Defect(length=200, relative_depth=0.25))
        pipe.calculate_maximum_allowable_defect_depth()
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1
        assert len(pipe.properties.maximum_allowable_defect_depth[0]) == 0

    def test_calculate_corrosion_rate_with_width(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, width=40, relative_depth=0.25, measurement_timestamp=0))
        pipe.add_defect(Defect(length=220, width=50, relative_depth=0.30, measurement_timestamp=86400))
        r_depth, r_length = pipe.calculate_corrosion_rate()
        assert r_depth == pytest.approx(0.05)
        assert r_length == pytest.approx(20.0)

    def test_estimate_remaining_life(self, valid_config):
        pipe = Pipe(config=valid_config)
        env = Environment(seawater_density=1025, containment_density=200,
                          elevation_reference=0, elevation=-100)
        pipe.set_environment(env)
        # r_corr = 0.01/day depth, 1.0/day length
        pipe.add_defect(Defect(length=250, relative_depth=0.20, measurement_timestamp=0))
        pipe.add_defect(Defect(length=251, relative_depth=0.21, measurement_timestamp=86400))
        pipe.properties.pressure_resistance = 20.0
        pipe.properties.effective_pressure = 15.0
        # Two-row allowable curve. The allowable depth is interpolated along it
        # (the RP's allowable curves are continuous, and the calculation samples them):
        #   growth    d(T) = 0.21 + 0.01T,  l(T) = 251 + 1.0T
        #   allowable f(l) = 0.80 - 0.55 * (l - 300) / 50
        #   d(T) = f(l(T))  ->  0.21 + 0.01T = 0.80 - 0.011(T - 49)  ->  T = 53.762
        df = pd.DataFrame({
            'defect_length': [300.0, 350.0],
            'defect_relative_depth': [0.80, 0.25],
        })
        pipe.properties.maximum_allowable_defect_depth = [df]
        pipe.estimate_remaining_life()
        assert pipe.properties.remaining_life == pytest.approx(53.762, abs=1e-3)

    def test_estimate_remaining_life_zero_corrosion_rate(self, valid_config):
        pipe = Pipe(config=valid_config)
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=0))
        pipe.add_defect(Defect(length=200, relative_depth=0.25, measurement_timestamp=86400))
        pipe.properties.pressure_resistance = 20.0
        pipe.properties.effective_pressure = 15.0
        pipe.properties.maximum_allowable_defect_depth = [pd.DataFrame({
            'defect_length': [300.0], 'defect_relative_depth': [0.80]
        })]
        pipe.estimate_remaining_life()
        assert pipe.properties.remaining_life is None
