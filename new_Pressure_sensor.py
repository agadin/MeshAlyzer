import time
import spidev
import RPi.GPIO as GPIO

# **ADS1256 SPI Config**
SPI_CHANNEL = 0
SPI_SPEED = 2500000  # 2.5 MHz SPI speed
CS_PIN = 8  # Chip Select
DRDY_PIN = 7  # Data Ready
PUMP_PIN = 4  # GPIO pin for pump control

# **ADS1256 Commands**
CMD_RDATA = 0x01
CMD_SDATAC = 0x0F
CMD_WREG = 0x50
CMD_RREG = 0x10
CMD_RESET = 0xFE

# **ADS1256 Registers**
REG_MUX = 0x01
REG_ADCON = 0x02
REG_DRATE = 0x03

# **Pressure Sensor Calibration**
VREF = 5.0  # Reference voltage
BASELINE_VOLTAGE = 0.45  # Adjust based on zero-pressure reading
MAX_PRESSURE = 100.0  # Maximum pressure in PSI
MAX_SENSOR_VOLTAGE = 4.5  # Voltage at max PSI

# **Initialize SPI & GPIO**
spi = spidev.SpiDev()
spi.open(0, SPI_CHANNEL)
spi.max_speed_hz = SPI_SPEED
spi.mode = 1  # SPI Mode 1

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.setup(DRDY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(PUMP_PIN, GPIO.LOW)

# **Send SPI Command**
def send_command(command):
    GPIO.output(CS_PIN, GPIO.LOW)
    spi.xfer2([command])
    GPIO.output(CS_PIN, GPIO.HIGH)

# **Write to ADS1256 Register**
def write_register(reg, value):
    GPIO.output(CS_PIN, GPIO.LOW)
    spi.xfer2([CMD_WREG | reg, 0x00, value])
    GPIO.output(CS_PIN, GPIO.HIGH)

# **Read ADS1256 ADC Data**
def read_adc():
    while GPIO.input(DRDY_PIN) == 1:
        time.sleep(0.001)

    send_command(CMD_RDATA)
    time.sleep(0.01)

    GPIO.output(CS_PIN, GPIO.LOW)
    raw_data = spi.xfer2([0x00, 0x00, 0x00])
    GPIO.output(CS_PIN, GPIO.HIGH)

    adc_value = (raw_data[0] << 16) | (raw_data[1] << 8) | raw_data[2]

    if adc_value & 0x800000:
        adc_value -= 0x1000000

    return adc_value

# **Convert ADC Value to Voltage**
def adc_to_voltage(adc_value):
    return (adc_value / 8388607.0) * VREF  # ADS1256 is a 24-bit ADC

# **Convert Voltage to PSI**
def voltage_to_pressure(voltage):
    return ((voltage - BASELINE_VOLTAGE) / (MAX_SENSOR_VOLTAGE - BASELINE_VOLTAGE)) * MAX_PRESSURE

# **Initialize ADS1256**
def setup_ads1256():
    send_command(CMD_RESET)
    time.sleep(0.1)

    send_command(CMD_SDATAC)
    time.sleep(0.01)

    write_register(REG_MUX, (0x00 << 4) | 0x08)  # AIN0 vs AINCOM
    write_register(REG_ADCON, 0x00)  # Gain = 1
    time.sleep(0.1)

# **Main Loop**
def main():
    setup_ads1256()
    print("ADS1256 Initialized. Starting Pressure Readings...")

    while True:
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        time.sleep(2)  # Run pump for 2 seconds

        adc_value = read_adc()
        voltage = adc_to_voltage(adc_value)
        pressure = voltage_to_pressure(voltage)

        print(f"ADC: {adc_value} | Voltage: {voltage:.5f} V | Pressure: {pressure:.2f} PSI")

        time.sleep(0.2)  # Short delay for stability

        GPIO.output(PUMP_PIN, GPIO.LOW)
        time.sleep(0.4)  # Wait before next cycle

try:
    main()
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    GPIO.cleanup()
    spi.close()
