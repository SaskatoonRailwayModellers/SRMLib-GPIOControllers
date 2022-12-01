from typing import TypeVar, Union

Number = TypeVar("Number", bound=Union[float, int])


def clamp(value: Number, min_: Number, max_: Number) -> Number:
    """
    Clamp a value between 2 numbers.

    :param value: The value to clamp.
    :param min_: The minimum output value.
    :param max_: The maximum output value.
    :return: The value if it is between the max and min, otherwise the closest edge of the clamp range.
    """
    return max(min_, min(max_, value))


def calculate_percentage(val: float, min_: float, max_: float) -> float:
    """
    Calculates the position of the value within the range as a percentage [0, 100].

    :param val: The value within the range.
    :param min_: The lower bound of the range.
    :param max_: The higher bound of the range.
    :return: Returns the position as a percentage [0, 100].
    """
    return (clamp(val, min_, max_) - min_) / (max_ - min_) * 100
