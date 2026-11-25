import datetime

import pytest

from src.utils.assessment import build_pipe, assess, validate_inputs


def _input(value, unit=''):
    return {'Value': value, 'Unit': unit}


def pipe_data(**overrides):
    """A complete, valid set of interface inputs for the DNV example geometry."""
    data = {
        'Pipe Outer Diameter': _input(812.8, 'mm'),
        'Pipe Wall Thickness': _input(19.1, 'mm'),
        'SMTS': _input(530.9, 'MPa'),
        'Defect Length': _input(200, 'mm'),
        'Defect Width': _input(50, 'mm'),
        'Defect Depth': _input(0.25, 't'),
        'Defect Elevation': _input(-100, 'm'),
        'Design Pressure': _input(150, 'bar'),
        'Design Temperature': _input(75, 'C'),
        'Incidental to Design Pressure Ratio': _input(1.1),
        'Accuracy': _input(0.1),
        'Confidence Level': _input(0.8),
        'Safety Class': _input('medium'),
        'Sizing Accuracy Type': _input('relative'),
        'Seawater Density': _input(1025, 'kg/m3'),
        'Containment Density': _input(200, 'kg/m3'),
        'Elevation Reference': _input(30, 'm'),
        'Axial Stress': _input(None, 'MPa'),
        'Bending Stress': _input(None, 'MPa'),
        'Combined Stress': _input(None, 'MPa'),
        'Secondary Defect Length': _input(None, 'mm'),
        'Secondary Defect Width': _input(None, 'mm'),
        'Secondary Defect Depth': _input(None, 't'),
        'Secondary Defect Separation': _input(None, 'mm'),
        'First Date': _input(None, 'date'),
        'Second Date': _input(None, 'date'),
    }
    data.update(overrides)
    return data


class TestValidateInputs:
    def test_complete_inputs_pass(self):
        validate_inputs(pipe_data())

    def test_missing_value_is_named(self):
        with pytest.raises(ValueError, match='Required fields are empty: SMTS'):
            validate_inputs(pipe_data(**{'SMTS': _input(None, 'MPa')}))

    def test_multiple_missing_values_are_listed(self):
        with pytest.raises(ValueError, match='Accuracy, SMTS|SMTS, Accuracy'):
            validate_inputs(pipe_data(**{'SMTS': _input(None, 'MPa'),
                                         'Accuracy': _input(None)}))


class TestBuildPipe:
    def test_geometry_and_material(self):
        pipe = build_pipe(pipe_data())
        assert pipe.dimensions.outside_diameter == 812.8
        assert pipe.dimensions.wall_thickness == 19.1
        assert pipe.material_properties.smts == 530.9
        assert pipe.material_properties.f_u == pytest.approx((530.9 - 15) * 0.96)

    def test_relative_depth_input_selects_relative_measurement(self):
        pipe = build_pipe(pipe_data())
        assert pipe.factors.inspection_method == 'relative'
        assert pipe.defect.relative_depth == 0.25
        assert pipe.defect.depth == pytest.approx(0.25 * 19.1)

    def test_absolute_depth_is_parsed_as_absolute(self):
        """A depth in mm is an absolute depth; the accuracy type is chosen separately."""
        pipe = build_pipe(pipe_data(**{'Defect Depth': _input(4.775, 'mm')}))
        assert pipe.defect.depth == 4.775
        assert pipe.defect.relative_depth == pytest.approx(0.25)

    def test_environment_is_set(self):
        pipe = build_pipe(pipe_data())
        assert pipe.environment.incidental_pressure == pytest.approx(
            0.1 * 150 * 1.1 + 200 * 9.81 * 130 / 1_000_000)
        assert pipe.environment.external_pressure == pytest.approx(1025 * 9.81 * 100 / 1_000_000)

    def test_no_analysis_is_run(self):
        pipe = build_pipe(pipe_data())
        assert pipe.properties.pressure_resistance is None
        assert pipe.properties.maximum_allowable_defect_depth == []

    def test_secondary_defect_with_separation(self):
        pipe = build_pipe(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Width': _input(50, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'Secondary Defect Separation': _input(100, 'mm'),
        }))
        assert len(pipe.defects) == 2
        assert pipe.defects[1].length == 150
        assert pipe.defects[1].position == 100

    def test_combined_stress_is_compressive(self):
        pipe = build_pipe(pipe_data(**{'Combined Stress': _input(50, 'MPa')}))
        assert pipe.loading.loading_stress == pytest.approx(-50.0)

    def test_combined_stress_with_interacting_defects_rejected(self):
        with pytest.raises(ValueError, match='not supported with superimposed stress'):
            build_pipe(pipe_data(**{
                'Combined Stress': _input(50, 'MPa'),
                'Secondary Defect Length': _input(150, 'mm'),
                'Secondary Defect Separation': _input(100, 'mm'),
            }))

    def test_combined_stress_without_width_rejected(self):
        with pytest.raises(ValueError, match='Defect Width is required'):
            build_pipe(pipe_data(**{'Combined Stress': _input(50, 'MPa'),
                                    'Defect Width': _input(None, 'mm')}))

    def test_defect_depth_beyond_85_percent_rejected(self):
        with pytest.raises(ValueError, match='85'):
            build_pipe(pipe_data(**{'Defect Depth': _input(0.90, 't')}))

    def test_measurement_timestamps_from_dates(self):
        pipe = build_pipe(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'First Date': _input('2024-01-01', 'date'),
            'Second Date': _input('2025-01-01', 'date'),
        }))
        expected = datetime.datetime(2025, 1, 1).timestamp()
        assert pipe.defects[1].measurement_timestamp == pytest.approx(expected)


