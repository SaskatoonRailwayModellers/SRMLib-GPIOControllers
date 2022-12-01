from logging import debug, error
from typing import List, Callable

from RPi.GPIO import setmode, BOARD, input as gpio_input, add_event_detect, BOTH, setup, IN, PUD_DOWN

from srmlib.gpiocontrollers.constants import PRESSED, RELEASED, ButtonState, FORWARD, BACKWARD, Direction

SwitchCallback = Callable[[ButtonState], None]
RotationCallback = Callable[[Direction], None]


class RotaryEncoderKY040:
    """
    Controller for a KY040 Rotary Encoder
    Datasheet: https://www.rcscomponents.kiev.ua/datasheets/ky-040-datasheet.pdf
    """
    _log_id: str
    _clk_state: int
    _dt_state: int
    _sw_state: int
    _switch_callbacks: List[SwitchCallback]
    _rotation_callbacks: List[RotationCallback]

    def __init__(self, clk_pin: int, dt_pin: int, sw_pin: int, *, logging_identifier: str = None) -> None:
        setmode(BOARD)
        setup(clk_pin, IN, pull_up_down=PUD_DOWN)
        setup(dt_pin, IN, pull_up_down=PUD_DOWN)
        setup(sw_pin, IN, pull_up_down=PUD_DOWN)
        self._clk_state = gpio_input(clk_pin)
        self._dt_state = gpio_input(dt_pin)
        self._sw_state = gpio_input(sw_pin)
        self._switch_callbacks = []
        self._rotation_callbacks = []
        self._log_id = f"[{logging_identifier or f'{self.__class__.__name__}-{id(self)}'}]"

        def switch_callback(_) -> None:
            current_state = gpio_input(sw_pin)  # Read the current state of the button pin
            if current_state != self._sw_state:
                self._invoke_switch_callbacks(PRESSED if not current_state else RELEASED)
            self._sw_state = current_state

        def rotation_callback(pin: int) -> None:
            current_state = gpio_input(pin)  # Read the current state of the button pin
            last = (self._clk_state, self._dt_state)
            if pin == dt_pin:
                self._dt_state = current_state
            elif pin == clk_pin:
                self._clk_state = current_state
            current = (self._clk_state, self._dt_state)
            if last != current and all(current):
                self._invoke_rotation_callbacks(FORWARD if last[0] else BACKWARD)

        add_event_detect(clk_pin, BOTH, callback=rotation_callback, bouncetime=1)
        add_event_detect(dt_pin, BOTH, callback=rotation_callback, bouncetime=1)
        add_event_detect(sw_pin, BOTH, callback=switch_callback, bouncetime=1)
        debug(f"{self._log_id} Initialized with clk={clk_pin};dt={dt_pin};sw={sw_pin}")

    def add_switch_callback(self, callback: SwitchCallback) -> None:
        self._switch_callbacks.append(callback)

    def add_rotation_callback(self, callback: RotationCallback) -> None:
        self._rotation_callbacks.append(callback)

    def _invoke_switch_callbacks(self, switch_state: ButtonState) -> None:
        debug(f"{self._log_id} Switch state changed, now is {switch_state}. Invoking callbacks.")
        for callback in self._switch_callbacks:
            try:
                callback(switch_state)
            except RuntimeError as e:
                error(f"{self._log_id} Switch callback threw an exception: {e}")

    def _invoke_rotation_callbacks(self, direction: Direction) -> None:
        debug(f"{self._log_id} {direction} Direction event occurred. Invoking callbacks.")
        for callback in self._rotation_callbacks:
            try:
                callback(direction)
            except RuntimeError as e:
                error(f"{self._log_id} Direction callback threw an exception: {e}")
