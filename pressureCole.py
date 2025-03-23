#!/usr/bin/env python3
import time
import json
import socket
import ADS1263

class PressureSensorReader:
    def __init__(self, ref_voltage=5.08, channels=None):
        self.REF = ref_voltage
        self.channels = channels if channels is not None else [0, 1, 2, 3, 4]
        self.ADC = None

    def setup(self):
        self.ADC = ADS1263.ADS1263()
        if self.ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1:
            raise RuntimeError("Failed to initialize ADC1")
        self.ADC.ADS1263_SetMode(0)

    def get_pressure_sensors(self):
        if not self.ADC:
            raise RuntimeError("ADC not initialized. Call setup() first.")
        ADC_Values = self.ADC.ADS1263_GetAll(self.channels)
        sensor_readings = {}
        for i, raw in zip(self.channels, ADC_Values):
            if raw >> 31 == 1:
                value = -(self.REF * 2 - raw * self.REF / 0x80000000)
            else:
                value = raw * self.REF / 0x7FFFFFFF
            sensor_readings[f"channel_{i}"] = value
        return sensor_readings

    def cleanup(self):
        if self.ADC:
            self.ADC.ADS1263_Exit()

def main():
    reader = PressureSensorReader()
    try:
        reader.setup()
    except Exception as e:
        print(f"[ERROR] Sensor init failed: {e}")
        return

    SERVER_IP = "10.42.0.1"
    SERVER_PORT = 65432

    print(f"[CLIENT] Connecting to {SERVER_IP}:{SERVER_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            print("[CLIENT] Connected. Starting data transmission...")

            while True:
                sensor_data = reader.get_pressure_sensors()
                package = {
                    "timestamp": time.time(),
                    "sensors": sensor_data
                }
                json_data = json.dumps(package)
                s.sendall((json_data + "\n").encode("utf-8"))
                print("[CLIENT] Sent:", json_data)
                time.sleep(0.01)

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
    finally:
        reader.cleanup()

if __name__ == "__main__":
    main()
