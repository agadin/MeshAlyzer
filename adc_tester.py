import lgpio
import time

# Raspberry Pi GPIO and SPI settings
SPI_CHANNEL = 0    # SPI0 (CE0)
SPI_SPEED = 1000000  # 1 MHz
DRDY_PIN = 7       # Data Ready (DRDY) pin – originally used by SPI as CE1
CS_PIN = 16         # Chip Select (CS) pin

# ADS1256 Commands
CMD_WAKEUP = 0x00
CMD_RDATA = 0x01
CMD_RDATAC = 0x03
CMD_SDATAC = 0x0F
CMD_RREG = 0x10
CMD_WREG = 0x50
CMD_SELFCAL = 0xF0

# Register addresses
REG_STATUS = 0x00
REG_MUX = 0x01
REG_ADCON = 0x02
REG_DRATE = 0x03

# Data rate settings
DRATE_100SPS = 0xF0  # 100 Samples per second

# Initialize the lgpio interface
h = lgpio.gpiochip_open(0)

# Claim the chip-select pin as output and set it high (inactive)
lgpio.gpio_claim_output(h, CS_PIN)
lgpio.gpio_write(h, CS_PIN, 1)

# Set up the DRDY pin as input
lgpio.gpio_claim_input(h, DRDY_PIN)

# Open SPI interface with the flag to disable automatic chip select (SPI_NO_CS = 0x04)
spi = lgpio.spi_open(h, SPI_CHANNEL, SPI_SPEED, 0x04)

def spi_transfer(data, read_length=0):
    """Performs an SPI transfer with manual control of the CS pin."""
    # Assert CS (active low)
    lgpio.gpio_write(h, CS_PIN, 0)
    # Write data
    lgpio.spi_write(h, spi, data)
    result = None
    # If a read is expected, perform the SPI read while keeping CS low.
    if read_length:
        result = lgpio.spi_read(h, spi, read_length)[1]
    # Deassert CS after transaction
    lgpio.gpio_write(h, CS_PIN, 1)
    return result

def send_command(command):
    """Sends a single command to the ADS1256."""
    spi_transfer([command])

def read_register(reg):
    """Reads a single register from the ADS1256."""
    # Begin transaction: send the register read command and the byte count (0x00)
    lgpio.gpio_write(h, CS_PIN, 0)
    lgpio.spi_write(h, spi, [CMD_RREG | reg, 0x00])
    # Read back one byte (the register value)
    result = lgpio.spi_read(h, spi, 1)[1][0]
    lgpio.gpio_write(h, CS_PIN, 1)
    return result

def write_register(reg, value):
    """Writes a value to a register on the ADS1256."""
    lgpio.gpio_write(h, CS_PIN, 0)
    lgpio.spi_write(h, spi, [CMD_WREG | reg, 0x00, value])
    lgpio.gpio_write(h, CS_PIN, 1)

def wait_for_drdy():
    """Waits for the DRDY pin to go low (data ready)."""
    while lgpio.gpio_read(h, DRDY_PIN):
        time.sleep(0.001)

def read_adc(channel):
    """Reads a single-ended ADC value from the given channel."""
    wait_for_drdy()  # Wait until DRDY goes low

    # Set multiplexer: select the desired channel (AINx vs AINCOM)
    write_register(REG_MUX, (channel << 4) | 0x08)
    send_command(CMD_WAKEUP)
    send_command(CMD_RDATA)

    # For the ADC data read, perform the SPI read manually
    lgpio.gpio_write(h, CS_PIN, 0)
    raw_data = lgpio.spi_read(h, spi, 3)[1]
    lgpio.gpio_write(h, CS_PIN, 1)

    # Assemble 24-bit result
    result = (raw_data[0] << 16) | (raw_data[1] << 8) | raw_data[2]

    # Convert to signed 24-bit integer
    if result & 0x800000:
        result -= 0x1000000

    return result

def setup_ads1256():
    """Configures the ADS1256."""
    send_command(CMD_SDATAC)       # Stop continuous mode
    write_register(REG_STATUS, 0x06)  # Enable auto-calibration
    write_register(REG_ADCON, 0x00)   # Gain = 1, disable clock output
    write_register(REG_DRATE, DRATE_100SPS)  # Set data rate
    send_command(CMD_SELFCAL)      # Run self-calibration
    time.sleep(0.1)

try:
    print("Initializing ADS1256...")
    setup_ads1256()

    while True:
        value = read_adc(0)  # Read ADC value from Channel 0
        voltage = (value * 5.0) / 0x7FFFFF  # Convert ADC reading to voltage (assuming 5V reference)
        print(f"ADC Channel 0: {value} ({voltage:.5f} V)")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    lgpio.spi_close(h, spi)
    lgpio.gpiochip_close(h)
