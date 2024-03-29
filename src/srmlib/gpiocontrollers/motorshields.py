"""
Useful Links:
- RPi.GPIO PWM: https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
"""
from abc import ABC, abstractmethod
from logging import debug

from RPi.GPIO import setup, OUT, LOW, PWM, getmode, BOARD, output

from srmlib.gpiocontrollers.constants import FORWARD, BACKWARD, Direction

_VALID_DIRECTIONS = {FORWARD, BACKWARD}


class MotorShield(ABC):
    def __init__(self, *args, **kwargs) -> None:
        super(MotorShield, self).__init__(*args, **kwargs)  # Support multiple inheritance

    @property
    @abstractmethod
    def speed(self) -> float:
        """
        Getter for the current speed setting as a percentage [0, 100].

        :return: Returns the current speed as a percentage [0, 100].
        """
        pass

    @speed.setter
    @abstractmethod
    def speed(self, speed_: float) -> None:
        """
        Setter for the current speed setting as a percentage [0, 100].

        :param speed_: The new speed setting as a percentage [0, 100]
        """
        pass

    @property
    @abstractmethod
    def direction(self) -> Direction:
        """
        Getter for the current direction setting.

        :return: Returns the current direction setting.
        """
        pass

    @direction.setter
    @abstractmethod
    def direction(self, direction_: Direction) -> None:
        """
        Setter for the current direction setting.

        :param direction_: The new direction setting.
        """
        pass


class CytronMD10C(MotorShield):
    """
    Controller for a Cytron 10A DC Motor Driver, model number MD10C
    Product Page: https://www.cytron.io/p-10amp-5v-30v-dc-motor-driver
    User Manual: https://docs.google.com/document/d/1rgQzn-nWn-qcWNnHjDZvIYqUrdCeBQQxXA-TU3BF0AQ/view
    """

    _speed: float
    _pwm: PWM
    _direction_pin: int
    _direction: Direction
    _log_id: str

    def __init__(
            self, direction_pin: int, pulse_width_modulation_pin: int, *args,
            logging_identifier: str = None, **kwargs
    ) -> None:
        """
        Construct a controller for a Cytron MD10C motor shield

        :param direction_pin: The gpio pin connected to the motor shield's direction pin.
        :param pulse_width_modulation_pin: The gpio pin connected to the motor shield's pwm pin.
        """
        super().__init__(*args, **kwargs)
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
        self._log_id = f"[{logging_identifier or f'{self.__class__.__name__}-{id(self)}'}]"
        debug(f"{self._log_id} Initialized with dir={direction_pin};pwm={pulse_width_modulation_pin}")

    @property
    def speed(self) -> float:
        """
        Getter for the current speed setting as a percentage [0, 100].

        :return: Returns the current speed as a percentage [0, 100].
        """
        return self._speed

    @speed.setter
    def speed(self, speed_: float) -> None:
        """
        Setter for the current speed setting as a percentage [0, 100].

        :param speed_: The new speed setting as a percentage [0, 100]
        """
        if not (0 <= speed_ <= 100):
            raise ValueError(f"speed must be a percentage from 0 to 100 inclusive, was {speed_}")
        self._speed = speed_
        self._pwm.start(self._speed)
        debug(f"{self._log_id} Set speed to {speed_}")

    @property
    def direction(self) -> Direction:
        """
        Getter for the current direction setting.

        :return: Returns the current direction setting.
        """
        return self._direction

    @direction.setter
    def direction(self, direction_: Direction) -> None:
        """
        Setter for the current direction setting.

        :param direction_: The new direction setting.
        """
        if direction_ not in _VALID_DIRECTIONS:
            raise ValueError(f"{direction_} is not a valid direction, must be one of {','.join([str(direction) for direction in _VALID_DIRECTIONS])}")
        self._direction = direction_
        debug(f"{self._log_id} Set direction to {direction_}")
        output(self._direction_pin, 0 if self._direction == FORWARD else 1)  # For GPIO: forward = 0, backward = 1
