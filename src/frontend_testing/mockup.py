# Run this src with `python src.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df1 = pd.DataFrame({
    "Corrosion defect length (mm)": [25, 45, 100, 160, 200, 450],
    "Allowable defect relative depth (d/t)": [0.25, 0.5, 0.35, 0.6, 0.19, 0.43],
    "Type": ['measurement', 'estimate', 'measurement', 'estimate', 'measurement', 'estimate']
})

fig1 = px.scatter(df1, x="Corrosion defect length (mm)", y="Allowable defect relative depth (d/t)", color="Type")

df2 = pd.DataFrame({
    "Corrosion defect length (mm)":
        [0, 25, 50, 75, 100, 125, 150, 175, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    "Allowable defect relative depth (d/t)":
        [0.85, 0.85, 0.75, 0.72, 0.7, 0.68, 0.64, 0.6, 0.57, 0.55, 0.5, 0.48, 0.475, 0.47, 0.46, 0.45, 0.45],
})
df2['type'] = 'acceptable'
fig2 = px.line(df2, x="Corrosion defect length (mm)", y="Allowable defect relative depth (d/t)", color='type')

fig3 = go.Figure(data=fig1.data + fig2.data)

app.layout = html.Div(children=[
    html.H1(children='Sample WebUI'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    html.H1(children='Defect Details'),
    dcc.Input(
        id="input_defect_length",
        type='number',
        placeholder="input type {}".format('number'),
    ),
    # dcc.Graph(
    #     id='Defect Samples',
    #     figure=fig1
    # ),
    # dcc.Graph(
    #     id='Acceptable Values',
    #     figure=fig2
    # ),
    html.H1(children='Remaining Life Assessment'),
    dcc.Graph(
        id='Remaining Life Assessment',
        figure=fig3
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
