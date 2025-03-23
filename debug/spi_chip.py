#!/usr/bin/python3
import lgpio
import time

def main():
    try:
        # Open the GPIO chip (usually chip 0 on Raspberry Pi)
        chip = lgpio.gpiochip_open(0)
        print("GPIO chip opened.")

        # Open SPI channel 0 with 500 kHz speed, mode 0, flags 0
        spi_handle = lgpio.spi_open(chip, 0, 500000, 0, 0)
        print("SPI device opened on channel 0.")

        # Send a dummy command (adjust the command bytes as needed)
        dummy_command = bytes([0x00])
        lgpio.spi_write(spi_handle, dummy_command)
        print("Sent dummy command.")

        # Wait briefly before reading the response
        time.sleep(0.1)
        data = lgpio.spi_read(spi_handle, 4)  # Read 4 bytes from the device
        print("Received data:", list(data))

    except Exception as e:
        print("An error occurred:", e)
    finally:
        # Cleanup: close the SPI channel and GPIO chip
        try:
            lgpio.spi_close(spi_handle)
            print("SPI device closed.")
        except Exception:
            pass
        try:
            lgpio.gpiochip_close(chip)
            print("GPIO chip closed.")
        except Exception:
            pass

if __name__ == '__main__':
    main()
