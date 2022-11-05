"""
Controllers for Cytron Technologies devices

Useful Links:
- RPi.GPIO PWM: https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
"""

from RPi.GPIO import setup, OUT, LOW, PWM, getmode, BOARD, output


_FORWARD = 0
_BACKWARD = 1
_VALID_DIRECTIONS = {_FORWARD, _BACKWARD}
# class _Direction(IntEnum):
#     Forward: 0
#     Backward: 1


class CytronMD10C:
    """
    Controller for a Cytron 10A DC Motor Driver, model number MD10C
    Product Page: https://www.cytron.io/p-10amp-5v-30v-dc-motor-driver
    User Manual: https://docs.google.com/document/d/1rgQzn-nWn-qcWNnHjDZvIYqUrdCeBQQxXA-TU3BF0AQ/view
    """

    _speed: float
    _pwm: PWM
    _direction_pin: int
    _direction: int

    def __init__(self, direction_pin: int, pulse_width_modulation_pin: int) -> None:
        if getmode() != BOARD:
            # TODO kirypto 2022-Sep-17: Determine if it is safe to call setmode multiple times, and
            #  do that instead if so
            raise ValueError(
                f"GPIO board mode must be BOARD to use the {CytronMD10C.__name__}. "
                f"(Use PRi.GPIO.setmode to set this)")

        setup(pulse_width_modulation_pin, OUT, initial=LOW)
        setup(direction_pin, OUT, initial=LOW)
        self._speed = 0
        self._pwm = PWM(pulse_width_modulation_pin, 200)
        self._direction_pin = direction_pin

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        if not (0 <= value <= 100):
            raise ValueError(f"speed must be a percentage from 0 to 100 inclusive, was {value}")
        self._speed = value
        self._pwm.start(self._speed)

    @property
    def direction(self) -> int:
        return self._direction

    @direction.setter
    def direction(self, value: int) -> None:
        if value not in _VALID_DIRECTIONS:
            raise ValueError(f"{value} is not a valid direction, must be one of {','.join([str(direction) for direction in _VALID_DIRECTIONS])}")
        self._direction = value
        output(self._direction_pin, self._direction)
