import serial
import time


class MotorController:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        Initialize the serial connection to the Arduino.
        :param port: The serial port (e.g., "COM3" on Windows or "/dev/ttyACM0" on Linux/Mac).
        :param baudrate: Baud rate for the serial connection.
        :param timeout: Read timeout in seconds.
        """
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        # Allow time for the Arduino to reset.
        time.sleep(2)
        print(f"MotorController initialized on port {port}")

    def send_command(self, command):
        """
        Sends a command string to the Arduino and reads any response.
        :param command: Command string to send (e.g., "forward,10").
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

    def run_forward(self, seconds):
        """Run the motors forward for the given number of seconds."""
        command = f"forward,{seconds}"
        self.send_command(command)

    def run_backward(self, seconds):
        """Run the motors backward for the given number of seconds."""
        command = f"backward,{seconds}"
        self.send_command(command)

    def stop(self):
        """Immediately stop the motors."""
        self.send_command("stop")

    def close(self):
        """Close the serial connection."""
        if self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")


def main():
    # Replace 'COM3' with your Arduino's serial port (e.g., '/dev/ttyACM0' on Linux/Mac)
    port = input("Enter Arduino port (e.g., COM3 or /dev/ttyACM0): ").strip()
    controller = MotorController(port=port, baudrate=9600)

    print("Enter commands:")
    print("  forward,<seconds>   -> Run motors forward for <seconds>")
    print("  backward,<seconds>  -> Run motors backward for <seconds>")
    print("  stop                -> Stop motors immediately")
    print("  exit                -> Quit the program")

    try:
        while True:
            user_input = input("Command: ").strip().lower()
            if user_input == "exit":
                break
            elif user_input.startswith("forward"):
                # Expect format "forward,10"
                try:
                    _, sec = user_input.split(',')
                    controller.run_forward(float(sec))
                except ValueError:
                    print("Invalid command format. Use: forward,<seconds>")
            elif user_input.startswith("backward"):
                try:
                    _, sec = user_input.split(',')
                    controller.run_backward(float(sec))
                except ValueError:
                    print("Invalid command format. Use: backward,<seconds>")
            elif user_input == "stop":
                controller.stop()
            else:
                print("Unknown command. Please use forward,<seconds>, backward,<seconds>, stop, or exit.")
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        controller.close()


if __name__ == "__main__":
    main()
