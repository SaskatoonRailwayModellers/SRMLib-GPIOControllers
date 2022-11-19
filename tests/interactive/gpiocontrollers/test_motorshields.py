from time import sleep
from unittest import TestCase
from RPi.GPIO import setmode, BOARD, cleanup as cleanup_gpio

from srmlib.gpiocontrollers.motorshields import CytronMD10C
from srmlib.gpiocontrollers.constants import FORWARD, BACKWARD


class CytronMD10CTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pwm_pin = int(input("Enter pwm pin number: "))
        cls.direction_pin = int(input("Enter direction pin number: "))

    def setUp(self) -> None:
        setmode(BOARD)
        self.controller = CytronMD10C(self.direction_pin, self.pwm_pin)

    def tearDown(self) -> None:
        cleanup_gpio()

    def test__should_move_forward(self) -> None:
        # Arrange
        print(f"!!! TEST - Expected Observation: Engine should run FORWARD for 3 seconds then stop")
        input("Press Enter to run test...")

        # Act
        self.controller.direction = FORWARD
        self.controller.speed = 50
        sleep(3)
        self.controller.speed = 0

        # Assert
        test_succeeded = input("Did the engine perform as expected? (Y/n) ").lower() in {"", "y"}
        self.assertTrue(test_succeeded)

    def test__should_move_backward(self) -> None:
        # Arrange
        print(f"!!! TEST - Expected Observation: Engine should run BACKWARD for 3 seconds then stop")
        input("Press Enter to run test...")

        # Act
        self.controller.direction = BACKWARD
        self.controller.speed = 50
        sleep(3)
        self.controller.speed = 0

        # Assert
        test_succeeded = input("Did the engine perform as expected? (Y/n) ").lower() in {"", "y"}
        self.assertTrue(test_succeeded)

    def test__should_ramp_up_speed(self) -> None:
        # Arrange
        print(f"!!! TEST - Expected Observation: Engine should run FORWARD, starting slowly and speeding up for 10 seconds total then stop")
        input("Press Enter to run test...")

        # Act
        self.controller.direction = FORWARD
        self.controller.speed = 20
        sleep(2)
        self.controller.speed = 40
        sleep(2)
        self.controller.speed = 60
        sleep(2)
        self.controller.speed = 80
        sleep(2)
        self.controller.speed = 100
        sleep(2)
        self.controller.speed = 0

        # Assert
        test_succeeded = input("Did the engine perform as expected? (Y/n) ").lower() in {"", "y"}
        self.assertTrue(test_succeeded)
