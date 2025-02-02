import customtkinter as ctk
import lgpio

# GPIO setup
RELAY_1_PIN = 17
RELAY_2_PIN = 27

chip = lgpio.gpiochip_open(0)

lgpio.gpio_claim_output(chip, RELAY_1_PIN)
lgpio.gpio_claim_output(chip, RELAY_2_PIN)

lgpio.gpio_write(chip, RELAY_1_PIN, 0)
lgpio.gpio_write(chip, RELAY_2_PIN, 0)

def toggle_relay1():
    current_state = lgpio.gpio_read(chip, RELAY_1_PIN)
    new_state = 1 if current_state == 0 else 0
    lgpio.gpio_write(chip, RELAY_1_PIN, new_state)
    relay1_button.configure(text=f"Relay 1: {'ON' if new_state else 'OFF'}")

def toggle_relay2():
    current_state = lgpio.gpio_read(chip, RELAY_2_PIN)
    new_state = 1 if current_state == 0 else 0
    lgpio.gpio_write(chip, RELAY_2_PIN, new_state)
    relay2_button.configure(text=f"Relay 2: {'ON' if new_state else 'OFF'}")

# UI setup
app = ctk.CTk()
app.title("Relay Control")
app.geometry("300x200")

relay1_button = ctk.CTkButton(app, text="Relay 1: OFF", command=toggle_relay1)
relay1_button.pack(pady=20)

relay2_button = ctk.CTkButton(app, text="Relay 2: OFF", command=toggle_relay2)
relay2_button.pack(pady=20)

def on_close():
    lgpio.gpio_write(chip, RELAY_1_PIN, 0)
    lgpio.gpio_write(chip, RELAY_2_PIN, 0)
    lgpio.gpiochip_close(chip)
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)

app.mainloop()
