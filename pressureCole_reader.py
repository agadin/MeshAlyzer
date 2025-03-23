#!/usr/bin/env python3
import socket
import json
import time

class PressureReceiver:
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
                p3 = sensors.get("channel_3", 0.0)
                print(f"[SERVER] Pressures: {p0:.3f}, {p1:.3f}, {p2:.3f}, {p3:.3f}")
            else:
                print("[SERVER] Invalid data: missing 'sensors'")
        except json.JSONDecodeError as e:
            print(f"[SERVER] JSON decode error: {e}")

if __name__ == "__main__":
    receiver = PressureReceiver()
    try:
        receiver.run()
    except KeyboardInterrupt:
        print("[SERVER] Shutting down.")
