#!/usr/bin/env python3
import socket
import json
import time
import threading

class PressureReceiver:
    _latest_pressures = [0.0, 0.0, 0.0, 0.0]

    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.client_socket = None

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"[SERVER] Listening on {self.host}:{self.port}...")

            self.client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connection from {addr}")

            with self.client_socket:
                buffer = ""
                while True:
                    data = self.client_socket.recv(1024).decode("utf-8")
                    if not data:
                        print("[SERVER] Connection closed.")
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        self.handle_line(line)

    def handle_line(self, line):
        try:
            data = json.loads(line)
            if "sensors" in data:
                sensors = data["sensors"]
                p0 = sensors.get("channel_0", 0.0)
                p1 = sensors.get("channel_1", 0.0)
                p2 = sensors.get("channel_2", 0.0)
                PressureReceiver._latest_pressures = [p0, p1, p2]
            else:
                print("[SERVER] Invalid data: missing 'sensors'")
        except json.JSONDecodeError as e:
            print(f"[SERVER] JSON decode error: {e}")

    @classmethod
    def getpressures(cls):
        return tuple(cls._latest_pressures)

# Run server in a thread (so you can call getpressures from elsewhere)
if __name__ == "__main__":
    receiver = PressureReceiver()
    server_thread = threading.Thread(target=receiver.run, daemon=True)
    server_thread.start()

    try:
        while True:
            pressure0, pressure1, pressure2 = PressureReceiver.getpressures()
            print(f"[MAIN] Latest Pressures: {pressure0:.2f}, {pressure1:.2f}, {pressure2:.2f}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Stopping...")
