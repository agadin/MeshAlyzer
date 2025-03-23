#!/usr/bin/env python3
import time
import json
import socket
import logging
from logging.handlers import RotatingFileHandler
import ADS1263

LOG_FILE = "/home/lakelab/pressure_sensor.log"
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# Configure logging with RotatingFileHandler
logging.basicConfig(
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT)],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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
        logging.info("ADC initialized successfully.")

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
            logging.info("ADC cleanup complete.")

def run_client():
    SERVER_IP = "10.42.0.1"
    SERVER_PORT = 65432

    reader = PressureSensorReader()
    try:
        reader.setup()
    except Exception as e:
        logging.error(f"Sensor initialization failed: {e}")
        return

    try:
        logging.info(f"Attempting to connect to server at {SERVER_IP}:{SERVER_PORT}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            logging.info("Connected to server. Starting data transmission...")

            while True:
                sensor_data = reader.get_pressure_sensors()
                package = {
                    "timestamp": time.time(),
                    "sensors": sensor_data
                }
                json_data = json.dumps(package)
                s.sendall((json_data + "\n").encode("utf-8"))
                time.sleep(0.01)

    except Exception as e:
        logging.error(f"Client encountered an error: {e}")
    finally:
        reader.cleanup()

if __name__ == "__main__":
    while True:
        run_client()
        logging.warning("Restarting script after failure...")
        time.sleep(2)