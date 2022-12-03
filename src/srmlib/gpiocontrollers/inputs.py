from abc import ABC
from logging import debug, error
from threading import Thread
from time import sleep
from typing import List, Callable

from RPi.GPIO import setmode, BOARD, input as gpio_input, add_event_detect, BOTH, setup, IN, PUD_DOWN

from srmlib.gpiocontrollers.constants import PRESSED, RELEASED, ButtonState, FORWARD, BACKWARD, Direction
from srmlib.gpiocontrollers.util import calculate_percentage, clamp

SwitchCallback = Callable[[ButtonState], None]
RotationCallback = Callable[[Direction], None]


class PercentageInput(ABC):
    _percent_changed_callbacks: List[Callable[[float], None]]
    _current_percent: float
    _log_id: str

    def __init__(self, *args, logging_identifier: str = None, initial_percent: float = 0, **kwargs) -> None:
        super(PercentageInput, self).__init__(*args, **kwargs)
        self._percent_changed_callbacks = []
        self._current_percent = initial_percent
        self._log_id = f"[{logging_identifier or f'{self.__class__.__name__}-{id(self)}'}]"

    def add_percent_changed_callback(self, callback: Callable[[float], None]) -> None:
        """
        Registers a new callback to be invoked whenever the input percentage changes.

        :param callback: A function that accepts the current input as a percentage [0, 100].
        """
        self._percent_changed_callbacks.append(callback)

    def _invoke_all_callbacks(self) -> None:
        debug(f"{self._log_id} Input percentage changed to {self._current_percent}. Invoking callbacks.")
        for callback in self._percent_changed_callbacks:
            try:
                callback(self._current_percent)
            except RuntimeError as e:
                error(f"{self._log_id} Switch callback threw an exception: {e}")


class RateLimitedPercentageInput(PercentageInput):
    _desired_percent: float
    _thread: Thread
    _terminated: bool

    def __init__(
            self, percentage_input: PercentageInput, max_percent_change_per_second: float, *args,
            initial_percent: float = 0, **kwargs
    ) -> None:
        super().__init__(*args, initial_percent=initial_percent, **kwargs)

        def percent_changed_handler(percent: float) -> None:
            self._desired_percent = percent
            debug(f"{self._log_id} Desired input percentage changed to {self._current_percent}. "
                  f"Rate-limited invocation to follow.")

        percentage_input.add_percent_changed_callback(percent_changed_handler)

        def acceleration_thread() -> None:
            loop_time = 0.25
            while not self._terminated:
                if self._current_percent != self._desired_percent:
                    is_within_one_step = abs(self._current_percent - self._desired_percent) < max_percent_change_per_second
                    if is_within_one_step:
                        self._current_percent = self._desired_percent
                    else:
                        sign = loop_time if self._current_percent < self._desired_percent else -loop_time
                        self._current_percent = clamp(
                            self._current_percent + (sign * max_percent_change_per_second),
                            0,
                            100
                        )
                    self._invoke_all_callbacks()
                sleep(loop_time)

        self._thread = Thread(target=acceleration_thread)
        self._thread.start()

    def terminate(self) -> None:
        self._terminated = True
        self._thread.join()


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


class RotaryEncoderPercentageInput(PercentageInput):
    def __init__(
            self, rotary_encoder: RotaryEncoderKY040, min_rotary_position: int, max_rotary_position: int,
            initial_rotary_position: int = 0, *args, **kwargs
    ) -> None:
        initial_percent = calculate_percentage(initial_rotary_position, min_rotary_position, max_rotary_position)
        super(RotaryEncoderPercentageInput, self).__init__(*args, initial_percent=initial_percent, **kwargs)
        container = {
            "position": clamp(initial_rotary_position, min_rotary_position, max_rotary_position)
        }

        def rotary_encoder_rotation_handler(direction: Direction) -> None:
            current_position = clamp(
                container["position"] + (1 if direction == FORWARD else -1),
                min_rotary_position,
                max_rotary_position
            )
            self._current_percent = calculate_percentage(current_position, min_rotary_position, max_rotary_position)
            container["position"] = current_position
            self._invoke_all_callbacks()

        rotary_encoder.add_rotation_callback(rotary_encoder_rotation_handler)
