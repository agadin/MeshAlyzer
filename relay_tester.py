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
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN2, 0)
    lgpio.gpio_write(chip, PIN4, 0)

def set_deflation():
    # Deflation: turn on pins 2 & 4, turn off inflation pins
    lgpio.gpio_write(chip, PIN1, 0)
    lgpio.gpio_write(chip, PIN3, 0)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN4, 1)

def set_neutral():
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN4, 1)

# For Option 2, we want to control two groups independently:
def set_group(slider_value, infl_pin, defl_pin):
    # slider_value is an integer: 0=deflation, 1=neutral, 2=inflation
    if slider_value == 0:
        lgpio.gpio_write(chip, infl_pin, 0)
        lgpio.gpio_write(chip, defl_pin, 1)
    elif slider_value == 2:
        lgpio.gpio_write(chip, infl_pin, 1)
        lgpio.gpio_write(chip, defl_pin, 0)
    else:
        lgpio.gpio_write(chip, infl_pin, 0)
        lgpio.gpio_write(chip, defl_pin, 0)

# --- UI Setup ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Balloon Valve Control")
app.geometry("500x400")

# Create a Tabview with three tabs for the three control modes.
tabview = ctk.CTkTabview(app, width=480, height=360)
tabview.pack(padx=10, pady=10, fill="both", expand=True)
tabview.add("Option 2: Control Both Valve Groups Together")
tabview.add("Option 1: Control Two Valve Groups Independently")
set_neutral()

def option2_callback_left(value):
    pos = int(round(float(value)))
    set_group(pos, PIN1, PIN2)
    if pos != 1:
        segmented_button.set("Neutral")

def option2_callback_right(value):
    pos = int(round(float(value)))
    set_group(pos, PIN3, PIN4)
    if pos != 1:
        segmented_button.set("Neutral")

option2_frame = tabview.tab("Option 1: Control Two Valve Groups Independently")
ctk.CTkLabel(option2_frame, text="Independent Control of Two Valve Groups").pack(pady=10)
ctk.CTkLabel(option2_frame, text="Group 1 (Pins 1 & 2):").pack()
segmented_button = ctk.CTkSegmentedButton(option2_frame,
                                          values=["Deflation", "Neutral", "Inflation"],
                                          command=option2_callback_left)
segmented_button.set("Neutral")
segmented_button.pack(pady=10)

ctk.CTkLabel(option2_frame, text="Group 2 (Pins 3 & 4):").pack(pady=(20, 0))
segmented_button = ctk.CTkSegmentedButton(option2_frame,
                                          values=["Deflation", "Neutral", "Inflation"],
                                          command=option2_callback_right)
segmented_button.set("Neutral")
segmented_button.pack(pady=10)

def option3_callback(choice):
    # choice is a string: "Deflation", "Neutral", or "Inflation"
    if choice == "Deflation":
        set_deflation()
    elif choice == "Inflation":
        set_inflation()
    else:
        set_neutral()
    if choice != "Neutral":
        segmented_button_left.set("Neutral")
        segmented_button_right.set("Neutral")

option3_frame = tabview.tab("Option 2: Control Both Valve Groups Together")
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