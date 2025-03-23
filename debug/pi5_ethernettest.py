# server_pi5.py
import socket

HOST = '0.0.0.0'      # Listen on all interfaces
PORT = 65432          # Must match client

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[SERVER] Waiting for connection on port {PORT}...")
        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    print("[SERVER] Connection closed.")
                    break
                message = data.decode()
                print(f"[SERVER] Received: {message}")
                # Optionally, send a reply
                conn.sendall(b"ACK from Pi 5")

if __name__ == '__main__':
    main()
