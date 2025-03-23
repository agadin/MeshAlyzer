#!/usr/bin/env python3
"""
ADS1263.py - ADS1263 driver for Raspberry Pi using spidev for SPI and lgpio for GPIO
Based on Waveshare code, modified to use spidev and lgpio (do NOT use RPi.GPIO)
"""

import spidev
import lgpio
import time

# ----- Configuration Functions and Global Variables -----

# Define your GPIO pin numbers (adjust these to match your wiring)
RST_PIN = 17  # Reset pin
CS_PIN = 27  # Chip Select pin
DRDY_PIN = 22  # Data Ready pin

# Global handles for SPI and GPIO chip
spi = None
chip_handle = None


def module_init():
    """Initialize SPI (using spidev) and GPIO (using lgpio)."""
    global spi, chip_handle
    # --- Initialize SPI ---
    spi = spidev.SpiDev()
    # Open SPI bus 0, device 0 (modify if needed)
    spi.open(0, 0)
    spi.max_speed_hz = 500000  # Set the SPI speed as needed
    spi.mode = 0b01  # Set SPI mode (adjust if necessary)

    # --- Initialize LGPIO ---
    chip_handle = lgpio.gpiochip_open(0)  # Open the first GPIO chip
    # Claim outputs for RST and CS (set initial values: RST LOW, CS HIGH)
    lgpio.gpio_claim_output(chip_handle, RST_PIN, 0)
    lgpio.gpio_claim_output(chip_handle, CS_PIN, 1)
    # Claim input for DRDY
    lgpio.gpio_claim_input(chip_handle, DRDY_PIN)
    return 0


def module_exit():
    """Clean up SPI and GPIO resources."""
    global spi, chip_handle
    if spi:
        spi.close()
    if chip_handle:
        lgpio.gpiochip_close(chip_handle)


def digital_write(pin, value):
    """Set the specified GPIO pin to the given value using lgpio."""
    lgpio.gpio_write(chip_handle, pin, value)


def digital_read(pin):
    """Read and return the value of the specified GPIO pin using lgpio."""
    return lgpio.gpio_read(chip_handle, pin)


def spi_writebyte(data):
    """Write a list of byte values over SPI."""
    spi.xfer2(data)


def spi_readbytes(n):
    """Read n bytes over SPI by transferring dummy bytes (0x00)."""
    return spi.xfer2([0x00] * n)


def delay_ms(ms):
    """Delay execution for the specified number of milliseconds."""
    time.sleep(ms / 1000.0)


# ----- ADS1263 Constants -----

# Gain settings for ADC1
ADS1263_GAIN = {
    'ADS1263_GAIN_1': 0,
    'ADS1263_GAIN_2': 1,
    'ADS1263_GAIN_4': 2,
    'ADS1263_GAIN_8': 3,
    'ADS1263_GAIN_16': 4,
    'ADS1263_GAIN_32': 5,
    'ADS1263_GAIN_64': 6,
}

# Gain settings for ADC2
ADS1263_ADC2_GAIN = {
    'ADS1263_ADC2_GAIN_1': 0,
    'ADS1263_ADC2_GAIN_2': 1,
    'ADS1263_ADC2_GAIN_4': 2,
    'ADS1263_ADC2_GAIN_8': 3,
    'ADS1263_ADC2_GAIN_16': 4,
    'ADS1263_ADC2_GAIN_32': 5,
    'ADS1263_ADC2_GAIN_64': 6,
    'ADS1263_ADC2_GAIN_128': 7,
}

# Data rates for ADC1
ADS1263_DRATE = {
    'ADS1263_38400SPS': 0xF,
    'ADS1263_19200SPS': 0xE,
    'ADS1263_14400SPS': 0xD,
    'ADS1263_7200SPS': 0xC,
    'ADS1263_4800SPS': 0xB,
    'ADS1263_2400SPS': 0xA,
    'ADS1263_1200SPS': 0x9,
    'ADS1263_400SPS': 0x8,
    'ADS1263_100SPS': 0x7,
    'ADS1263_60SPS': 0x6,
    'ADS1263_50SPS': 0x5,
    'ADS1263_20SPS': 0x4,
    'ADS1263_16d6SPS': 0x3,
    'ADS1263_10SPS': 0x2,
    'ADS1263_5SPS': 0x1,
    'ADS1263_2d5SPS': 0x0,
}

