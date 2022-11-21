"""
Collection of constants used by other srmlib.gpiocontrollers.
"""
from typing import Literal

FORWARD = 1
BACKWARD = -1
Direction = Literal[1, -1]

RELEASED = 0
PRESSED = 1
ButtonState = Literal[0, 1]
