import serial
import time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)

while True:
    message = "Hello from Pi 3!\n"
    ser.write(message.encode('utf-8'))
    print("Sent:", message.strip())
    time.sleep(1)
