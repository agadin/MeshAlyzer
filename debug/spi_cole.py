#!/usr/bin/env python3
"""
Debugging script for ADS1263 initialization issue.
"""

import spidev
import lgpio
import time

# ADS1263 definitions
REG_ID = 0x00
CMD_RREG = 0x20  # Read register command base

# Pin definitions (BCM numbering)
RST_PIN = 18   # Reset pin
CS_PIN = 22    # Chip Select pin (handled manually via lgpio)
DRDY_PIN = 17  # Data Ready pin

def hardware_reset(chip_handle):
    """Perform a hardware reset on the ADS1263."""
    print("Performing hardware reset...")
    lgpio.gpio_write(chip_handle, RST_PIN, 1)
    time.sleep(0.2)
    lgpio.gpio_write(chip_handle, RST_PIN, 0)
    time.sleep(0.2)
    lgpio.gpio_write(chip_handle, RST_PIN, 1)
    time.sleep(0.2)
    print("Hardware reset complete.")

def read_chip_id(spi, chip_handle):
    """Read the ADS1263 ID register and return the raw byte."""
    print("Reading chip ID...")
    lgpio.gpio_write(chip_handle, CS_PIN, 0)
    spi.xfer2([CMD_RREG | REG_ID, 0x00])
    result = spi.xfer2([0x00])
    lgpio.gpio_write(chip_handle, CS_PIN, 1)
    print(f"Raw ID byte: 0x{result[0]:02X}")
    return result[0]

def main():
    # Initialize SPI
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 2000000  # 2 MHz (adjust if necessary)
    spi.mode = 0b01           # ADS1263 typically uses mode 1 (try mode 0 if needed)
    try:
        spi.no_cs = True
    except Exception as e:
        print("Warning: Could not disable hardware CS:", e)

    # Initialize lgpio: open GPIO chip 0 and claim pins
    try:
        chip_handle = lgpio.gpiochip_open(0)
    except Exception as e:
        print("Failed to open GPIO chip:", e)
        spi.close()
        return

    try:
        lgpio.gpio_claim_output(chip_handle, [RST_PIN], 0)  # RST initially LOW
        lgpio.gpio_claim_output(chip_handle, [CS_PIN], 1)  # CS initially HIGH
        lgpio.gpio_claim_input(chip_handle, [DRDY_PIN])
    except Exception as e:
        print("Failed to claim GPIO lines:", e)
        spi.close()
        lgpio.gpiochip_close(chip_handle)
        return

    # Reset the ADS1263
    hardware_reset(chip_handle)

    # Read the chip ID
    raw_id = read_chip_id(spi, chip_handle)
    chip_id = raw_id >> 5
    print(f"Extracted chip ID: 0x{chip_id:02X}")

    if chip_id == 0x01:
        print("ADS1263 chip ID is correct. The board appears to be working!")
    else:
        print("ADS1263 chip ID mismatch. Check wiring and initialization.")

    # Cleanup resources
    spi.close()
    lgpio.gpiochip_close(chip_handle)

if __name__ == "__main__":
    main()