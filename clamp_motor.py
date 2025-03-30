import serial
import time


class MotorController:
    def __init__(self, port="/dev/ttyACM0", baudrate=9600, timeout=1):
        """
        Initialize the serial connection to the Arduino.

        :param port: The serial port (default: "/dev/ttyACM0" for Raspberry Pi).
        :param baudrate: Baud rate for the serial connection.
        :param timeout: Read timeout in seconds.
        """
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        # Allow time for the Arduino to reset.
        print(f"MotorController initialized on port {port}")

    def send_command(self, command):
        """
        Sends a command string to the Arduino and reads any response.

        :param command: Command string to send.
        :return: Response from the Arduino.
        """
        self.ser.reset_input_buffer()
        full_command = command.strip() + '\n'
        self.ser.write(full_command.encode('utf-8'))
        # Wait a little bit for a response.
        time.sleep(0.1)
        response = self.ser.read_all().decode('utf-8')
        print(f"Sent command: {command} | Response: {response}")
        return response

    def close(self):
        """Close the serial connection."""
        if self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")

    def status(self):
        """
        Returns the status of the serial connection.
        """
        return True if self.ser.is_open else False


def main():
    # Use the default port /dev/ttyACM0 for the Raspberry Pi.
    port = "/dev/ttyACM0"
    controller = MotorController(port=port, baudrate=9600)

    print("Enter commands in one of the following formats:")
    print("  1. direction,side,duration")
    print("     - Example: forward,right,10  (runs right motors forward for 10 seconds)")
    print("     - Valid sides: left, right, both")
    print("  2. direction,duration (defaults to both sides)")
    print("     - Example: backward,5 (runs both motors backward for 5 seconds)")
    print("  Other commands:")
    print("     stop   -> Stop motors immediately")
    print("     exit   -> Quit the program")

    try:
        while True:
            user_input = input("Command: ").strip().lower()
            if user_input == "exit":
                break
            elif user_input == "stop":
                controller.send_command("stop")
            else:
                tokens = user_input.split(',')
                if len(tokens) == 2 or len(tokens) == 3:
                    # For a two-token command, assume both sides.
                    if len(tokens) == 2:
                        # Prepend "both" as side
                        command = f"{tokens[0]},both,{tokens[1]}"
                    else:
                        command = user_input
                    controller.send_command(command)
                else:
                    print("Invalid command format.")
                    print("Please use either:")
                    print("  direction,side,duration (e.g., forward,right,10)")
                    print("or")
                    print("  direction,duration (e.g., backward,5)")
                    print("Valid sides: left, right, both; Valid directions: forward, backward.")
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        controller.close()


if __name__ == "__main__":
    main()
