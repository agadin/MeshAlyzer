import spidev
import lgpio
import time

# ---------------------------------------------------------------------------
# Define constants for digital levels (since we no longer use RPi.GPIO)
HIGH = 1
LOW = 0

# ---------------------------------------------------------------------------
# ADS1263 configuration dictionaries

# gain
ADS1263_GAIN = {
    'ADS1263_GAIN_1': 0,  # GAIN   1
    'ADS1263_GAIN_2': 1,  # GAIN   2
    'ADS1263_GAIN_4': 2,  # GAIN   4
    'ADS1263_GAIN_8': 3,  # GAIN   8
    'ADS1263_GAIN_16': 4,  # GAIN  16
    'ADS1263_GAIN_32': 5,  # GAIN  32
    'ADS1263_GAIN_64': 6,  # GAIN  64
}
# ADC2 gain
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
# data rate
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
# ADC2 data rate
ADS1263_ADC2_DRATE = {
    'ADS1263_ADC2_10SPS': 0,
    'ADS1263_ADC2_100SPS': 1,
    'ADS1263_ADC2_400SPS': 2,
    'ADS1263_ADC2_800SPS': 3,
}
# Delay time
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
# DAC out volt
ADS1263_DAC_VOLT = {
    'ADS1263_DAC_VLOT_4_5': 0b01001,  # 4.5V
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
# registration definition
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
# command definitions
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

# ---------------------------------------------------------------------------
# Minimal config module implemented with spidev for SPI and lgpio for GPIO
#
# Global handles
_chip = None
_spi = None
_gpio_wrapper = None


def module_init():
    global _chip, _spi, _gpio_wrapper
    # Open GPIO chip 0 using lgpio
    _chip = lgpio.gpiochip_open(0)
    _gpio_wrapper = LGPIOWrapper(_chip)

    # Initialize SPI using spidev
    _spi = spidev.SpiDev()
    # Open SPI bus 0, device 0 (adjust bus/device numbers as needed)
    _spi.open(0, 0)
    _spi.max_speed_hz = 250000
    # Disable spidev's chip-select since we handle it manually via lgpio:
    _spi.no_cs = True
    return 0


def module_exit():
    global _chip, _spi, _gpio_wrapper
    try:
        if _spi is not None:
            _spi.close()
    except Exception as e:
        print("Error closing SPI:", e)
    _gpio_wrapper.cleanup()
    lgpio.gpiochip_close(_chip)


def digital_read(pin):
    global _gpio_wrapper
    return _gpio_wrapper.digital_read(pin)


def delay_ms(ms):
    time.sleep(ms / 1000.0)


def spi_writebyte(data):
    global _spi
    # data is a list of integers; use spidev to transfer data
    _spi.xfer2(data)


def spi_readbytes(n):
    global _spi
    # Read n bytes by sending dummy bytes (0x00)
    return _spi.xfer2([0x00] * n)


# ---------------------------------------------------------------------------
# LGPIOWrapper class for digital I/O
#
class LGPIOWrapper:
    def __init__(self, chip):
        self.chip = chip
        self.out_lines = {}
        self.in_lines = {}

    def setup_out(self, pin):
        # Request an output line; adjust parameters as needed.
        handle = lgpio.gpio_request_line(self.chip, [pin], "ADS1263_out", 0, 0)
        self.out_lines[pin] = handle

    def setup_in(self, pin):
        # Request an input line; adjust parameters as needed.
        handle = lgpio.gpio_request_line(self.chip, [pin], "ADS1263_in", 0, 1)
        self.in_lines[pin] = handle

    def digital_write(self, pin, value):
        if pin not in self.out_lines:
            self.setup_out(pin)
        lgpio.gpio_set_line_value(self.out_lines[pin], value)

    def digital_read(self, pin):
        if pin not in self.in_lines:
            self.setup_in(pin)
        return lgpio.gpio_get_line_value(self.in_lines[pin])

    def cleanup(self):
        for handle in self.out_lines.values():
            lgpio.gpio_release_line(handle)
        for handle in self.in_lines.values():
            lgpio.gpio_release_line(handle)


# ---------------------------------------------------------------------------
# ADS1263 Driver Class (using spidev for SPI and lgpio for GPIO)
#
class ADS1263:
    def __init__(self):
        # Define your pin numbers for reset, chip-select and DRDY.
        self.rst_pin = 5  # Replace with your actual reset pin number
        self.cs_pin = 6  # Replace with your actual chip-select pin number
        self.drdy_pin = 13  # Replace with your actual DRDY pin number
        self.ScanMode = 1

    # Hardware reset
    def ADS1263_reset(self):
        digital_write(self.rst_pin, HIGH)
        delay_ms(200)
        digital_write(self.rst_pin, LOW)
        delay_ms(200)
        digital_write(self.rst_pin, HIGH)
        delay_ms(200)

    def ADS1263_WriteCmd(self, reg):
        digital_write(self.cs_pin, LOW)  # cs = 0
        spi_writebyte([reg])
        digital_write(self.cs_pin, HIGH)  # cs = 1

    def ADS1263_WriteReg(self, reg, data):
        digital_write(self.cs_pin, LOW)
        spi_writebyte([ADS1263_CMD['CMD_WREG'] | reg, 0x00, data])
        digital_write(self.cs_pin, HIGH)

    def ADS1263_ReadData(self, reg):
        digital_write(self.cs_pin, LOW)
        spi_writebyte([ADS1263_CMD['CMD_RREG'] | reg, 0x00])
        data = spi_readbytes(1)
        digital_write(self.cs_pin, HIGH)
        return data

    # Check Data (checksum)
    def ADS1263_CheckSum(self, val, byt):
        sum_val = 0
        mask = 0xff  # 8-bit mask
        while val:
            sum_val += val & mask
            val = val >> 8
        sum_val += 0x9b
        return (sum_val & 0xff) ^ byt

    # Wait for DRDY to go low (for ADC1)
    def ADS1263_WaitDRDY(self):
        i = 0
        while True:
            i += 1
            if digital_read(self.drdy_pin) == 0:
                break
            if i >= 400000:
                print("Time Out ...")
                break

    # Check chip ID; returns 1 on success
    def ADS1263_ReadChipID(self):
        id = self.ADS1263_ReadData(ADS1263_REG['REG_ID'])
        return id[0] >> 5

    def ADS1263_SetMode(self, Mode):
        self.ScanMode = Mode

    # Configure ADC1 parameters: gain and data rate
    def ADS1263_ConfigADC(self, gain, drate):
        MODE2 = 0x80  # PGA bypassed if set; otherwise enabled.
        MODE2 |= (gain << 4) | drate
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE2'], MODE2)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE2'])[0] == MODE2:
            print("REG_MODE2 success")
        else:
            print("REG_MODE2 unsuccess")

        REFMUX = 0x24  # VDD,VSS as REF
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

        MODE1 = 0x84  # Digital Filter settings (FIR filter)
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE1'], MODE1)
        if self.ADS1263_ReadData(ADS1263_REG['REG_MODE1'])[0] == MODE1:
            print("REG_MODE1 success")
        else:
            print("REG_MODE1 unsuccess")

    # Configure ADC2 parameters: gain and data rate
    def ADS1263_ConfigADC2(self, gain, drate):
        ADC2CFG = 0x20  # 0x20: use VAVDD/VAVSS as reference
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

    # Set ADC1 measuring channel (single-ended or differential)
    def ADS1263_SetChannal(self, Channal):
        if Channal > 10:
            return 0
        INPMUX = (Channal << 4) | 0x0a
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_INPMUX'])[0] != INPMUX:
            print("REG_INPMUX unsuccess")

    # Set ADC2 measuring channel
    def ADS1263_SetChannal_ADC2(self, Channal):
        if Channal > 10:
            return 0
        INPMUX = (Channal << 4) | 0x0a
        self.ADS1263_WriteReg(ADS1263_REG['REG_ADC2MUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_ADC2MUX'])[0] != INPMUX:
            print("REG_ADC2MUX unsuccess")

    # Set ADC1 differential channel
    def ADS1263_SetDiffChannal(self, Channal):
        if Channal == 0:
            INPMUX = (0 << 4) | 1  # AIN0-AIN1
        elif Channal == 1:
            INPMUX = (2 << 4) | 3  # AIN2-AIN3
        elif Channal == 2:
            INPMUX = (4 << 4) | 5  # AIN4-AIN5
        elif Channal == 3:
            INPMUX = (6 << 4) | 7  # AIN6-AIN7
        elif Channal == 4:
            INPMUX = (8 << 4) | 9  # AIN8-AIN9
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        if self.ADS1263_ReadData(ADS1263_REG['REG_INPMUX'])[0] != INPMUX:
            print("REG_INPMUX unsuccess")

    # Set ADC2 differential channel
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

    # Device initialization for ADC1
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

    # Device initialization for ADC2
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

    # Read ADC1 data
    def ADS1263_Read_ADC_Data(self):
        digital_write(self.cs_pin, LOW)
        while True:
            spi_writebyte([ADS1263_CMD['CMD_RDATA1']])
            # Wait until the data-ready flag is set
            if spi_readbytes(1)[0] & 0x40 != 0:
                break
        buf = spi_readbytes(5)
        digital_write(self.cs_pin, HIGH)
        read = ((buf[0] << 24) & 0xff000000)
        read |= ((buf[1] << 16) & 0xff0000)
        read |= ((buf[2] << 8) & 0xff00)
        read |= (buf[3] & 0xff)
        CRC = buf[4]
        if self.ADS1263_CheckSum(read, CRC) != 0:
            print("ADC1 data read error!")
        return read

    # Read ADC2 data
    def ADS1263_Read_ADC2_Data(self):
        read = 0
        digital_write(self.cs_pin, LOW)
        while True:
            spi_writebyte([ADS1263_CMD['CMD_RDATA2']])
            if spi_readbytes(1)[0] & 0x80 != 0:
                break
        buf = spi_readbytes(5)
        digital_write(self.cs_pin, HIGH)
        read |= ((buf[0] << 16) & 0xff0000)
        read |= ((buf[1] << 8) & 0xff00)
        read |= (buf[2] & 0xff)
        CRC = buf[4]
        if self.ADS1263_CheckSum(read, CRC) != 0:
            print("ADC2 data read error!")
        return read

    # Read ADC1 value from a specified channel
    def ADS1263_GetChannalValue(self, Channel):
        if self.ScanMode == 0:
            if Channel > 10:
                print("Channel number must be less than 10")
                return 0
            self.ADS1263_SetChannal(Channel)
            self.ADS1263_WaitDRDY()
            Value = self.ADS1263_Read_ADC_Data()
        else:
            if Channel > 4:
                print("Channel number must be less than 5")
                return 0
            self.ADS1263_SetDiffChannal(Channel)
            self.ADS1263_WaitDRDY()
            Value = self.ADS1263_Read_ADC_Data()
        return Value

    # Read ADC2 value from a specified channel
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

        MODE0 = Delay
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE0'], MODE0)
        delay_ms(1)

        IDACMUX = (0x0a << 4) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_IDACMUX'], IDACMUX)
        delay_ms(1)

        IDACMAG = (0x03 << 4) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_IDACMAG'], IDACMAG)
        delay_ms(1)

        MODE2 = (Gain << 4) | Drate
        self.ADS1263_WriteReg(ADS1263_REG['REG_MODE2'], MODE2)
        delay_ms(1)

        INPMUX = (0x07 << 4) | 0x06
        self.ADS1263_WriteReg(ADS1263_REG['REG_INPMUX'], INPMUX)
        delay_ms(1)

        REFMUX = (0x03 << 3) | 0x03
        self.ADS1263_WriteReg(ADS1263_REG['REG_REFMUX'], REFMUX)
        delay_ms(1)

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
        if isOpen:
            Value = Volt | 0x80
        else:
            Value = 0x00
        self.ADS1263_WriteReg(Reg, Value)

    def ADS1263_Exit(self):
        module_exit()

### END OF FILE ###
