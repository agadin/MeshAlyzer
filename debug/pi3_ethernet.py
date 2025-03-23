# client_pi3.py
import socket
import time

SERVER_IP = '10.42.0.1'  # Pi 5's IP
PORT = 65432

def main():
    print(f"[CLIENT] Connecting to {SERVER_IP}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print("[CLIENT] Connected to server.")

        for i in range(5):  # Send 5 messages
            message = f"Hello from Pi 3 - msg #{i+1}"
            s.sendall(message.encode())
            print(f"[CLIENT] Sent: {message}")
            data = s.recv(1024)
            print(f"[CLIENT] Received: {data.decode()}")
            time.sleep(1)

        print("[CLIENT] Done sending messages.")

if __name__ == '__main__':
    main()
