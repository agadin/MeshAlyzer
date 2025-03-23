# config.py:
# /*****************************************************************************
# * | File        :   config.py
# * | Author      :   Waveshare team (modified for lgpio)
# * | Function    :   Hardware underlying interface using lgpio
# * | Info        :
# ******************************************************************************/

import time
import lgpio

# Define HIGH and LOW constants
HIGH = 1
LOW = 0

class LgpioInterface:
    # Pin definitions
    RST_PIN = 18
    CS_PIN = 22
    DRDY_PIN = 17

    def __init__(self):
        # Open the default GPIO chip (chip 0)
        self.chip = lgpio.gpiochip_open(0)
        # Set up pins as outputs/inputs
        self.setup_output(self.RST_PIN)
        self.setup_output(self.CS_PIN)
        self.setup_input(self.DRDY_PIN)
        # Open SPI channel using lgpio's SPI functions:
        # Parameters: chip handle, SPI channel (0), speed, SPI mode (0b01)
        self.spi_handle = lgpio.spi_open(self.chip, 0, 2000000, 0b01)

    def setup_output(self, pin):
        # Claim the pin for output with an initial LOW state
        lgpio.gpio_claim_output(self.chip, pin, LOW)

    def setup_input(self, pin):
        # Claim the pin for input
        lgpio.gpio_claim_input(self.chip, pin)

    def digital_write(self, pin, value):
        lgpio.gpio_write(self.chip, pin, value)

    def digital_read(self, pin):
        return lgpio.gpio_read(self.chip, pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        # Convert list of integers to bytes and write via SPI
        lgpio.spi_write(self.spi_handle, bytes(data))

    def spi_readbytes(self, length):
        # Read 'length' bytes via SPI and return as a list of integers
        result = lgpio.spi_read(self.spi_handle, length)
        return list(result)

    def module_init(self):
        # Initialization is handled in __init__
        return 0

    def module_exit(self):
        lgpio.spi_close(self.spi_handle)
        lgpio.gpiochip_close(self.chip)


# Expose functions and constants at module level.
implementation = LgpioInterface()
for func in [x for x in dir(implementation) if not x.startswith('_')]:
    globals()[func] = getattr(implementation, func)

# Also expose HIGH, LOW, and pin definitions.
RST_PIN = LgpioInterface.RST_PIN
CS_PIN = LgpioInterface.CS_PIN
DRDY_PIN = LgpioInterface.DRDY_PIN
