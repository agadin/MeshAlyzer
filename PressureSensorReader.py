import serial
import json
import time

class PressureReceiver:
    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def get_latest_pressure(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                latest_line = None

                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        latest_line = data
                    except json.JSONDecodeError:
                        continue

                if latest_line and "sensors" in latest_line:
                    sensors = latest_line["sensors"]
                    # Safely extract values for 4 channels
                    pressure0 = sensors.get("channel_0", 0.0)
                    pressure1 = sensors.get("channel_1", 0.0)
                    pressure2 = sensors.get("channel_2", 0.0)
                    pressure3 = sensors.get("channel_3", 0.0)
                    return pressure0, pressure1, pressure2, pressure3
                else:
                    return 0.0, 0.0, 0.0, 0.0  # fallback values
        except Exception as e:
            print(f"Error reading serial: {e}")
            return 0.0, 0.0, 0.0, 0.0
