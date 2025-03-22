#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import lgpio


class ValveController:
    """
    A class to control a valve using lgpio.

    This class allows you to initialize the valve with specified supply and vent pins.
    It provides three methods:
      - neutral(): Sets all outputs to HIGH (neutral state).
      - vent(): Activates vent (deflation) mode: sets supply pins LOW and vent pins HIGH.
      - supply(): Activates supply (inflation) mode: sets vent pins LOW and supply pins HIGH.
    Additionally, the get_state() method returns the current state of the valve.

    Note: In this valve configuration, a HIGH output (1) is the neutral/off state,
    while driving a pin LOW (0) activates that channel.
    """

    def __init__(self, supply_pins, vent_pins):
        """
        Initialize the valve controller with the given supply and vent pins.

        :param supply_pins: List of GPIO pin numbers for the supply (inflation) function.
        :param vent_pins: List of GPIO pin numbers for the vent (deflation) function.
        """
        self.supply_pins = supply_pins
        self.vent_pins = vent_pins
        self._state = "neutral"  # initial state
        self.chip = lgpio.gpiochip_open(0)  # open the first GPIO chip

        # Claim each pin as an output and initialize them to HIGH (neutral state)
        for pin in self.supply_pins + self.vent_pins:
            lgpio.gpio_claim_output(self.chip, pin)
            lgpio.gpio_write(self.chip, pin, 1)  # HIGH = neutral/off

    def neutral(self):
        """Set all valve pins to HIGH (neutral state) and update state."""
        for pin in self.supply_pins + self.vent_pins:
            lgpio.gpio_write(self.chip, pin, 1)
        self._state = "neutral"

    def vent(self):
        """
        Activate the valve in vent (deflation) mode:
          - Set supply pins LOW (0)
          - Set vent pins HIGH (1)
        Update the state accordingly.
        """
        for pin in self.supply_pins:
            lgpio.gpio_write(self.chip, pin, 0)
        for pin in self.vent_pins:
            lgpio.gpio_write(self.chip, pin, 1)
        self._state = "vent"

    def supply(self):
        """
        Activate the valve in supply (inflation) mode:
          - Set vent pins LOW (0)
          - Set supply pins HIGH (1)
        Update the state accordingly.
        """
        for pin in self.vent_pins:
            lgpio.gpio_write(self.chip, pin, 0)
        for pin in self.supply_pins:
            lgpio.gpio_write(self.chip, pin, 1)
        self._state = "supply"

    def get_state(self):
        """
        Return the current state of the valve.

        :return: A string indicating the current state ('neutral', 'vent', or 'supply').
        """
        return self._state

    def cleanup(self):
        """Clean up resources by closing the lgpio chip."""
        lgpio.gpiochip_close(self.chip)


# Test the ValveController class when running the script directly.
if __name__ == "__main__":
    try:
        # Define test pins (adjust these based on your actual wiring)
        # Example: Two groups – supply pins for inflation and vent pins for deflation.
        test_supply_pins = [20, 12]  # e.g., PIN1 and PIN3 for inflation
        test_vent_pins = [27, 24]  # e.g., PIN2 and PIN4 for deflation

        valve = ValveController(supply_pins=test_supply_pins, vent_pins=test_vent_pins)

        print("Setting valve to neutral state for 2 seconds.")
        valve.neutral()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Activating vent mode (deflation) for 2 seconds.")
        valve.vent()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Activating supply mode (inflation) for 2 seconds.")
        valve.supply()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Returning to neutral state.")
        valve.neutral()
        print("Current State:", valve.get_state())
        time.sleep(2)

        print("Valve controller test complete.")

    finally:
        valve.cleanup()
        print("lgpio chip closed, cleanup complete.")
