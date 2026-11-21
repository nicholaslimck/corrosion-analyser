"""
Build an assessment model from the flat input dictionary used by the web interface.

Keeping this here rather than in the Dash page means the input validation and the
mapping from form values to model parameters can be exercised without instantiating
the application.
"""
import datetime

from src.utils import models

# Input key -> label shown to the user when the value is missing
REQUIRED_INPUTS = {
    'Pipe Outer Diameter': 'Outer Diameter',
    'Pipe Wall Thickness': 'Wall Thickness',
    'SMTS': 'SMTS',
    'Defect Length': 'Defect Length',
    'Defect Depth': 'Defect Depth',
    'Defect Elevation': 'Defect Elevation',
    'Design Pressure': 'Design Pressure',
    'Design Temperature': 'Design Temperature',
    'Incidental to Design Pressure Ratio': 'Incidental/Design Ratio',
    'Accuracy': 'Accuracy',
    'Confidence Level': 'Confidence Level',
    'Seawater Density': 'Seawater Density',
    'Containment Density': 'Containment Density',
    'Elevation Reference': 'Elevation Reference',
}


def _value(pipe_data: dict, key: str, default=None):
    return pipe_data.get(key, {}).get('Value', default)


def validate_inputs(pipe_data: dict) -> None:
    """
    Check that every required input has a value.

    Raises:
        ValueError: naming the inputs that are empty
    """
    missing = [label for key, label in REQUIRED_INPUTS.items() if _value(pipe_data, key) is None]
    if missing:
        raise ValueError(f"Required fields are empty: {', '.join(missing)}")


def build_pipe(pipe_data: dict) -> models.Pipe:
    """
    Build the Pipe model from the interface inputs, without running the assessment.

    Args:
        pipe_data: flat mapping of input name to {'Value': ..., 'Unit': ...}

    Returns:
        pipe: configured Pipe with defects, environment and loading attached

    Raises:
        ValueError: on missing inputs, unsupported input combinations, or inputs
            outside the acceptance criteria of DNVGL-RP-F101
    """
    validate_inputs(pipe_data)

    measurement_method = "relative" if _unit_of(pipe_data, 'Defect Depth') == "t" else "absolute"

    pipe_config = models.PipeConfig(
        outside_diameter=_value(pipe_data, 'Pipe Outer Diameter'),
        wall_thickness=_value(pipe_data, 'Pipe Wall Thickness'),
        smts=_value(pipe_data, 'SMTS'),
        design_pressure=_value(pipe_data, 'Design Pressure'),
        design_temperature=_value(pipe_data, 'Design Temperature'),
        incidental_to_design_pressure_ratio=_value(pipe_data, 'Incidental to Design Pressure Ratio'),
        accuracy=_value(pipe_data, 'Accuracy'),
        confidence_level=_value(pipe_data, 'Confidence Level'),
        safety_class=_value(pipe_data, 'Safety Class'),
        measurement_method=measurement_method,
    )

    defect_config = _defect_config(pipe_data, 'Defect')
    secondary_defect_config = _defect_config(pipe_data, 'Secondary Defect')

    first_date = _value(pipe_data, 'First Date')
    second_date = _value(pipe_data, 'Second Date')
    if first_date and second_date:
        defect_config['measurement_timestamp'] = _timestamp(first_date)
        secondary_defect_config['measurement_timestamp'] = _timestamp(second_date)

    secondary_defect_separation = _value(pipe_data, 'Secondary Defect Separation')
    if secondary_defect_separation:
        secondary_defect_config['position'] = secondary_defect_separation

    environment_config = {
        'seawater_density': _value(pipe_data, 'Seawater Density'),
        'containment_density': _value(pipe_data, 'Containment Density'),
        'elevation_reference': _value(pipe_data, 'Elevation Reference'),
        'elevation': _value(pipe_data, 'Defect Elevation'),
    }

    combined_stress = _value(pipe_data, 'Combined Stress')
    if combined_stress:
        if secondary_defect_separation:
            raise ValueError('Interacting defects are not supported with superimposed stress.')
        if _value(pipe_data, 'Defect Width') is None:
            raise ValueError('Defect Width is required for stress calculations.')
        # Treated as a compressive load
        loading_config = {'combined_stress': -abs(float(combined_stress))}
    else:
        loading_config = None

    pipe = models.Pipe(config=pipe_config)
    pipe.add_defect(models.Defect(**defect_config))
    if secondary_defect_config['length']:
        pipe.add_defect(models.Defect(**secondary_defect_config))

    if loading_config:
        pipe.add_loading(**loading_config)

    pipe.set_environment(models.Environment(**environment_config))

    return pipe


def assess(pipe_data: dict) -> models.Pipe:
    """Build the model and run the full assessment pipeline."""
    pipe = build_pipe(pipe_data)
    pipe.analyze()
    return pipe


def _unit_of(pipe_data: dict, key: str, default=None):
    return pipe_data.get(key, {}).get('Unit', default)


def _defect_config(pipe_data: dict, prefix: str) -> dict:
    """Map a defect's inputs, using whichever depth representation the unit implies."""
    depth_key = f'{prefix} Depth'
    depth_field = 'relative_depth' if _unit_of(pipe_data, depth_key) == 't' else 'depth'
    return {
        'length': _value(pipe_data, f'{prefix} Length'),
        'width': _value(pipe_data, f'{prefix} Width'),
        depth_field: _value(pipe_data, depth_key),
    }


def _timestamp(date_string: str) -> float:
    return datetime.datetime.timestamp(
        datetime.datetime.strptime(date_string, '%Y-%m-%d'))
