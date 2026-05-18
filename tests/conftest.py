import json
from os import path

import pytest

FIXTURE_PATH = path.join(path.dirname(__file__), 'fixtures')


@pytest.fixture
def example_a_1():
    with open(path.join(FIXTURE_PATH, 'example_a_1.json'), 'r') as file:
        example_a_1 = json.load(file)
    return example_a_1
