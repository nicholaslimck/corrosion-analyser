from dataclasses import dataclass
from typing import Union


@dataclass
class Parameter:
    """
    Parameter dataclass containing the value and optional unit
    """
    value: Union[int, float]
    unit: 'str' = None