# Data rates for ADC2
ADS1263_ADC2_DRATE = {
    'ADS1263_ADC2_10SPS': 0,
    'ADS1263_ADC2_100SPS': 1,
    'ADS1263_ADC2_400SPS': 2,
    'ADS1263_ADC2_800SPS': 3,
}

# Delay times
ADS1263_DELAY = {
    'ADS1263_DELAY_0s': 0,
    'ADS1263_DELAY_8d7us': 1,
    'ADS1263_DELAY_17us': 2,
    'ADS1263_DELAY_35us': 3,
    'ADS1263_DELAY_169us': 4,
    'ADS1263_DELAY_139us': 5,
    'ADS1263_DELAY_278us': 6,
    'ADS1263_DELAY_555us': 7,
    'ADS1263_DELAY_1d1ms': 8,
    'ADS1263_DELAY_2d2ms': 9,
    'ADS1263_DELAY_4d4ms': 10,
    'ADS1263_DELAY_8d8ms': 11,
}

# DAC voltage levels
ADS1263_DAC_VOLT = {
    'ADS1263_DAC_VLOT_4_5': 0b01001,
    'ADS1263_DAC_VLOT_3_5': 0b01000,
    'ADS1263_DAC_VLOT_3': 0b00111,
    'ADS1263_DAC_VLOT_2_75': 0b00110,
    'ADS1263_DAC_VLOT_2_625': 0b00101,
    'ADS1263_DAC_VLOT_2_5625': 0b00100,
    'ADS1263_DAC_VLOT_2_53125': 0b00011,
    'ADS1263_DAC_VLOT_2_515625': 0b00010,
    'ADS1263_DAC_VLOT_2_5078125': 0b00001,
    'ADS1263_DAC_VLOT_2_5': 0b00000,
    'ADS1263_DAC_VLOT_2_4921875': 0b10001,
    'ADS1263_DAC_VLOT_2_484375': 0b10010,
    'ADS1263_DAC_VLOT_2_46875': 0b10011,
    'ADS1263_DAC_VLOT_2_4375': 0b10100,
    'ADS1263_DAC_VLOT_2_375': 0b10101,
    'ADS1263_DAC_VLOT_2_25': 0b10110,
    'ADS1263_DAC_VLOT_2': 0b10111,
    'ADS1263_DAC_VLOT_1_5': 0b11000,
    'ADS1263_DAC_VLOT_0_5': 0b11001,
}

# Register definitions
ADS1263_REG = {
    'REG_ID': 0,
    'REG_POWER': 1,
    'REG_INTERFACE': 2,
    'REG_MODE0': 3,
    'REG_MODE1': 4,
    'REG_MODE2': 5,
    'REG_INPMUX': 6,
    'REG_OFCAL0': 7,
    'REG_OFCAL1': 8,
    'REG_OFCAL2': 9,
    'REG_FSCAL0': 10,
    'REG_FSCAL1': 11,
    'REG_FSCAL2': 12,
    'REG_IDACMUX': 13,
    'REG_IDACMAG': 14,
    'REG_REFMUX': 15,
    'REG_TDACP': 16,
    'REG_TDACN': 17,
    'REG_GPIOCON': 18,
    'REG_GPIODIR': 19,
    'REG_GPIODAT': 20,
    'REG_ADC2CFG': 21,
    'REG_ADC2MUX': 22,
    'REG_ADC2OFC0': 23,
    'REG_ADC2OFC1': 24,
    'REG_ADC2FSC0': 25,
    'REG_ADC2FSC1': 26,
}

