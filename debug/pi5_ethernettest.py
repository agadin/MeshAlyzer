# server_pi5.py
import socket

HOST = '0.0.0.0'
PORT = 65432


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[SERVER] Listening on port {PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)  # Echo back the exact data


if __name__ == '__main__':
    main()
