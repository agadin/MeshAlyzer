import time
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

    def get_pressure_sensors(self, specific_channel=None):
        """Retrieve and return pressure sensor values from the ADC."""
        if not self.ADC:
            raise RuntimeError("ADC not initialized. Call setup() first.")

        ADC_Values = self.ADC.ADS1263_GetAll(self.channels)
        sensor_readings = []

        channels_to_read = [specific_channel] if specific_channel is not None else self.channels

        for i in channels_to_read:
            if ADC_Values[i] >> 31 == 1:
                sensor_readings.append(-(self.REF * 2 - ADC_Values[i] * self.REF / 0x80000000))
            else:
                sensor_readings.append(ADC_Values[i] * self.REF / 0x7FFFFFFF)

        return tuple(sensor_readings)

    def cleanup(self):
        """Safely exit the ADC module."""
        if self.ADC:
            self.ADC.ADS1263_Exit()


# Example usage
if __name__ == "__main__":
    try:
        reader = PressureSensorReader()
        reader.setup()

        while True:
            sensor_values = reader.get_pressure_sensors()
            for sensor, value in sensor_values.items():
                print(f"{sensor}: {value:.6f} V")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
        reader.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        reader.cleanup()
