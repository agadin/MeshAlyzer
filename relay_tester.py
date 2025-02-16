import customtkinter as ctk
import lgpio

# --- GPIO Setup ---
PIN1 = 17  # Inflation valve group 1
PIN2 = 27  # Deflation valve group 1
PIN3 = 23  # Inflation valve group 2
PIN4 = 24  # Deflation valve group 2

chip = lgpio.gpiochip_open(0)

# Claim each pin as an output and start OFF (0)
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
    # Neutral: turn all pins OFF
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN4, 1)


# For Option 1 (independent control) we set each group individually.
def set_group(mode, group):
    """
    group: 1 for Group 1 (PIN1 & PIN2); 2 for Group 2 (PIN3 & PIN4)
    mode: "Deflation", "Neutral", or "Inflation"
    """
    if group == 1:
        if mode == "Deflation":
            lgpio.gpio_write(chip, PIN1, 0)
            lgpio.gpio_write(chip, PIN2, 1)
        elif mode == "Inflation":
            lgpio.gpio_write(chip, PIN1, 1)
            lgpio.gpio_write(chip, PIN2, 0)
        else:
            lgpio.gpio_write(chip, PIN1, 0)
            lgpio.gpio_write(chip, PIN2, 0)
    elif group == 2:
        if mode == "Deflation":
            lgpio.gpio_write(chip, PIN3, 0)
            lgpio.gpio_write(chip, PIN4, 1)
        elif mode == "Inflation":
            lgpio.gpio_write(chip, PIN3, 1)
            lgpio.gpio_write(chip, PIN4, 0)
        else:
            lgpio.gpio_write(chip, PIN3, 0)
            lgpio.gpio_write(chip, PIN4, 0)


# --- UI Setup ---
set_neutral()
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Balloon Valve Control")
app.geometry("500x400")


# Bind the "q" key so that when pressed, the application will shut off
def on_key(event):
    if event.char.lower() == "q":
        on_close()


app.bind("<Key>", on_key)

# Create a Tabview with two tabs for the two control options.
tabview = ctk.CTkTabview(app, width=480, height=360)
tabview.pack(padx=10, pady=10, fill="both", expand=True)
tabview.add("Option 1: Independent Control")
tabview.add("Option 2: Both Groups Together")

# ======================
# Option 1 – Independent Control:
# Two segmented buttons control Group 1 (PIN1 & PIN2) and Group 2 (PIN3 & PIN4)
# ======================
option1_frame = tabview.tab("Option 1: Independent Control")
ctk.CTkLabel(option1_frame, text="Independent Control of Two Valve Groups", font=("Helvetica", 16)).pack(pady=10)

ctk.CTkLabel(option1_frame, text="Group 1 (Pins 1 & 2):", font=("Helvetica", 14)).pack()
segmented_button_group1 = ctk.CTkSegmentedButton(option1_frame,
                                                 values=["Deflation", "Neutral", "Inflation"])
segmented_button_group1.set("Neutral")
segmented_button_group1.pack(pady=5)

ctk.CTkLabel(option1_frame, text="Group 2 (Pins 3 & 4):", font=("Helvetica", 14)).pack(pady=(20, 0))
segmented_button_group2 = ctk.CTkSegmentedButton(option1_frame,
                                                 values=["Deflation", "Neutral", "Inflation"])
segmented_button_group2.set("Neutral")
segmented_button_group2.pack(pady=5)


def independent_group1_callback(choice):
    set_group(choice, 1)
    # Reset Option 2's control to Neutral.
    segmented_button_both.set("Neutral")


def independent_group2_callback(choice):
    set_group(choice, 2)
    segmented_button_both.set("Neutral")


segmented_button_group1.configure(command=independent_group1_callback)
segmented_button_group2.configure(command=independent_group2_callback)

# ======================
# Option 2 – Both Groups Together:
# A single segmented button controls both valve groups.
# ======================
option2_frame = tabview.tab("Option 2: Both Groups Together")
ctk.CTkLabel(option2_frame, text="Control Both Valve Groups Together", font=("Helvetica", 16)).pack(pady=10)
segmented_button_both = ctk.CTkSegmentedButton(option2_frame,
                                               values=["Deflation", "Neutral", "Inflation"])
segmented_button_both.set("Neutral")
segmented_button_both.pack(pady=5)


def both_groups_callback(choice):
    if choice == "Deflation":
        set_deflation()
    elif choice == "Inflation":
        set_inflation()
    else:
        set_neutral()
    # Reset Option 1's segmented buttons to neutral.
    segmented_button_group1.set("Neutral")
    segmented_button_group2.set("Neutral")


segmented_button_both.configure(command=both_groups_callback)


# --- On Close: Clean up ---
def on_close():
    set_neutral()
    lgpio.gpiochip_close(chip)
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_close)
app.mainloop()