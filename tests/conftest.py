import json
from os import path

import pytest

from core.utils.pipes import Pipe

FIXTURE_PATH = path.join(path.dirname(__file__), 'fixtures')


@pytest.fixture
def example_1_pipe():
    with open(path.join(FIXTURE_PATH, 'example_1.json'), 'r') as file:
        pipe_1_dict = json.load(file)
    pipe_1_data = {}
    for key, value in pipe_1_dict.items():
        pipe_1_data[key] = float(value['value'])
    pipe_1 = Pipe(**pipe_1_data)
    return pipe_1
