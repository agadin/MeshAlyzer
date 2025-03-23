#!/usr/bin/env python3
"""
Simple ADS1263 test script using spidev and lgpio

This script performs a hardware reset of the ADS1263,
reads the ID register, and prints the raw and extracted
chip ID. (The expected chip ID is 0x01.)
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
    # Bring reset HIGH, then LOW, then HIGH with delays
    lgpio.gpio_write(chip_handle, RST_PIN, 1)
    time.sleep(0.2)
    lgpio.gpio_write(chip_handle, RST_PIN, 0)
    time.sleep(0.2)
    lgpio.gpio_write(chip_handle, RST_PIN, 1)
    time.sleep(0.2)

def read_chip_id(spi, chip_handle):
    """Read the ADS1263 ID register and return the raw byte."""
    # Drive CS low
    lgpio.gpio_write(chip_handle, CS_PIN, 0)
    # Send the RREG command to read the ID register with count=0 (one byte)
    spi.xfer2([CMD_RREG | REG_ID, 0x00])
    # Read one byte (the response)
    result = spi.xfer2([0x00])
    # Drive CS high
    lgpio.gpio_write(chip_handle, CS_PIN, 1)
    return result[0]

def main():
    # Initialize SPI
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 2000000  # 2 MHz (adjust if necessary)
    spi.mode = 0b01           # ADS1263 typically uses mode 1 (try mode 0 if needed)
    # Attempt to disable hardware CS if supported
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

    # Claim RST and CS as outputs and DRDY as input (pass pin numbers as lists)
    try:
        lgpio.gpio_claim_output(chip_handle, [RST_PIN], [0])
        lgpio.gpio_claim_output(chip_handle, [CS_PIN], [1])     # CS initially HIGH
        lgpio.gpio_claim_input(chip_handle, [DRDY_PIN])
    except Exception as e:
        print("Failed to claim GPIO lines:", e)
        spi.close()
        lgpio.gpiochip_close(chip_handle)
        return

    # Reset the ADS1263
    print("Performing hardware reset...")
    hardware_reset(chip_handle)

    # Read the chip ID
    print("Reading chip ID...")
    raw_id = read_chip_id(spi, chip_handle)
    print("Raw ID byte: 0x{:02X}".format(raw_id))

    # The ADS1263 returns the chip ID in the upper bits; shift right 5 bits
    chip_id = raw_id >> 5
    print("Extracted chip ID: 0x{:02X}".format(chip_id))

    if chip_id == 0x01:
        print("ADS1263 chip ID is correct. The board appears to be working!")
    else:
        print("ADS1263 chip ID mismatch. Check wiring and initialization.")

    # Cleanup resources
    spi.close()
    lgpio.gpiochip_close(chip_handle)

if __name__ == "__main__":
    main()
