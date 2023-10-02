import json
from os import path

import pytest

from src.utils.models import Parameter

FIXTURE_PATH = path.join(path.dirname(__file__), 'fixtures')


@pytest.fixture
def example_a_1():
    with open(path.join(FIXTURE_PATH, 'example_a_1.json'), 'r') as file:
        example_a_1 = json.load(file)
    return example_a_1


@pytest.fixture
def example_a_1_parameterised():
    with open(path.join(FIXTURE_PATH, 'example_a_1.json'), 'r') as file:
        example_a_1 = json.load(file)
        for key, value in example_a_1:
            example_a_1[key] = Parameter(**value)
    return example_a_1
