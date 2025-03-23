#!/usr/bin/env python3
import time
import json
import serial
import ADS1263
import RPi.GPIO as GPIO
class PressureSensorReader:
    def __init__(self, ref_voltage=5.08, channels=None):
        self.REF = ref_voltage  # Reference voltage
        self.channels = channels if channels is not None else [0, 1, 2, 3, 4]
        self.ADC = None

    def setup(self):
        """Initialize the ADS1263 ADC module."""
        self.ADC = ADS1263.ADS1263()
        if self.ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1:
            raise RuntimeError("Failed to initialize ADC1")
        self.ADC.ADS1263_SetMode(0)  # 0 for single-channel mode

    def get_pressure_sensors(self):
        """Retrieve and return pressure sensor values from the ADC."""
        if not self.ADC:
            raise RuntimeError("ADC not initialized. Call setup() first.")
        ADC_Values = self.ADC.ADS1263_GetAll(self.channels)
        sensor_readings = {}
        # Package each channel reading in a dictionary
        for i, raw in zip(self.channels, ADC_Values):
            # Calculate voltage based on sign
            if raw >> 31 == 1:
                value = -(self.REF * 2 - raw * self.REF / 0x80000000)
            else:
                value = raw * self.REF / 0x7FFFFFFF
            sensor_readings[f"channel_{i}"] = value
        return sensor_readings

    def cleanup(self):
        """Safely exit the ADC module."""
        if self.ADC:
            self.ADC.ADS1263_Exit()

def main():
    # Open the UART port (adjust the device file if necessary)
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    reader = PressureSensorReader()
    try:
        reader.setup()
    except Exception as e:
        print(f"Error initializing sensor: {e}")
        return

    print("Starting sensor read and transmit loop...")
    try:
        while True:
            sensor_data = reader.get_pressure_sensors()
            package = {
                "timestamp": time.time(),
                "sensors": sensor_data
            }
            json_data = json.dumps(package)
            # Send data with a newline as a delimiter
            ser.write((json_data + "\n").encode('utf-8'))
            print("Sent:", json_data)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        reader.cleanup()
        ser.close()

def test_serial_connection():
    try:
        ser = serial.Serial('/dev/serial0', 9600, timeout=1)
        print("Starting to send test messages continuously...")
        try:
            while True:
                ser.write(b'hello from pi3\n')
                print("Test message sent successfully.")
                time.sleep(1)  # Adjust the sleep time as needed
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Stopping...")
        finally:
            ser.close()
    except Exception as e:
        print(f"Error during serial test: {e}")

if __name__ == "__main__":
    test_serial_connection()
    main()
