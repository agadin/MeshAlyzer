#!/usr/bin/python3
import spidev
import time


def main():
    # Create an SPI instance
    spi = spidev.SpiDev()

    # Open SPI bus 0, chip select (CS) 0
    spi.open(0, 0)
    spi.max_speed_hz = 500000  # Set speed to 500 kHz
    spi.mode = 0  # Set SPI mode to 0

    print("SPI device opened using spidev.")

    # Send a dummy command (0x00) and simultaneously read 4 bytes.
    # xfer2 performs a full-duplex SPI transaction.
    dummy_command = [0x00]
    # Append dummy bytes (e.g., 0) to read 4 bytes in response.
    response = spi.xfer2(dummy_command + [0x00] * 4)
    print("Received data:", response)

    # Close the SPI connection
    spi.close()
    print("SPI device closed.")


if __name__ == "__main__":
    main()
