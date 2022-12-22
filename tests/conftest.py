import json
from os import path

import pytest

from backend.characteristics import Pipe, Defect

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


@pytest.fixture
def example_a_1():
    with open(path.join(FIXTURE_PATH, 'example_a_1.json'), 'r') as file:
        example_a_1 = json.load(file)
    return example_a_1


@pytest.fixture
def pipe_a_1(example_a_1):
    pipe_1_data = {}
    for key, value in example_a_1.items():
        try:
            pipe_1_data[key] = float(value['value'])
        except TypeError:
            pass
    pipe_1 = Pipe(pipe_1_data)
    return pipe_1


@pytest.fixture
def defect_a_1(example_a_1):
    length = example_a_1['defect_length']['value']
    relative_depth = example_a_1['defect_relative_depth']['value']
    elevation = example_a_1['defect_elevation']['value']
    measurement_tolerance = example_a_1['acc_rel']['value']
    measurement_confidence_interval = example_a_1['conf']['value']
    return Defect(length, elevation, measurement_tolerance, measurement_confidence_interval, relative_depth=relative_depth)
