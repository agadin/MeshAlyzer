#!/usr/bin/env python3
"""
/*****************************************************************************
 * | File        :   config.py
 * | Author      :   Waveshare team (modified)
 * | Function    :   Hardware underlying interface using lgpio instead of RPi.GPIO
 * | Info        :
 *----------------
 * | This version:   V1.0 (modified for lgpio)
 * | Date        :   2020-12-12 (original), updated for lgpio
 ******************************************************************************
 *
 * Permission is hereby granted...
 *****************************************************************************/
"""

import os
import sys
import time
import spidev
import lgpio  # Using lgpio instead of RPi.GPIO


class RaspberryPi:
    # Pin definition (BCM numbering)
    RST_PIN = 18
    CS_PIN = 22
    DRDY_PIN = 17

    def __init__(self):
        self.SPI = spidev.SpiDev(0, 0)
        self.chip_handle = None

    def digital_write(self, pin, value):
        lgpio.gpio_write(self.chip_handle, pin, value)

    def digital_read(self, pin):
        return lgpio.gpio_read(self.chip_handle, pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_readbytes(self, n):
        return self.SPI.readbytes(n)

    def module_init(self):
        # Initialize SPI
        self.SPI.max_speed_hz = 2000000
        # You may experiment with mode 0 or mode 1; try mode 0 if mode 1 still fails.
        self.SPI.mode = 0b01

        # Initialize lgpio: open GPIO chip 0
        try:
            self.chip_handle = lgpio.gpiochip_open(0)
        except Exception as e:
            print("Error opening GPIO chip:", e)
            return -1

        # Claim outputs for RST and CS with initial values: RST LOW, CS HIGH
        try:
            # Note: pass pin numbers as a list
            lgpio.gpio_claim_output(self.chip_handle, [self.RST_PIN], 0)
            lgpio.gpio_claim_output(self.chip_handle, [self.CS_PIN], 1)
        except Exception as e:
            print("Error claiming output lines:", e)
            return -1

        # Claim input for DRDY (as a list)
        try:
            lgpio.gpio_claim_input(self.chip_handle, [self.DRDY_PIN])
        except Exception as e:
            print("Error claiming input line:", e)
            return -1

        return 0

    def module_exit(self):
        # Set pins to a safe state and close resources
        try:
            lgpio.gpio_write(self.chip_handle, self.RST_PIN, 0)
            lgpio.gpio_write(self.chip_handle, self.CS_PIN, 0)
            lgpio.gpiochip_close(self.chip_handle)
        except Exception as e:
            print("Error during cleanup:", e)
        self.SPI.close()


class JetsonNano:
    # Pin definition (BCM numbering)
    RST_PIN = 18
    CS_PIN = 22
    DRDY_PIN = 17

    def __init__(self):
        self.SPI = spidev.SpiDev(0, 0)
        import Jetson.GPIO as GPIO
        self.GPIO = GPIO

    def digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        return self.GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_readbytes(self, n):
        return self.SPI.readbytes(n)

    def module_init(self):
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        self.GPIO.setup(self.RST_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.CS_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.DRDY_PIN, self.GPIO.IN)
        self.SPI.max_speed_hz = 2000000
        self.SPI.mode = 0b01
        return 0

    def module_exit(self):
        self.SPI.close()
        self.GPIO.output(self.RST_PIN, 0)
        self.GPIO.cleanup()


hostname = os.popen("uname -n").read().strip()

if hostname == "raspberrypi":
    implementation = RaspberryPi()
else:
    implementation = JetsonNano()

for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))