class TestPressureUnits:
    """The design pressure is read in whatever unit the interface quotes it in."""

    @pytest.mark.parametrize('unit,entered', [('bar', 150.0), ('MPa', 15.0),
                                              ('psi', 150.0 * 14.503773773020923)])
    def test_same_assessment_for_equivalent_design_pressures(self, unit, entered):
        pipe = build_pipe(pipe_data(**{'Design Pressure': _input(entered, unit)}))
        assert pipe.design_limits.design_pressure == pytest.approx(150.0)
        pipe.analyze()
        reference = assess(pipe_data())
        assert pipe.properties.effective_pressure == pytest.approx(
            reference.properties.effective_pressure, rel=1e-9)
        assert pipe.properties.pressure_resistance == pytest.approx(
            reference.properties.pressure_resistance, rel=1e-9)


class TestSizingAccuracyDecoupling:
    """Either accuracy type may be quoted with either depth representation."""

    def test_relative_accuracy_with_absolute_depth(self):
        pipe = build_pipe(pipe_data(**{
            'Defect Depth': _input(4.775, 'mm'),
            'Sizing Accuracy Type': _input('relative'),
        }))
        assert pipe.factors.inspection_method == 'relative'
        assert pipe.defect.depth == pytest.approx(4.775)
        assert pipe.defect.relative_depth == pytest.approx(0.25)
        # relative accuracy 0.1 at 80% confidence
        assert pipe.factors.standard_deviation == pytest.approx(0.078, abs=1e-3)

    def test_absolute_accuracy_with_relative_depth(self):
        pipe = build_pipe(pipe_data(**{
            'Defect Depth': _input(0.25, 't'),
            'Sizing Accuracy Type': _input('absolute'),
            'Accuracy': _input(0.5),
        }))
        assert pipe.factors.inspection_method == 'absolute'
        assert pipe.defect.relative_depth == pytest.approx(0.25)
        # absolute accuracy is scaled by the wall thickness and sqrt(2) (Table 3-4 to 3-6)
        from src.utils.calculations.statistical_calculations import calculate_inv_cumulative_dist
        expected = (2 ** 0.5 * 0.5) / (19.1 * calculate_inv_cumulative_dist(0.9))
        assert pipe.factors.standard_deviation == pytest.approx(expected, abs=1e-12)

    def test_very_high_safety_class_is_usable(self):
        """Table D-1 allows Very High; it must produce sane factors, not zeros."""
        pipe = build_pipe(pipe_data(**{'Safety Class': _input('very high')}))
        assert pipe.factors.safety_class == 'very high'
        assert pipe.factors.gamma_m == pytest.approx(0.76)
        assert pipe.factors.gamma_d >= 1.0
        assert pipe.factors.xi == pytest.approx(0.75)
        pipe.analyze()
        assert pipe.properties.pressure_resistance > 0


