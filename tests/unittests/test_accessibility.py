"""Structural checks that every form control carries an accessible name.

The page had labels that looked right but were not bound to their inputs: no
`for` attribute, so the accessibility tree exposed five unnamed spin buttons and
four unnamed comboboxes. These tests pin the binding at the component level,
because a visual review cannot see it.
"""
from dash import html

import src.app  # noqa: F401 - instantiates the Dash app so page modules can register
from src.pages.defect_analysis import _input_row, layout

CONTROL_IDS = [
    'input-outer-diameter',
    'input-wall-thickness',
    'input-smts',
    'input-defect-length',
    'input-defect-width',
    'input-defect-depth',
    'single_defect_select_safety_class',
    'single_defect_select_measurement',
    'single_defect_select_accuracy_type',
]


def _walk(node):
    """Yield every Dash component in a component tree."""
    if isinstance(node, (list, tuple)):
        for item in node:
            yield from _walk(item)
        return
    if not hasattr(node, '_prop_names'):
        return
    yield node
    children = getattr(node, 'children', None)
    if children is not None:
        yield from _walk(children)


def test_input_row_binds_its_label_to_the_input():
    row = _input_row('Wall Thickness', 'input-wall-thickness', 19.1, 'mm')
    labels = [c for c in _walk(row) if isinstance(c, html.Label)]
    assert labels, 'the row has no label'
    assert labels[0].htmlFor == 'input-wall-thickness'


def test_optional_input_is_marked_optional_in_its_label():
    # dbc.Input whitelists its props and rejects aria-required, so the cue is
    # carried in the label text, which also lands in the accessible name.
    labels = [c for c in _walk(_input_row('Width', 'input-defect-width', None, 'mm',
                                          optional=True)) if isinstance(c, html.Label)]
    assert labels[0].htmlFor == 'input-defect-width'
    assert '(optional)' in str(labels[0].children)


def test_required_inputs_are_not_marked_optional():
    text = str(_input_row('Length', 'input-defect-length', 200, 'mm'))
    assert '(optional)' not in text


def test_every_form_control_in_the_panel_has_a_bound_label():
    bound = {c.htmlFor for c in _walk(layout()) if isinstance(c, html.Label)}
    missing = [control for control in CONTROL_IDS if control not in bound]
    assert missing == [], f'controls without a bound label: {missing}'
