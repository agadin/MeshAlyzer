import serial
import json
import time

class PressureReceiver:
    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def get_latest_pressure(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                latest_line = None

                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        print("Received blank line")  # Debug: print blank line
                        continue
                    print(f"Read line: {line}")  # Debug: print each line read
                    try:
                        data = json.loads(line)
                        latest_line = data
                        print(f"Decoded JSON: {data}")  # Debug: print decoded JSON
                    except json.JSONDecodeError:
                        print("JSON decode error")  # Debug: print JSON decode error
                        continue

                if latest_line and "sensors" in latest_line:
                    sensors = latest_line["sensors"]
                    # Safely extract values for 4 channels
                    pressure0 = sensors.get("channel_0", 0.0)
                    pressure1 = sensors.get("channel_1", 0.0)
                    pressure2 = sensors.get("channel_2", 0.0)
                    pressure3 = sensors.get("channel_3", 0.0)
                    print(f"Pressure values: {pressure0}, {pressure1}, {pressure2}, {pressure3}")  # Debug: print pressure values
                    return pressure0, pressure1, pressure2, pressure3
                else:
                    print("No valid sensor data found")  # Debug: print no valid sensor data
                    return 0.0, 0.0, 0.0, 0.0  # fallback values
        except Exception as e:
            print(f"Error reading serial: {e}")
            return 0.0, 0.0, 0.0, 0.0

    def test_average_speed(self):
        packet_count = 0
        start_time = time.time()

        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                while packet_count < 10:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        print("Received blank line")  # Debug: print blank line
                        continue
                    print(f"Read line: {line}")  # Debug: print each line read
                    try:
                        data = json.loads(line)
                        if "sensors" in data:
                            packet_count += 1
                            print(f"Packet {packet_count} received")  # Debug: print packet count
                    except json.JSONDecodeError:
                        print("JSON decode error")  # Debug: print JSON decode error
                        continue

        except Exception as e:
            print(f"Error reading serial: {e}")
            return 0.0

        total_time = time.time() - start_time
        print(f"Total time to receive 10 packets: {total_time:.2f} seconds")  # Debug: print total time
        return total_time

def main():
    receiver = PressureReceiver()
    print("Starting to receive pressure data...")
    total_time = receiver.test_average_speed()
    print(f"Total time to receive 10 packets: {total_time:.2f} seconds")

    print("Listening for the most recent packet every 3 seconds...")
    try:
        while True:
            pressure_data = receiver.get_latest_pressure()
            print(f"Pressure Data: {pressure_data}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("Exiting...")
def wait_for_input_or_message(ser):
    input_event = threading.Event()
    message_event = threading.Event()

    def wait_for_input():
        input("Press Enter to continue...")
        input_event.set()

    def wait_for_message():
        while not message_event.is_set():
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Received message: {line}")
                message_event.set()

    input_thread = threading.Thread(target=wait_for_input)
    message_thread = threading.Thread(target=wait_for_message)

    input_thread.start()
    message_thread.start()

    while not (input_event.is_set() or message_event.is_set()):
        pass

def test_serial_connection():
    try:
        ser = serial.Serial('/dev/serial0', 9600, timeout=1)
        ser.write(b'hello from pi3\n')
        print("Test message sent successfully.")
        wait_for_input_or_message(ser)
        ser.close()
    except Exception as e:
        print(f"Error during serial test: {e}")

if __name__ == "__main__":
    test_serial_connection()
    main()