class TestMeasurementOrdering:
    def test_defects_keep_axial_order(self):
        """The form's order is preserved. The §3.8.2 interaction maths reads the
        axial separation as defects[1].position - defects[0].position, so
        reordering the pair inverts it."""
        pipe = build_pipe(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'First Date': _input('2025-01-01', 'date'),   # later
            'Second Date': _input('2024-01-01', 'date'),  # earlier
        }))
        earlier = datetime.datetime(2024, 1, 1).timestamp()
        later = datetime.datetime(2025, 1, 1).timestamp()
        assert pipe.defects[0].measurement_timestamp == pytest.approx(later)
        assert pipe.defects[1].measurement_timestamp == pytest.approx(earlier)

    def test_chronological_pair_orders_by_timestamp(self):
        pipe = build_pipe(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
            'First Date': _input('2025-01-01', 'date'),   # later
            'Second Date': _input('2024-01-01', 'date'),  # earlier
        }))
        earlier, later = pipe._chronological_pair()
        assert earlier.measurement_timestamp < later.measurement_timestamp

    def test_reversed_dates_do_not_change_the_combined_defect(self):
        """Regression: ordering the defect list by date inverted the axial
        separation, so a reversed date range built the combined defect from the
        wrong span and could flip an acceptable pipeline to unacceptable."""
        geometry = {
            'Defect Length': _input(100, 'mm'),
            'Defect Depth': _input(0.20, 't'),
            'Secondary Defect Length': _input(100, 'mm'),
            'Secondary Defect Depth': _input(0.25, 't'),
            'Secondary Defect Separation': _input(50, 'mm'),
        }
        forward = assess(pipe_data(**geometry, **{
            'First Date': _input('2024-01-01', 'date'),
            'Second Date': _input('2025-01-01', 'date'),
        }))
        reversed_dates = assess(pipe_data(**geometry, **{
            'First Date': _input('2025-01-01', 'date'),
            'Second Date': _input('2024-01-01', 'date'),
        }))

        assert forward.combined_defect is not None
        assert reversed_dates.combined_defect is not None
        assert reversed_dates.combined_defect.length == pytest.approx(
            forward.combined_defect.length)
        assert reversed_dates.combined_defect.relative_depth == pytest.approx(
            forward.combined_defect.relative_depth)
        assert reversed_dates.properties.pressure_resistance == pytest.approx(
            forward.properties.pressure_resistance)

    def test_reversed_dates_still_yield_a_positive_corrosion_rate(self):
        # The growth is attached to the dates, so the later (deeper) measurement is
        # the primary defect; the dates are then entered in reverse order.
        pipe = assess(pipe_data(**{
            'Defect Length': _input(210, 'mm'),
            'Defect Depth': _input(0.26, 't'),
            'Secondary Defect Length': _input(200, 'mm'),
            'Secondary Defect Depth': _input(0.25, 't'),
            'First Date': _input('2025-01-01', 'date'),   # later
            'Second Date': _input('2024-01-01', 'date'),  # earlier
        }))
        rate, rate_length = pipe.calculate_corrosion_rate()
        assert rate > 0
        assert rate_length > 0
        assert pipe.properties.remaining_life is not None


class TestAssess:
    def test_full_assessment(self):
        pipe = assess(pipe_data())
        assert pipe.properties.pressure_resistance == pytest.approx(17.172, abs=1e-3)
        assert pipe.properties.effective_pressure == pytest.approx(15.75, abs=1e-3)
        assert len(pipe.properties.maximum_allowable_defect_depth) == 1

    def test_assessment_with_loading(self):
        pipe = assess(pipe_data(**{'Combined Stress': _input(200, 'MPa')}))
        assert pipe.properties.pressure_resistance > 0


class TestAccuracyTypeFallback:
    """Callers that predate the depth-unit/accuracy-type split sent no accuracy type.

    They used to get it inferred from the depth unit, so a depth in mm meant
    absolute accuracy; defaulting them to 'relative' would reinterpret their
    accuracy silently.
    """

    def test_absent_accuracy_type_with_an_mm_depth_is_absolute(self):
        inputs = pipe_data(**{'Defect Depth': _input(4.8, 'mm')})
        inputs.pop('Sizing Accuracy Type')
        pipe = build_pipe(inputs)
        assert pipe.factors.inspection_method == 'absolute'

    def test_absent_accuracy_type_with_a_relative_depth(self):
        inputs = pipe_data()
        inputs.pop('Sizing Accuracy Type')
        pipe = build_pipe(inputs)
        assert pipe.factors.inspection_method == 'relative'


class TestLegendEncoding:
    def test_measured_markers_keep_their_palette_colour(self):
        """Regression: passing marker=None to trace.update() resets the marker that
        px.scatter built, so the first measured defect lost the pass/fail colour
        and the square/circle symbol distinction on the adequacy chart."""
        from src.utils.graphing import defect_plots

        pipe = assess(pipe_data(**{
            'Secondary Defect Length': _input(150, 'mm'),
            'Secondary Defect Depth': _input(0.30, 't'),
        }))
        fig = defect_plots.generate_defect_depth_plot(pipe, theme='dark')

        measured = [trace for trace in fig.data
                    if trace.name and trace.name.startswith('Measured Defect')]
        assert len(measured) == 2
        for trace in measured:
            assert trace.marker.color is not None, f'{trace.name} lost its marker colour'
        assert measured[1].marker.symbol == 'square'
