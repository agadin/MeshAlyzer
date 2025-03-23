import serial
import json
import time

class PressureReceiver:
    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        # Open the serial port once
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Opened serial port {self.port} at {self.baudrate} baud.")
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.ser = None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def get_latest_pressure(self):
        """
        Attempt to read a complete JSON message within the timeout period.
        Returns the sensor pressures as a tuple if successful, or None.
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                line = self.ser.readline().decode('utf-8').strip()
            except Exception as e:
                print(f"Error reading line: {e}")
                continue
            if not line:
                # No data in this read; try again
                continue
            print(f"Received line: {line}")
            try:
                data = json.loads(line)
                if "sensors" in data:
                    sensors = data["sensors"]
                    # Extract pressure values for channels 0-3 (default to 0.0 if missing)
                    pressure0 = sensors.get("channel_0", 0.0)
                    pressure1 = sensors.get("channel_1", 0.0)
                    pressure2 = sensors.get("channel_2", 0.0)
                    pressure3 = sensors.get("channel_3", 0.0)
                    return pressure0, pressure1, pressure2, pressure3
            except json.JSONDecodeError:
                print("Invalid JSON received, skipping line.")
                continue
        print("No valid sensor data received within timeout.")
        return None

    def run(self):
        try:
            while True:
                pressures = self.get_latest_pressure()
                if pressures:
                    print(f"Pressure Data: {pressures}")
                else:
                    print("No pressure data available.")
                time.sleep(1)  # Poll every second
        except KeyboardInterrupt:
            print("Receiver exiting...")
        finally:
            self.close()

def main():
    receiver = PressureReceiver()
    receiver.run()

if __name__ == "__main__":
    main()
