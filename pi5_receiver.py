#!/usr/bin/env python3
import serial
import json
import threading

# Global variable to store the most recent sensor data
latest_data = None
data_lock = threading.Lock()

def uart_listener():
    global latest_data
    # Open the UART port (adjust device file if needed)
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                data = json.loads(line)
                with data_lock:
                    latest_data = data
        except Exception as e:
            print("Error reading data:", e)

def get_latest_data():
    """Return the most recent sensor data received."""
    with data_lock:
        return latest_data

if __name__ == "__main__":
    # Start the UART listener in a background thread
    listener_thread = threading.Thread(target=uart_listener, daemon=True)
    listener_thread.start()
    print("Receiver running. Listening for sensor data...")

    # For demonstration: periodically print the latest data.
    try:
        while True:
            data = get_latest_data()
            if data:
                print("Latest data:", data)
            else:
                print("No data received yet...")
            # Adjust the interval as needed
            threading.Event().wait(2)
    except KeyboardInterrupt:
        print("Exiting...")
