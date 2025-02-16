import customtkinter as ctk
import lgpio

# --- GPIO Setup ---
PIN1 = 17  # Inflation valve group 1
PIN2 = 27  # Deflation valve group 1
PIN3 = 23  # Inflation valve group 2
PIN4 = 24  # Deflation valve group 2

chip = lgpio.gpiochip_open(0)

# Claim each pin as an output
for pin in (PIN1, PIN2, PIN3, PIN4):
    lgpio.gpio_claim_output(chip, pin)
    lgpio.gpio_write(chip, pin, 0)

# --- Functions to set outputs ---
def set_inflation():
    # Inflation: turn on pins 1 & 3, turn off deflation pins
    lgpio.gpio_write(chip, PIN1, 0)
    lgpio.gpio_write(chip, PIN3, 0)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN4, 1)

def set_deflation():
    # Deflation: turn on pins 2 & 4, turn off inflation pins
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN2, 0)
    lgpio.gpio_write(chip, PIN4, 0)

def set_neutral():
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN4, 1)

# --- UI Setup ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Balloon Valve Control")
app.geometry("500x400")

# Create a Tabview with three tabs for the three control modes.
tabview = ctk.CTkTabview(app, width=480, height=360)
tabview.pack(padx=10, pady=10, fill="both", expand=True)
tabview.add("Solinoid Control")
set_neutral()

def option3_callback(choice):
    # choice is a string: "Deflation", "Neutral", or "Inflation"
    if choice == "Deflation":
        set_deflation()
    elif choice == "Inflation":
        set_inflation()
    else:
        set_neutral()

option3_frame = tabview.tab("Solinoid Control")
ctk.CTkLabel(option3_frame, text="Segmented Button Control").pack(pady=10)
segmented_button = ctk.CTkSegmentedButton(option3_frame,
                                          values=["Deflation", "Neutral", "Inflation"],
                                          command=option3_callback)
segmented_button.set("Neutral")
segmented_button.pack(pady=10)

# --- On Close: Clean up ---
def on_close():
    # Turn off all outputs before closing
    set_neutral()
    lgpio.gpiochip_close(chip)
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)
app.mainloop()
