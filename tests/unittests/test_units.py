import pytest

from src.utils.units import PSI_PER_BAR, PRESSURE_UNITS, format_pressure, from_bar, from_mpa, to_bar


class TestConversion:
    @pytest.mark.parametrize('unit,value,expected_bar', [
        ('bar', 150.0, 150.0),
        ('MPa', 15.0, 150.0),
        ('psi', 150.0 * PSI_PER_BAR, 150.0),
    ])
    def test_to_bar(self, unit, value, expected_bar):
        assert to_bar(value, unit) == pytest.approx(expected_bar)

    def test_round_trip_through_every_unit(self):
        for unit in PRESSURE_UNITS:
            assert from_bar(to_bar(42.0, unit), unit) == pytest.approx(42.0)

    def test_known_conversions(self):
        assert to_bar(1.0, 'bar') == pytest.approx(1.0)
        assert to_bar(1.0, 'MPa') == pytest.approx(10.0)          # 1 MPa = 10 bar
        assert to_bar(PSI_PER_BAR, 'psi') == pytest.approx(1.0)
        assert from_mpa(1.0, 'bar') == pytest.approx(10.0)        # 1 MPa = 10 bar
        assert from_mpa(1.0, 'MPa') == pytest.approx(1.0)
        assert from_mpa(1.0, 'psi') == pytest.approx(145.0377, abs=1e-4)

    def test_unknown_unit_is_rejected(self):
        with pytest.raises(ValueError, match='Unknown pressure unit'):
            to_bar(1.0, 'kPa')
        with pytest.raises(ValueError, match='Unknown pressure unit'):
            from_bar(1.0, 'kPa')


class TestFormatting:
    def test_includes_the_unit_on_the_number(self):
        # DNV example: p_corr 17.172 MPa = 171.72 bar
        assert format_pressure(17.172, 'MPa') == '17.17 MPa'
        assert format_pressure(17.172, 'bar') == '171.72 bar'
        expected_psi = f'{17.172 * 10 * PSI_PER_BAR:,.3f} psi'
        assert format_pressure(17.172, 'psi') == expected_psi

    def test_uses_thousands_separators(self):
        assert format_pressure(17.172, 'psi').startswith('2,490')
        assert '.psi' not in format_pressure(17.172, 'psi')
