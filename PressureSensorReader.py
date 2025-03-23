import serial

def uart_listener():
    try:
        ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
        print("Listening for UART messages...")
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Received message: {line}")
            except Exception as e:
                print(f"Error reading data: {e}")
    except Exception as e:
        print(f"Error opening serial port: {e}")

if __name__ == "__main__":
    try:
        uart_listener()
    except KeyboardInterrupt:
        print("Exiting...")