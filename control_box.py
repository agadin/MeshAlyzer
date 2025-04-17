import threading
import lgpio
import time

# Define a constant for enabling the internal pull-up resistor.
# Adjust this constant to match the one in your lgpio documentation.
# For example, it might be something like lgpio.LG_BIAS_PULL_UP.
PULL_UP_FLAG = lgpio.LG_BIAS_PULL_UP if hasattr(lgpio, 'LG_BIAS_PULL_UP') else 0x01  # placeholder value

class InputMonitor:
    def __init__(self, start_button_pin=17, stop_flag_pin=27, key_switch_pin=22):
        """
        Initialize the InputMonitor with GPIO pins for the inputs.
        Enables internal pull-ups so that when the pins are connected to ground,
        they maintain a defined HIGH level when inactive.
        """
        self.start_button_pin = start_button_pin
        self.stop_flag_pin = stop_flag_pin
        self.key_switch_pin = key_switch_pin

        # Open the first GPIO chip
        self.chip = lgpio.gpiochip_open(0)

        # Claim the pins as inputs **with internal pull-ups enabled.**
        lgpio.gpio_claim_input(self.chip, self.start_button_pin, flags=PULL_UP_FLAG)
        lgpio.gpio_claim_input(self.chip, self.stop_flag_pin, flags=PULL_UP_FLAG)
        lgpio.gpio_claim_input(self.chip, self.key_switch_pin, flags=PULL_UP_FLAG)

        # Initialize states
        self.start_button_state = lgpio.gpio_read(self.chip, self.start_button_pin)
        self.stop_flag_state = lgpio.gpio_read(self.chip, self.stop_flag_pin)
        # Reverse logic for the key switch if necessary
        self.key_switch_state = not lgpio.gpio_read(self.chip, self.key_switch_pin)

        self.running = True
        self.lock = threading.Lock()

    def monitor_inputs(self, callback):
        """
        Monitor the inputs in a thread and call the callback function on state change.
        """
        while self.running:
            with self.lock:
                # Read current states
                new_start_button_state = lgpio.gpio_read(self.chip, self.start_button_pin)
                new_stop_flag_state = lgpio.gpio_read(self.chip, self.stop_flag_pin)
                new_key_switch_state = not lgpio.gpio_read(self.chip, self.key_switch_pin)  # Reverse logic

                # Check for changes and call the callback as needed
                if new_start_button_state != self.start_button_state:
                    self.start_button_state = new_start_button_state
                    callback("start_button", self.start_button_state)

                if new_stop_flag_state != self.stop_flag_state:
                    self.stop_flag_state = new_stop_flag_state
                    callback("stop_flag", self.stop_flag_state)

                if new_key_switch_state != self.key_switch_state:
                    self.key_switch_state = new_key_switch_state
                    callback("key_switch", self.key_switch_state)

            time.sleep(0.1)  # Adjust polling interval as needed

    def start_monitoring(self, callback):
        """Start the monitoring thread."""
        self.thread = threading.Thread(target=self.monitor_inputs, args=(callback,))
        self.thread.daemon = True
        self.thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

    def cleanup(self):
        """Clean up GPIO resources."""
        lgpio.gpiochip_close(self.chip)


# Example usage
if __name__ == "__main__":
    def input_callback(input_name, state):
        print(f"{input_name} changed to {'HIGH' if state else 'LOW'}")

    monitor = InputMonitor()
    try:
        monitor.start_monitoring(input_callback)
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Stopping monitoring...")
    finally:
        monitor.stop_monitoring()
        monitor.cleanup()
