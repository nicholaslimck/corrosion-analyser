from dash import dcc, html
import dash_bootstrap_components as dbc


def generate_input(
        name: str,
        field_type: str
):
    # if field_type in ['number', 'text']:
    #     return dbc.Input(id=f'input_{name.lower().replace(" ", "_")}', type=field_type, debounce=1, placeholder=name)

    return dbc.Input(id=f'input_{name.lower().replace(" ", "_")}', type=field_type, debounce=1, placeholder=name)


def generate_input_group(
        name: str,
        field_type: str,
        units: str
):
    return dbc.InputGroup(
        [
            dbc.Input(
                id=f'input_{name.lower().replace(" ", "_")}',
                type=field_type,
                debounce=1,
                placeholder=name
            ),
            dbc.InputGroupText(units)
        ],
        className="mb-3",
    )


def generate_input_section(
        section_name: str,
        input_fields: list[tuple[str, str, str]]
):
    # fields = [dbc.Row([dbc.Col(generate_input(name, field_type))]) for name, field_type in input_fields]
    fields = [dbc.Row([dbc.Col(generate_input_group(name, field_type, units))]) for name, field_type, units in
              input_fields]
    return [
        html.H4(section_name),
        dbc.Form(fields)
    ]


center_align_style = {
    "text-align": "center",
    "display": "flex",
    "justify-content": "center",
    "align-items": "center"
}
