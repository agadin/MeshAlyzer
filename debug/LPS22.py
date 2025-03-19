import time
import board
import busio
import adafruit_lps2x

i2c = busio.I2C(board.SCL, board.SDA)
lps = adafruit_lps2x.LPS22(i2c)

while True:
    print(f"Pressure: {lps.pressure:.2f} hPa")
    print(f"Temperature: {lps.temperature:.2f} °C")
    time.sleep(1)
