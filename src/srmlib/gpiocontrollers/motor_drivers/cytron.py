from typing import Literal

from RPi.GPIO import PWM, setup, OUT, LOW, output


class CytronMD10C:
    """
    Controller for a Cytron 10A DC Motor Driver, model number MD10C
    Product Page: https://www.cytron.io/p-10amp-5v-30v-dc-motor-driver
    User Manual: https://docs.google.com/document/d/1rgQzn-nWn-qcWNnHjDZvIYqUrdCeBQQxXA-TU3BF0AQ/view

    Inputs:
    - PWM pin: analog from LOW (0) to HIGH (1)
    - DIR pin: digital, either LOW (0) or HIGH (1)
    Input/Output Truth Table
    | PWM (in) | DIR (in) | A (out) | B (out) | Operation |
    | low      | X (any)  | low     | low     | brake low |
    | high     | low      | high    | low     | forward   |
    | high     | high     | low     | high    | reverse   |

    Notes:
    - The Cytron MD10C supports both Sign-Magnitude PWM and Locked-Antiphase PWM. This
      implementation currently only supports SignMagnitude. See User Manual for details.
    """
    # TODO: Add support for Locked-Antiphase PWM

    _duty_cycle: float
    _pwm: PWM
    _direction: Literal[0, 1]
    _dir_channel: int

    def __init__(
            self, dir_channel: int, pwm_channel: int, *args,
            pwm_frequency: float = 50, **kwargs
    ) -> None:
        """
        Constructs a controller for a Cytron MD10C Motor Driver

        :param dir_channel: The GPIO channel connected to the motor driver's DIR pin,
                either as a board or BCM number depending on GPIO mode.
        :param pwm_channel: The GPIO channel connected to the motor driver's PWM pin,
                either as a board or BCM number depending on GPIO mode.
        :param pwm_frequency: The pwm frequency in Hz. Cytron MD10C supports
                'up to 20KHz'.
        """
        super().__init__(*args, **kwargs)
        setup(pwm_channel, OUT, initial=LOW)
        setup(dir_channel, OUT, initial=LOW)
        self._duty_cycle = 0
        self._pwm = PWM(pwm_channel, pwm_frequency)
        self._direction = 0
        self._dir_channel = dir_channel

    @property
    def duty_cycle(self) -> float:
        """
        :return: Returns the current pwm duty cycle setting as a percentage [0, 100].
        """
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, duty_cycle: float) -> None:
        """
        :param duty_cycle: The value to set the pwm duty cycle to as a percentage [0, 100].
        :raises ValueError: Raised if the duty cycle is invalid.
        """
        if not 0 <= duty_cycle <= 1:
            raise ValueError(f"PWM duty cycle must be between 0 and 100 (inclusive), was {duty_cycle}")
        self._duty_cycle = duty_cycle
        if duty_cycle == 0:
            self._pwm.stop()
        else:
            self._pwm.start(duty_cycle)

    @property
    def direction(self) -> Literal[0, 1]:
        """
        :return:  Returns the current direction setting: 0 = Forward, 1 = Reverse.
        """
        return self._direction

    @direction.setter
    def direction(self, direction: Literal[0, 1]) -> None:
        """
        :param direction: The direction to set: 0 = Forward, 1 = Reverse.
        :raises ValueError: Raised if the direction is invalid.
        """
        if direction not in {0, 1}:
            raise ValueError(f"Direction must be either 0 (forward) or 1 (backward), was {direction}")
        self._direction = direction
        output(self._dir_channel, direction)





