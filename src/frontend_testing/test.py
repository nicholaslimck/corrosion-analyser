import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

import backend.models as models

pipe = models.Pipe

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive Dash Web App"),
    html.Label('Pipe Dimensions:'),
    html.Div(children=[
            dcc.Input(id='outer-diameter', type='number', placeholder='Enter Outer Diameter'),
            dcc.Input(id='wall-thickness', type='number', placeholder='Enter Wall Thickness'),
            dcc.Input(id='smts', type='number', placeholder='Enter SMTS'),
            dcc.Input(id='design-pressure', type='number', placeholder='Enter Design Pressure'),
            dcc.Input(id='design-temperature', type='number', placeholder='Enter Design Temperature'),
            dcc.Input(id='f-u-temp', type='number', placeholder='Enter F_u_temp'),
        ]
    ),
    html.Label('Environment Properties:'),
    html.Div(children=[
            dcc.Input(id='seawater-density', type='number', placeholder='Enter Seawater Density')
        ]
    ),
    html.Label('Defect Dimensions:'),
    html.Div(children=[
            dcc.Input(id='defect-length', type='number', placeholder='Enter Defect Length'),
            dcc.Input(id='defect-depth', type='number', placeholder='Enter Defect Depth'),
            dcc.Input(id='defect-elevation', type='number', placeholder='Enter Defect Elevation')
        ]
    ),
    html.Label('Measurement Factors:'),
    html.Div(children=[
        dcc.Input(id='measurement-tolerance', type='number', placeholder='Enter Measurement Tolerance'),
        dcc.Input(id='measurement-confidence-level', type='number', placeholder='Enter Measurement Confidence Level'),
        dcc.Dropdown(id='safety-class', options=['Low', 'Medium', 'High'], value='Medium')
    ]
    ),
    html.Div(children=html.Button('Submit', id='submit-val', n_clicks=0)),
    html.Div(id='container-button-basic',
             children='Enter a value and press submit'),
    html.Div(children='[PLACEHOLDER]'),
    dcc.Input(id='x-input', type='number', placeholder='Enter X'),
    dcc.Input(id='y-input', type='number', placeholder='Enter Y'),
    dcc.Graph(id='graph')
])


@app.callback(
    Output('graph', 'figure'),
    [Input('x-input', 'value'),
     Input('y-input', 'value')]
)
def update_graph(x_value, y_value):
    if x_value is None or y_value is None:
        return px.scatter()

    df = pd.DataFrame({'X': [x_value], 'Y': [y_value]})
    fig = px.scatter(df, x='X', y='Y', title='User-Generated Data')
    return fig


@app.callback(
    Output('container-button-basic', 'children'),
    [Input('submit-val', 'n_clicks'),
     Input('outer-diameter', 'value'),
     Input('wall-thickness', 'value'),
     Input('smts', 'value'),
     Input('design-pressure', 'value'),
     Input('design-temperature', 'value'),
     Input('f-u-temp', 'value'),
     Input('measurement-tolerance', 'value'),
     Input('measurement-confidence-level', 'value'),
     Input('safety-class', 'value')]
)
def validate_pipe_inputs(
        n_clicks,
        outer_diameter,
        wall_thickness,
        smts,
        design_pressure,
        design_temperature,
        f_u_temp,
        measurement_tolerance,
        measurement_confidence_level,
        safety_class):
    if n_clicks is not None:
        if n_clicks > 0:
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

            print(pipe_config)
            pipe = models.Pipe(config=pipe_config)

            return outer_diameter, wall_thickness


if __name__ == '__main__':
    app.run_server(debug=True)