# Command definitions
ADS1263_CMD = {
    'CMD_RESET': 0x06,
    'CMD_START1': 0x08,
    'CMD_STOP1': 0x0A,
    'CMD_START2': 0x0C,
    'CMD_STOP2': 0x0E,
    'CMD_RDATA1': 0x12,
    'CMD_RDATA2': 0x14,
    'CMD_SYOCAL1': 0x16,
    'CMD_SYGCAL1': 0x17,
    'CMD_SFOCAL1': 0x19,
    'CMD_SYOCAL2': 0x1B,
    'CMD_SYGCAL2': 0x1C,
    'CMD_SFOCAL2': 0x1E,
    'CMD_RREG': 0x20,
    'CMD_RREG2': 0x00,
    'CMD_WREG': 0x40,
    'CMD_WREG2': 0x00,
}


# ----- ADS1263 Driver Class -----

class ADS1263:
    def __init__(self):
        self.rst_pin = RST_PIN
        self.cs_pin = CS_PIN
        self.drdy_pin = DRDY_PIN
        self.ScanMode = 1

    # Hardware reset
    def ADS1263_reset(self):
        digital_write(self.rst_pin, 1)
        delay_ms(200)
        digital_write(self.rst_pin, 0)
        delay_ms(200)
        digital_write(self.rst_pin, 1)
        delay_ms(200)

    def ADS1263_WriteCmd(self, reg):
        digital_write(self.cs_pin, 0)  # CS LOW
        spi_writebyte([reg])
        digital_write(self.cs_pin, 1)  # CS HIGH

    def ADS1263_WriteReg(self, reg, data):
        digital_write(self.cs_pin, 0)
        spi_writebyte([ADS1263_CMD['CMD_WREG'] | reg, 0x00, data])
        digital_write(self.cs_pin, 1)

    def ADS1263_ReadData(self, reg):
        digital_write(self.cs_pin, 0)
        spi_writebyte([ADS1263_CMD['CMD_RREG'] | reg, 0x00])
        data = spi_readbytes(1)
        digital_write(self.cs_pin, 1)
        return data

    def ADS1263_CheckSum(self, val, byt):
        s = 0
        mask = 0xff
        while val:
            s += val & mask
            val = val >> 8
        s += 0x9b
        return (s & 0xff) ^ byt

    def ADS1263_WaitDRDY(self):
        i = 0
        while True:
            i += 1
            if digital_read(self.drdy_pin) == 0:
                break
            if i >= 400000:
                print("Time Out ...")
                break

    def ADS1263_ReadChipID(self):
        id = self.ADS1263_ReadData(ADS1263_REG['REG_ID'])
        return id[0] >> 5

    def ADS1263_SetMode(self, Mode):
        self.ScanMode = Mode

    def ADS1263_ConfigADC(self, gain, drate):
        MODE2 = 0x80
        MODE2 |= (gain << 4) | drate
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE2'], MODE2)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE2'])[0] == MODE2:
            print("REG_MODE2 success")
        else:
            print("REG_MODE2 unsuccess")

        REFMUX = 0x24
        self.ADS1263_WriteReg(ADS1263_REG['REG_REFMUX'], REFMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_REFMUX'])[0] == REFMUX:
            print("REG_REFMUX success")
        else:
            print("REG_REFMUX unsuccess")

        MODE0 = ADS1263_DELAY['ADS1263_DELAY_35us']
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE0'], MODE0)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE0'])[0] == MODE0:
            print("REG_MODE0 success")
        else:
            print("REG_MODE0 unsuccess")

        MODE1 = 0x84
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE1'], MODE1)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE1'])[0] == MODE1:
            print("REG_MODE1 success")
        else:
            print("REG_MODE1 unsuccess")

    def ADS1263_ConfigADC2(self, gain, drate):
        ADC2CFG = 0x20
        ADC2CFG |= (drate << 6) | gain
        self.ADS1263_WriteReg(ADS1263_REG['REG_ADC2CFG'], ADC2CFG)
        if self.ADS1263_ReadData(ADS1263_REG['REG_ADC2CFG'])[0] == ADC2CFG:
            print("REG_ADC2CFG success")
        else:
            print("REG_ADC2CFG unsuccess")

        MODE0 = ADS1263_DELAY['ADS1263_DELAY_35us']
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE0'], MODE0)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE0'])[0] == MODE0:
            print("REG_MODE0 success")
        else:
            print("REG_MODE0 unsuccess")

    def ADS1263_SetChannal(self, Channal):
        if Channal > 10:
            return 0
        INPMUX = (Channal << 4) | 0x0a
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_INPMUX'])[0] != INPMUX:
            print("REG_INPMUX unsuccess")

    def ADS1263_SetChannal_ADC2(self, Channal):
        if Channal > 10:
            return 0
        INPMUX = (Channal << 4) | 0x0a
        self.ADS1263_WriteReg(ADS1263_REG['REG_ADC2MUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_ADC2MUX'])[0] != INPMUX:
            print("REG_ADC2MUX unsuccess")

    def ADS1263_SetDiffChannal(self, Channal):
        if Channal == 0:
            INPMUX = (0 << 4) | 1
        elif Channal == 1:
            INPMUX = (2 << 4) | 3
        elif Channal == 2:
            INPMUX = (4 << 4) | 5
        elif Channal == 3:
            INPMUX = (6 << 4) | 7
        elif Channal == 4:
            INPMUX = (8 << 4) | 9
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_INPMUX'])[0] != INPMUX:
            print("REG_INPMUX unsuccess")

    def ADS1263_SetDiffChannal_ADC2(self, Channal):
        if Channal == 0:
            INPMUX = (0 << 4) | 1
        elif Channal == 1:
            INPMUX = (2 << 4) | 3
        elif Channal == 2:
            INPMUX = (4 << 4) | 5
        elif Channal == 3:
            INPMUX = (6 << 4) | 7
        elif Channal == 4:
            INPMUX = (8 << 4) | 9
        self.ADS1263_WriteReg(ADS1263_REG['REG_ADC2MUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_ADC2MUX'])[0] != INPMUX:
            print("REG_ADC2MUX unsuccess")

    def ADS1263_init_ADC1(self, Rate1='ADS1263_14400SPS'):
        if module_init() != 0:
            return -1
        self.ADS1263_reset()
        id = self.ADS1263_ReadChipID()
        if id == 0x01:
            print("ID Read success")
        else:
            print("ID Read failed")
            return -1
        self.ADS1263_WriteCmd(ADS1263_CMD['CMD_STOP1'])
        self.ADS1263_ConfigADC(ADS1263_GAIN['ADS1263_GAIN_1'], ADS1263_DRATE[Rate1])
        self.ADS1263_WriteCmd(ADS1263_CMD['CMD_START1'])
        return 0

    def ADS1263_init_ADC2(self, Rate2='ADS1263_ADC2_100SPS'):
        if module_init() != 0:
            return -1
        self.ADS1263_reset()
        id = self.ADS1263_ReadChipID()
        if id == 0x01:
            print("ID Read success")
        else:
            print("ID Read failed")
            return -1
        self.ADS1263_WriteCmd(ADS1263_CMD['CMD_STOP2'])
        self.ADS1263_ConfigADC2(ADS1263_ADC2_GAIN['ADS1263_ADC2_GAIN_1'], ADS1263_ADC2_DRATE[Rate2])
        return 0

    def ADS1263_Read_ADC_Data(self):
        digital_write(self.cs_pin, 0)
        while True:
            spi_writebyte([ADS1263_CMD['CMD_RDATA1']])
            if spi_readbytes(1)[0] & 0x40:
                break
        buf = spi_readbytes(5)
        digital_write(self.cs_pin, 1)
        read = ((buf[0] << 24) & 0xff000000) | ((buf[1] << 16) & 0xff0000) | ((buf[2] << 8) & 0xff00) | (buf[3] & 0xff)
        CRC = buf[4]
        if self.ADS1263_CheckSum(read, CRC) != 0:
            print("ADC1 data read error!")
        return read

    def ADS1263_Read_ADC2_Data(self):
        read = 0
        digital_write(self.cs_pin, 0)
        while True:
            spi_writebyte([ADS1263_CMD['CMD_RDATA2']])
            if spi_readbytes(1)[0] & 0x80:
                break
        buf = spi_readbytes(5)
        digital_write(self.cs_pin, 1)
        read |= ((buf[0] << 16) & 0xff0000) | ((buf[1] << 8) & 0xff00) | (buf[2] & 0xff)
        CRC = buf[4]
        if self.ADS1263_CheckSum(read, CRC) != 0:
            print("ADC2 data read error!")
        return read

    def ADS1263_GetChannalValue(self, Channel):
        if self.ScanMode == 0:  # Single-ended mode: 10 channels
            if Channel > 10:
                print("Channel number must be less than 10")
                return 0
            self.ADS1263_SetChannal(Channel)
            self.ADS1263_WaitDRDY()
            Value = self.ADS1263_Read_ADC_Data()
        else:  # Differential mode: 5 channels
            if Channel > 4:
                print("Channel number must be less than 5")
                return 0
            self.ADS1263_SetDiffChannal(Channel)
            self.ADS1263_WaitDRDY()
            Value = self.ADS1263_Read_ADC_Data()
        return Value

    def ADS1263_GetChannalValue_ADC2(self, Channel):
        if self.ScanMode == 0:
            if Channel > 10:
                print("Channel number must be less than 10")
                return 0
            self.ADS1263_SetChannal_ADC2(Channel)
            self.ADS1263_WriteCmd(ADS1263_CMD['CMD_START2'])
            Value = self.ADS1263_Read_ADC2_Data()
        else:
            if Channel > 4:
                print("Channel number must be less than 5")
                return 0
            self.ADS1263_SetDiffChannal_ADC2(Channel)
            self.ADS1263_WriteCmd(ADS1263_CMD['CMD_START2'])
            Value = self.ADS1263_Read_ADC2_Data()
        return Value

    def ADS1263_GetAll(self, List):
        ADC_Value = []
        for i in List:
            ADC_Value.append(self.ADS1263_GetChannalValue(i))
        return ADC_Value

    def ADS1263_GetAll_ADC2(self):
        ADC_Value = [0] * 10
        for i in range(10):
            ADC_Value[i] = self.ADS1263_GetChannalValue_ADC2(i)
            self.ADS1263_WriteCmd(ADS1263_CMD['CMD_STOP2'])
            delay_ms(20)
        return ADC_Value

    def ADS1263_RTD_Test(self):
        Delay = ADS1263_DELAY['ADS1263_DELAY_8d8ms']
        Gain = ADS1263_GAIN['ADS1263_GAIN_1']
        Drate = ADS1263_DRATE['ADS1263_20SPS']

        # MODE0 (CHOP OFF)
        MODE0 = Delay
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE0'], MODE0)
        delay_ms(1)

        # IDACMUX (IDAC2 AINCOM, IDAC1 AIN3)
        IDACMUX = (0x0a << 4) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_IDACMUX'], IDACMUX)
        delay_ms(1)

        # IDACMAG (IDAC2 = IDAC1 = 250uA)
        IDACMAG = (0x03 << 4) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_IDACMAG'], IDACMAG)
        delay_ms(1)

        MODE2 = (Gain << 4) | Drate
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE2'], MODE2)
        delay_ms(1)

        # INPMUX (AINP = AIN7, AINN = AIN6)
        INPMUX = (0x07 << 4) | 0x06
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        delay_ms(1)

        # REFMUX (AIN4, AIN5)
        REFMUX = (0x03 << 3) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_REFMUX'], REFMUX)
        delay_ms(1)

        # Start conversion, wait for data, then stop
        self.ADS1263_WriteCmd(ADS1263_CMD['CMD_START1'])
        delay_ms(10)
        self.ADS1263_WaitDRDY()
        Value = self.ADS1263_Read_ADC_Data()
        self.ADS1263_WriteCmd(ADS1263_CMD['CMD_STOP1'])

        return Value

    def ADS1263_DAC_Test(self, isPositive, isOpen):
        Volt = ADS1263_DAC_VOLT['ADS1263_DAC_VLOT_3']

        if isPositive:
            Reg = ADS1263_REG['REG_TDACP']
        else:
            Reg = ADS1263_REG['REG_TDACN']

        Value = Volt | 0x80 if isOpen else 0x00
        self.ADS1263_WriteReg(Reg, Value)

    def ADS1263_Exit(self):
        module_exit()

# ----- End of File -----
