"""
Pressure units.

The interface has to speak one unit consistently: entering a design pressure in bar and
reading results back in MPa is how wrong numbers get written down. The design pressure
is carried in **bar** (as DNVGL-RP-F101 states it) and the assessment works in **MPa**
(N/mm2, which is what the equations produce); this module is the only place those two
conventions meet.

An exported report always records MPa and bar, so a record is never ambiguous; the
selected unit only governs what the interface shows.
"""

# psi per bar, from 1 bar = 100 000 Pa and 1 psi = 6894.757293168361 Pa
PSI_PER_BAR = 14.503773773020923

PRESSURE_UNITS = ('bar', 'MPa', 'psi')


def to_bar(value: float, unit: str) -> float:
    """Convert a pressure given in `unit` to bar."""
    value = float(value)
    if unit == 'bar':
        return value
    if unit == 'MPa':
        return value * 10.0
    if unit == 'psi':
        return value / PSI_PER_BAR
    raise ValueError(f'Unknown pressure unit: {unit!r}. Use one of {PRESSURE_UNITS}')


def from_bar(value_bar: float, unit: str) -> float:
    """Convert a pressure in bar to `unit`."""
    value_bar = float(value_bar)
    if unit == 'bar':
        return value_bar
    if unit == 'MPa':
        return value_bar / 10.0
    if unit == 'psi':
        return value_bar * PSI_PER_BAR
    raise ValueError(f'Unknown pressure unit: {unit!r}. Use one of {PRESSURE_UNITS}')


def from_mpa(value_mpa: float, unit: str) -> float:
    """Convert a pressure in MPa, as the assessment equations produce it, to `unit`."""
    return from_bar(float(value_mpa) * 10.0, unit)


def format_pressure(value_mpa: float, unit: str, digits: int = 2) -> str:
    """Render an assessment pressure in the selected unit, with the unit on it."""
    digits = 3 if unit == 'psi' else digits
    return f'{from_mpa(value_mpa, unit):,.{digits}f} {unit}'
