"""
A single assessment, rendered as a record.

An integrity assessment is something an engineer files, reviews and later has to
reproduce, so the numbers behind a verdict are exported rather than left in the
browser. `build_report` gathers them into a plain dictionary (JSON ready) and
`render_markdown` turns the same dictionary into a readable summary.

Every number is cast to a builtin type: the calculation layer works in numpy, and
numpy scalars are not JSON serialisable.
"""
import datetime

STANDARD = 'DNVGL-RP-F101, Edition September 2019'


def build_report(pipe, generated_at: datetime.datetime = None, include_curve: bool = True) -> dict:
    """
    Collect the assessment into a serialisable dictionary.

    Args:
        pipe: an analysed Pipe
        generated_at: timestamp for the report, defaults to now
        include_curve: include the allowable depth curve points

    Returns:
        report: nested plain-python dictionary
    """
    generated_at = generated_at or datetime.datetime.now()
    effective = float(pipe.properties.effective_pressure)
    resistance = float(pipe.properties.pressure_resistance)

    return {
        'standard': STANDARD,
        'generated_at': generated_at.isoformat(timespec='seconds'),
        'verdict': {
            'acceptable': effective < resistance,
            'criterion': 'p_corr > p_li - p_le',
            'pressure_margin_mpa': round(resistance - effective, 4),
        },
        'pipe': {
            'outside_diameter_mm': float(pipe.dimensions.outside_diameter),
            'wall_thickness_mm': float(pipe.dimensions.wall_thickness),
        },
        'material': {
            'smts_mpa': _float(pipe.material_properties.smts),
            'smys_mpa': _float(pipe.material_properties.smys),
            'alpha_u': _float(pipe.material_properties.alpha_u),
            'design_temperature_c': _float(pipe.design_limits.design_temperature),
            'de_rating_mpa': _float(pipe.material_properties.f_u_temp),
            'f_u_mpa': _float(pipe.material_properties.f_u),
        },
        'design': {
            'design_pressure_bar': _float(pipe.design_limits.design_pressure),
            'incidental_to_design_ratio': _float(pipe.design_limits.incidental_to_design_pressure_ratio),
        },
        'assessment': {
            'safety_class': pipe.factors.safety_class,
            'measurement_method': pipe.factors.inspection_method,
            'measurement_accuracy': _float(pipe.factors.measurement_accuracy),
            'confidence_level': _float(pipe.factors.confidence_level),
            'standard_deviation': _float(pipe.factors.standard_deviation),
            'gamma_m': _float(pipe.factors.gamma_m),
            'gamma_d': _float(pipe.factors.gamma_d),
            'epsilon_d': _float(pipe.factors.epsilon_d),
            'xi': _float(pipe.factors.xi),
        },
        'environment': {
            'elevation_m': _float(pipe.environment.elevation),
            'elevation_reference_m': _float(pipe.environment.elevation_reference),
            'seawater_density_kg_m3': _float(pipe.environment.seawater_density),
            'containment_density_kg_m3': _float(pipe.environment.containment_density),
            'incidental_pressure_mpa': _float(pipe.environment.incidental_pressure),
            'external_pressure_mpa': _float(pipe.environment.external_pressure),
            'effective_pressure_mpa': effective,
        },
        'defects': [_defect_report(defect, pipe.combined_defect is defect)
                    for defect in pipe.assessment_defects],
        'results': _results(pipe),
        'allowable_depth_curves': _curves(pipe) if include_curve else [],
    }


