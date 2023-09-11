import backend.calculations.defect_calculations
import backend.calculations as calculations
import backend.models as models


if __name__ == '__main__':
    print('-'*10, 'ENTER MEASUREMENTS', '-'*10)
    # Pipe properties
    print('>> Enter pipe properties:')
    outer_diameter = float(input('Enter outer diameter in mm: '))
    wall_thickness = float(input('Enter wall thickness in mm: '))
    smts = float(input('Enter SMTS in N/mm^2: '))
    design_pressure = float(input('Enter design pressure in bar: '))
    design_temperature = float(input('Enter design temperature in DegC: '))
    f_u_temp = float(input('Input f_u_temp in N/mm^2: '))

    # Environment properties
    print('>> Enter environment properties:')
    elevation_defect = float(input('Enter elevation of the defect: '))
    # elevation_reference = input('Enter elevation of the reference point: ')
    # seawater_density = input('Enter seawater density: ')
    # containment_density = input('Enter containment density: ')

    # Defect dimensions
    print('>> Enter defect dimensions:')
    defect_length = float(input('Enter defect length in mm: '))
    defect_depth = float(input('Enter defect relative depth: '))

    # Measurement accuracy
    print('>> Enter measurement factors:')
    measurement_tolerance = float(input('Enter measurement tolerance: '))
    measurement_confidence_level = float(input('Enter measurement confidence level: '))
    safety_class = input('Enter safety class: ').lower()

    pipe_config = {
        'outside_diameter': outer_diameter,
        'wall_thickness': wall_thickness,
        'alpha_u': 0.96,
        'smts': smts,
        'design_pressure': design_pressure,
        'design_temperature': design_temperature,
        'f_u_temp': f_u_temp,
        'accuracy_relative': measurement_tolerance,
        'confidence_level': measurement_confidence_level,
        'safety_class': safety_class
    }
    pipe = models.Pipe(config=pipe_config)

    defect = models.Defect(
        length=defect_length,
        elevation=elevation_defect,
        # measurement_tolerance=measurement_tolerance,
        # measurement_confidence_interval=measurement_confidence_level,
        relative_depth=defect_depth
    )

    pipe.add_defect(defect)

    # Calculate parameters
    print('-'*10, 'CALCULATED PROPERTIES', '-'*10)
    # Calculate length correction factor
    defect.generate_length_correction_factor(
        d_nominal=pipe.dimensions.outside_diameter,
        t=pipe.dimensions.wall_thickness
    )
    print(f'Length correction factor Q = {defect.length_correction_factor:2f}')

    # Calculate depth
    defect.calculate_d_t(
        epsilon_d=1.0, stdev=0.08
    )
    print(f'Absolute depth (d/t)* = {defect.depth}')

    # f_u
    print(f'f_u = {pipe.material_properties.f_u:.2f} N/mm^2')

    # Calculate p_corr
    p_corr = pipe.calculate_pressure_resistance()
    print(f'p_corr = {p_corr:.2f} N/mm^2')

