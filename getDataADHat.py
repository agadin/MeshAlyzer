import spidev
import time
import numpy as np

# ADC Configuration (adjust based on Waveshare documentation)
spi = spidev.SpiDev()
spi.open(0, 0) # Bus 0, Chip Select 0 (CE0 pin)
spi.max_speed_hz = 1000000  # 1 MHz SPI clock (adjust as needed)

NUM_CHANNELS = 8 # Assuming 8 channels on the ADC HAT

def read_adc(channel):
    """Reads the ADC value from the specified channel (0-7)."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")

    # Construct SPI message (adjust based on ADC HAT datasheet!)
    cmd = 0b11000000  # Start bit + Single-ended mode
    cmd |= (channel << 3)  # Channel select
    cmd_bytes = [cmd, 0x00, 0x00] #cmd MSB first

    # Perform SPI transaction
    response = spi.xfer2(cmd_bytes)

    # Extract ADC value (adjust based on ADC HAT datasheet!)
    adc_value = ((response[1] & 0x0F) << 8) | response[2]
    return adc_value

# Example usage
try:
    while True:
        for channel in range(NUM_CHANNELS):
            adc_value = read_adc(channel)
            print(f"Channel {channel}: ADC Value = {adc_value}")
        time.sleep(0.5) # Read every 0.5 seconds

except KeyboardInterrupt:
    spi.close()
    print("SPI connection closed.")
