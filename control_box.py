import threading
import lgpio
import time

class InputMonitor:
    def __init__(self, start_button_pin=17, stop_flag_pin=27, key_switch_pin=22):
        """
        Initialize the InputMonitor with GPIO pins for the inputs.
        :param start_button_pin: GPIO pin for the start button.
        :param stop_flag_pin: GPIO pin for the stop flag.
        :param key_switch_pin: GPIO pin for the key switch.
        """
        self.start_button_pin = start_button_pin
        self.stop_flag_pin = stop_flag_pin
        self.key_switch_pin = key_switch_pin

        self.chip = lgpio.gpiochip_open(0)  # Open the first GPIO chip

        # Claim the pins as inputs
        lgpio.gpio_claim_input(self.chip, self.start_button_pin)
        lgpio.gpio_claim_input(self.chip, self.stop_flag_pin)
        lgpio.gpio_claim_input(self.chip, self.key_switch_pin)

        # Initialize states
        self.start_button_state = lgpio.gpio_read(self.chip, self.start_button_pin)
        self.stop_flag_state = lgpio.gpio_read(self.chip, self.stop_flag_pin)
        self.key_switch_state = not lgpio.gpio_read(self.chip, self.key_switch_pin)  # Reverse logic

        self.key_switch_last_update = 0  # Timestamp for debounce
        self.running = True
        self.lock = threading.Lock()

    def monitor_inputs(self, callback):
        """
        Monitor the inputs in a thread and call the callback function on state change.
        :param callback: Function to call when an input state changes.
        """
        while self.running:
            with self.lock:
                # Read current states
                new_start_button_state = lgpio.gpio_read(self.chip, self.start_button_pin)
                new_stop_flag_state = lgpio.gpio_read(self.chip, self.stop_flag_pin)
                new_key_switch_state = not lgpio.gpio_read(self.chip, self.key_switch_pin)  # Reverse logic

                # Check for changes
                if new_start_button_state != self.start_button_state:
                    self.start_button_state = new_start_button_state
                    callback("start_button", self.start_button_state)

                if new_stop_flag_state != self.stop_flag_state:
                    self.stop_flag_state = new_stop_flag_state
                    callback("stop_flag", self.stop_flag_state)

                    # Debounce logic for key_switch
                    current_time = time.time()
                    if new_key_switch_state != self.key_switch_state and current_time - self.key_switch_last_update >= 1:
                        self.key_switch_state = new_key_switch_state
                        self.key_switch_last_update = current_time
                        callback("key_switch", self.key_switch_state)

            time.sleep(0.1)  # Polling interval

    def start_monitoring(self, callback):
        """
        Start the monitoring thread.
        :param callback: Function to call when an input state changes.
        """
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
    # start_button: Connect to GPIO pin 17.
    # stop_flag: Connect to GPIO pin 27.
    # key_switch: Connect to GPIO pin 22.
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