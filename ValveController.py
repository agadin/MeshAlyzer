#!/usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as GPIO
import time


class ValveController:
    """
    A class to control a valve using GPIO pins.

    This class allows you to initialize the valve with specified supply and vent pins.
    It provides three methods:
      - neutral(): Turns off all outputs.
      - vent(): Sets the vent pins HIGH (activating vent mode) and supply pins LOW.
      - supply(): Sets the supply pins HIGH (activating supply mode) and vent pins LOW.
    Additionally, the get_state() method returns the current state of the valve.
    """

    def __init__(self, supply_pins, vent_pins):
        """
        Initialize the valve controller with the given supply and vent pins.

        :param supply_pins: List of GPIO pin numbers for the supply function.
        :param vent_pins: List of GPIO pin numbers for the vent function.
        """
        self.supply_pins = supply_pins
        self.vent_pins = vent_pins
        self._state = "neutral"  # Initial state

        # Setup the GPIO pins as outputs and initialize them to LOW
        for pin in self.supply_pins + self.vent_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def neutral(self):
        """Set all valve pins to LOW (neutral state) and update state."""
        for pin in self.supply_pins + self.vent_pins:
            GPIO.output(pin, GPIO.LOW)
        self._state = "neutral"

    def vent(self):
        """Activate the valve in vent mode: vent pins HIGH, supply pins LOW, and update state."""
        for pin in self.supply_pins:
            GPIO.output(pin, GPIO.LOW)
        for pin in self.vent_pins:
            GPIO.output(pin, GPIO.HIGH)
        self._state = "vent"

    def supply(self):
        """Activate the valve in supply mode: supply pins HIGH, vent pins LOW, and update state."""
        for pin in self.vent_pins:
            GPIO.output(pin, GPIO.LOW)
        for pin in self.supply_pins:
            GPIO.output(pin, GPIO.HIGH)
        self._state = "supply"

    def get_state(self):
        """
        Return the current state of the valve.

        :return: A string indicating the current state ('neutral', 'vent', or 'supply').
        """
        return self._state


# Test the ValveController class when running the script directly.
if __name__ == "__main__":
    # Set up GPIO mode (using BCM numbering)
    GPIO.setmode(GPIO.BCM)

    try:
        # Define test pins (modify these based on your actual wiring)
        test_supply_pins = [5]  # Example: GPIO pin 5 for supply
        test_vent_pins = [27]  # Example: GPIO pin 27 for vent

        valve = ValveController(supply_pins=test_supply_pins, vent_pins=test_vent_pins)

        print("Setting valve to neutral state for 2 seconds.")
        valve.neutral()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Activating vent mode for 2 seconds.")
        valve.vent()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Activating supply mode for 2 seconds.")
        valve.supply()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Returning to neutral state.")
        valve.neutral()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Valve controller test complete.")

    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete.")