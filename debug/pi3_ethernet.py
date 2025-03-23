# client_pi3.py
import socket
import time

SERVER_IP = '10.42.0.1'
PORT = 65432
NUM_MESSAGES = 10000
MESSAGE = b'x' * 512  # 512-byte message payload

def main():
    print(f"[CLIENT] Connecting to {SERVER_IP}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print("[CLIENT] Connected.")

        start = time.time()
        for i in range(NUM_MESSAGES):
            s.sendall(MESSAGE)
            data = s.recv(len(MESSAGE))  # Expect same length back
            if data != MESSAGE:
                print(f"[CLIENT] Warning: mismatch in message #{i}")
        end = time.time()

        duration = end - start
        avg_latency = duration / NUM_MESSAGES
        throughput_msg_s = NUM_MESSAGES / duration
        total_data_MB = (NUM_MESSAGES * len(MESSAGE)) / (1024 ** 2)
        mbps = total_data_MB / duration * 8  # convert MB/s to Mbps

        print("\n📊 [RESULTS]")
        print(f"Total time: {duration:.3f} s")
        print(f"Average round-trip latency: {avg_latency*1000:.3f} ms")
        print(f"Throughput: {throughput_msg_s:.1f} messages/sec")
        print(f"Data sent: {total_data_MB:.2f} MB")
        print(f"Approx. network speed: {mbps:.2f} Mbps")

if __name__ == '__main__':
    main()
