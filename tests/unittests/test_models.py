import pytest

from src.utils.models.pipe import Pipe, Loading, DesignLimits
from src.utils.models.defect import Defect
from src.utils.models.material import MaterialProperties, estimate_de_rating_stress_or_strength
from src.utils.models.environment import Environment
from src.utils.models.factors import Factors


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


# --- Pipe ---

class TestPipe:
    @pytest.fixture
    def valid_config(self):
        return {
            'outside_diameter': 812.8,
            'wall_thickness': 19.1,
            'smts': 530.9,
            'design_pressure': 150,
            'design_temperature': 75,
            'incidental_to_design_pressure_ratio': 1.1,
            'accuracy': 0.1,
            'confidence_level': 0.8,
            'safety_class': 'medium',
            'measurement_method': 'relative'
        }

    def test_valid_construction(self, valid_config):
        pipe = Pipe(config=valid_config)
        assert pipe.dimensions.outside_diameter == 812.8
        assert pipe.dimensions.wall_thickness == 19.1
        assert pipe.material_properties.f_u is not None
        assert pipe.factors.gamma_m == 0.85

    def test_zero_diameter_raises(self, valid_config):
        valid_config['outside_diameter'] = 0
        with pytest.raises(ValueError, match="Outside diameter must be positive"):
            Pipe(config=valid_config)

    def test_negative_diameter_raises(self, valid_config):
        valid_config['outside_diameter'] = -100
        with pytest.raises(ValueError, match="Outside diameter must be positive"):
            Pipe(config=valid_config)

    def test_zero_wall_thickness_raises(self, valid_config):
        valid_config['wall_thickness'] = 0
        with pytest.raises(ValueError, match="Wall thickness must be positive"):
            Pipe(config=valid_config)

    def test_wall_thickness_too_large_raises(self, valid_config):
        valid_config['wall_thickness'] = 500  # >= 812.8 / 2
        with pytest.raises(ValueError, match="Wall thickness must be less than half"):
            Pipe(config=valid_config)

    def test_zero_design_pressure_raises(self, valid_config):
        valid_config['design_pressure'] = 0
        with pytest.raises(ValueError, match="Design pressure must be positive"):
            Pipe(config=valid_config)

    def test_estimate_remaining_life_single_defect_raises(self, valid_config):
        pipe = Pipe(config=valid_config)
        defect = Defect(length=200, relative_depth=0.25)
        pipe.add_defect(defect)
        with pytest.raises(ValueError, match="Two defect measurements required"):
            pipe.estimate_remaining_life()
