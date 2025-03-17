import lgpio
import time

# Open the SPI device
h = lgpio.gpiochip_open(0)
spi_h = lgpio.spi_open(0, 0, 50000)  # Bus 0, CE0, 50kHz

def read_adc(channel):
    """Reads the ADC value from the specified channel (0-7)."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")

    # Construct SPI message
    cmd = 0b11000000 | (channel << 3)  # Start bit + Single-ended mode + channel
    cmd_bytes = [cmd, 0x00, 0x00]  # Command bytes

    # Perform SPI transaction
    count, data = lgpio.spi_transfer(spi_h, cmd_bytes)

    # Extract ADC value
    adc_value = ((data[1] & 0x0F) << 8) | data[2]
    return adc_value

try:
    while True:
        adc_value = read_adc(0)  # Reading from channel 0 (IN0)
        voltage = (adc_value * 5.0) / 4095  # Assuming a 12-bit ADC with 5V reference
        print(f"ADC Value: {adc_value}, Voltage: {voltage:.6f} V")
        time.sleep(0.5)

except KeyboardInterrupt:
    lgpio.spi_close(spi_h)
    lgpio.gpiochip_close(h)
    print("\nProgram terminated.")
