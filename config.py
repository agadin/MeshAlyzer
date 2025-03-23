#!/usr/bin/env python3
"""
/*****************************************************************************
 * | File        :   config.py
 * | Author      :   Waveshare team (modified)
 * | Function    :   Hardware underlying interface using lgpio for Raspberry Pi
 * | Info        :
 *----------------
 * | This version:   V1.0 (modified)
 * | Date        :   2020-12-12 (original), updated for lgpio
 * | Info        :
 ******************************************************************************
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction...
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND...
 *
 *****************************************************************************/
"""

import os
import sys
import time
import spidev
import lgpio  # Using lgpio instead of RPi.GPIO


class RaspberryPi:
    # Pin definition
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
        self.SPI.mode = 0b01

        # Initialize lgpio: open GPIO chip 0
        self.chip_handle = lgpio.gpiochip_open(0)
        # Claim outputs for RST and CS with initial values: RST LOW, CS HIGH
        lgpio.gpio_claim_output(self.chip_handle, self.RST_PIN, 0)
        lgpio.gpio_claim_output(self.chip_handle, self.CS_PIN, 1)
        # Claim input for DRDY
        lgpio.gpio_claim_input(self.chip_handle, self.DRDY_PIN)
        return 0

    def module_exit(self):
        # Set pins to a safe state and close resources
        lgpio.gpio_write(self.chip_handle, self.RST_PIN, 0)
        lgpio.gpio_write(self.chip_handle, self.CS_PIN, 0)
        self.SPI.close()
        lgpio.gpiochip_close(self.chip_handle)


class JetsonNano:
    # Pin definition
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
