from unittest import TestCase

from RPi.GPIO import setmode, BOARD, cleanup, remove_event_detect

from srmlib.gpiocontrollers.constants import Direction, FORWARD, BACKWARD
from srmlib.gpiocontrollers.inputs import RotaryEncoderKY040


class RotaryEncoderKY040Test(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clk_pin = int(input("Enter clk pin number: "))
        cls.dt_pin = int(input("Enter dt pin number: "))
        cls.sw_pin = int(input("Enter sw pin number: "))

    def setUp(self) -> None:
        setmode(BOARD)
        self.controller = RotaryEncoderKY040(self.clk_pin, self.dt_pin, self.sw_pin)

    def tearDown(self) -> None:
        remove_event_detect(self.clk_pin)
        remove_event_detect(self.dt_pin)
        remove_event_detect(self.sw_pin)
        cleanup()

    def test__add_rotation_callback__should_register_function_to_track_rotations(self) -> None:
        # Arrange
        print("!!! TEST - Expected Observation: Rotating CLOCKWISE should increase the printed value, "
              "and rotating COUNTER-CLOCKWISE should decrease it")
        container = {"value": 0}

        def handler(direction: Direction) -> None:
            container["value"] += (1 if direction == FORWARD else -1)
            print(f"Callback invoked, value: {container['value']}")

        # Act
        self.controller.add_rotation_callback(handler)

        # Assert
        input("Experiment with rotation, then press enter to continue...\n")
        test_succeeded = input("Did the controller perform as expected? (Y/n) ").lower() in {"", "y"}
        self.assertTrue(test_succeeded)

    def test__add_rotation_callback__should_register_multiple_functions_to_track_rotations(self) -> None:
        # Arrange
        print("!!! TEST - Expected Observation: Rotating CLOCKWISE should increase the 'positive' printed value, "
              "and rotating COUNTER-CLOCKWISE should decrease the 'negative' printed value. The two values should "
              "be distinct and update separately.")
        container = {"positive": 0, "negative": 0}

        def positive_handler(direction: Direction) -> None:
            if direction == FORWARD:
                container["positive"] += 1
                print(f"Positive callback invoked, value: {container['positive']}")

        def negative_handler(direction: Direction) -> None:
            if direction == BACKWARD:
                container["negative"] -= 1
                print(f"Negative callback invoked, value: {container['negative']}")

        # Act
        self.controller.add_rotation_callback(positive_handler)
        self.controller.add_rotation_callback(negative_handler)

        # Assert
        input("Experiment with rotation, then press enter to continue...\n")
        test_succeeded = input("Did the controller perform as expected? (Y/n) ").lower() in {"", "y"}
        self.assertTrue(test_succeeded)
