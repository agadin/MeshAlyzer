import lgpio

# Open the GPIO chip
chip_handle = lgpio.gpiochip_open(0)

# Define the GPIO pin number and initial level
gpio_pin = 31
initial_level = 1  # High

# Claim the GPIO for output
status = lgpio.gpio_claim_output(chip_handle, gpio_pin, initial_level)

# Check if the GPIO was successfully claimed
if status == 0:
    print(f"GPIO {gpio_pin} successfully claimed for output with initial level {initial_level}.")
else:
    print(f"Failed to claim GPIO {gpio_pin} for output. Error code: {status}")

# Close the GPIO chip when done
lgpio.gpiochip_close(chip_handle)