def render_markdown(report: dict) -> str:
    """Render a report dictionary as Markdown, for filing or pasting into a review."""
    verdict = report['verdict']
    results = report['results']
    assessment = report['assessment']

    conclusion = (f"Acceptable. The effective pressure of {results['effective_pressure_mpa']:.2f} MPa is "
                  f"below the pressure resistance of {results['pressure_resistance_mpa']:.2f} MPa."
                  if verdict['acceptable'] else
                  f"NOT acceptable. The pressure resistance of {results['pressure_resistance_mpa']:.2f} MPa "
                  f"is below the effective pressure of {results['effective_pressure_mpa']:.2f} MPa.")

    lines = [
        '# Pipeline Corrosion Assessment',
        '',
        f"**Standard:** {report['standard']}  ",
        f"**Generated:** {report['generated_at']}  ",
        f"**Verdict:** {conclusion}",
        '',
        '## Geometry and material',
        '',
        '| Item | Value |',
        '|------|-------|',
        f"| Outside diameter | {report['pipe']['outside_diameter_mm']:.1f} mm |",
        f"| Wall thickness | {report['pipe']['wall_thickness_mm']:.2f} mm |",
        f"| SMTS | {_fmt(report['material']['smts_mpa'])} MPa |",
        f"| Design temperature | {_fmt(report['material']['design_temperature_c'])} °C |",
        f"| Temperature de-rating, f_u,temp | {_fmt(report['material']['de_rating_mpa'])} MPa |",
        f"| Tensile strength used, f_u | {_fmt(report['material']['f_u_mpa'])} MPa |",
        '',
        '## Assessment parameters',
        '',
        '| Parameter | Value | Clause |',
        '|-----------|-------|--------|',
        f"| Safety class | {assessment['safety_class']} | §3.2 |",
        f"| Inspection method | {assessment['measurement_method']} | §3.3 |",
        f"| Sizing accuracy | {assessment['measurement_accuracy']:g} "
        f"({'fraction of t' if assessment['measurement_method'] == 'relative' else 'mm'}) | §3.3 |",
        f"| Confidence level | {assessment['confidence_level']:g} | §3.3 |",
        f"| StD[d/t] | {assessment['standard_deviation']:.4f} | Table 3-3 to 3-6 |",
        f"| γm | {assessment['gamma_m']:.2f} | Table 3-2 |",
        f"| γd | {assessment['gamma_d']:.4f} | Table 3-7 / 3-8 |",
        f"| εd | {assessment['epsilon_d']:.4f} | Table 3-7 / 3-8 |",
        f"| ξ | {assessment['xi']:.2f} | Table 3-10 |",
        f"| Design pressure | {_fmt(report['design']['design_pressure_bar'])} bar | |",
        f"| Incidental/design ratio | {_fmt(report['design']['incidental_to_design_ratio'])} | |",
        '',
        '## Defects',
        '',
        '| Defect | Length [mm] | Width [mm] | Depth [mm] | d/t | (d/t)* | Q | p_corr [MPa] |',
        '|--------|------------:|-----------:|-----------:|----:|-------:|--:|-------------:|',
    ]
    for index, defect in enumerate(report['defects'], start=1):
        label = 'Combined' if defect['combined'] else str(index)
        lines.append(
            f"| {label} | {defect['length_mm']:.1f} | {_fmt(defect['width_mm'], 1)} | "
            f"{_fmt(defect['depth_mm'], 3)} | {_fmt(defect['relative_depth'], 4)} | "
            f"{_fmt(defect['adjusted_relative_depth'], 4)} | {_fmt(defect['length_correction_factor'], 4)} | "
            f"{_fmt(defect['pressure_resistance_mpa'], 3)} |")

    lines += [
        '',
        '## Results',
        '',
        '| Quantity | Value |',
        '|----------|-------|',
        f"| Effective pressure, p_li − p_le | {results['effective_pressure_mpa']:.3f} MPa "
        f"({results['effective_pressure_bar']:.2f} bar) |",
        f"| Pressure resistance, p_corr | {results['pressure_resistance_mpa']:.3f} MPa "
        f"({results['pressure_resistance_bar']:.2f} bar) |",
        f"| Margin | {verdict['pressure_margin_mpa']:+.3f} MPa |",
    ]
    if results['remaining_life_days'] is not None:
        lines.append(f"| Remaining life | {results['remaining_life_days']:.0f} days |")
    if results['corrosion_rate_per_day'] is not None:
        lines.append(f"| Corrosion rate, depth | {results['corrosion_rate_per_day']:.6f} /day |")
        lines.append(f"| Corrosion rate, length | {results['corrosion_rate_length_per_day']:.4f} mm/day |")

    lines += ['', f"_Generated by corrosion-analyser against {report['standard']}._", '']
    return '\n'.join(lines)


def filename(report: dict, extension: str) -> str:
    """A deterministic, sortable name for an exported report."""
    stamp = report['generated_at'].replace('-', '').replace(':', '')[:13]
    return f'corrosion-assessment-{stamp}.{extension.lstrip(".")}'


def _results(pipe) -> dict:
    resistance = float(pipe.properties.pressure_resistance)
    effective = float(pipe.properties.effective_pressure)
    remaining_life = pipe.properties.remaining_life

    corrosion_rate = corrosion_rate_length = None
    if len(pipe.defects) >= 2 and all(d.measurement_timestamp for d in pipe.defects):
        corrosion_rate, corrosion_rate_length = pipe.calculate_corrosion_rate()
        corrosion_rate = float(corrosion_rate)
        corrosion_rate_length = float(corrosion_rate_length)

    return {
        'pressure_resistance_mpa': round(resistance, 4),
        'pressure_resistance_bar': round(resistance * 10, 3),
        'effective_pressure_mpa': round(effective, 4),
        'effective_pressure_bar': round(effective * 10, 3),
        'remaining_life_days': None if remaining_life is None else round(float(remaining_life), 1),
        'corrosion_rate_per_day': None if corrosion_rate is None else round(corrosion_rate, 8),
        'corrosion_rate_length_per_day': None if corrosion_rate_length is None else round(corrosion_rate_length, 6),
    }


def _defect_report(defect, combined: bool) -> dict:
    return {
        'combined': combined,
        'length_mm': float(defect.length),
        'width_mm': _float(defect.width),
        'depth_mm': _float(defect.depth),
        'relative_depth': _float(defect.relative_depth),
        'adjusted_relative_depth': _float(defect.relative_depth_with_uncertainty),
        'position_mm': _float(defect.position),
        'length_correction_factor': _float(defect.length_correction_factor),
        'pressure_resistance_mpa': _float(defect.pressure_resistance),
        'measurement_timestamp': _float(defect.measurement_timestamp),
    }


def _curves(pipe) -> list:
    curves = []
    labels = ['measured'] + (['combined'] if pipe.combined_defect is not None else [])
    for index, frame in enumerate(pipe.properties.maximum_allowable_defect_depth):
        points = [[round(float(length), 1), round(float(depth), 4)]
                  for length, depth in zip(frame['defect_length'], frame['defect_relative_depth'])]
        curves.append({'label': labels[index] if index < len(labels) else f'curve {index + 1}',
                       'points': points})
    return curves


def _float(value):
    return None if value is None else float(value)


def _fmt(value, digits: int = 2) -> str:
    return '—' if value is None else f'{value:.{digits}f}'
