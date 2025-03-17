#!/usr/bin/python
# -*- coding:utf-8 -*-

import customtkinter as ctk
from PIL import Image
import ADS1263
import lgpio
import time
import csv
from datetime import datetime
from threading import Thread
from tkinter import messagebox

# Global constant for voltage reference
REF = 5.08  # Reference voltage

# =========== GPIO Setup ===========
PIN1 = 5   # Inflation valve group 1
PIN2 = 27  # Deflation valve group 1
PIN3 = 23  # Inflation valve group 2
PIN4 = 24  # Deflation valve group 2

chip = lgpio.gpiochip_open(0)

# Claim each pin as an output and start OFF (0)
for pin in (PIN1, PIN2, PIN3, PIN4):
    lgpio.gpio_claim_output(chip, pin)
    lgpio.gpio_write(chip, pin, 0)

# =========== Valve Control Functions ===========
def set_inflation():
    """Activate inflation valves and deactivate deflation valves."""
    lgpio.gpio_write(chip, PIN1, 1)
    lgpio.gpio_write(chip, PIN3, 1)
    lgpio.gpio_write(chip, PIN2, 0)
    lgpio.gpio_write(chip, PIN4, 0)

def set_deflation():
    """Activate deflation valves and deactivate inflation valves."""
    lgpio.gpio_write(chip, PIN1, 0)
    lgpio.gpio_write(chip, PIN3, 0)
    lgpio.gpio_write(chip, PIN2, 1)
    lgpio.gpio_write(chip, PIN4, 1)

def set_neutral():
    """Set all valves to a neutral (inactive) state."""
    lgpio.gpio_write(chip, PIN1, 0)
    lgpio.gpio_write(chip, PIN2, 0)
    lgpio.gpio_write(chip, PIN3, 0)
    lgpio.gpio_write(chip, PIN4, 0)

def set_group(mode, group):
    """
    Controls a single group of valves (1 or 2).
    mode can be: "Deflation", "Neutral", or "Inflation".
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

# =========== Main Application Class ===========
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lake Lab: Cough/Pressure Simulation")
        self.geometry("600x500")

        # Initialize ADC
        self.adc = self.adc_init()

        # Set up GUI components
        self.setup_gui()

        # Start periodic ADC display updates (every 100ms)
        self.update_adc_display()

    def adc_init(self):
        """Initialize the ADS1263 ADC."""
        adc = ADS1263.ADS1263()
        if adc.ADS1263_init() == -1:
            self.destroy()
            raise Exception("Failed to initialize ADS1263 ADC.")
        adc.ADS1263_SetMode(0)  # 0 for single-ended mode
        return adc

    def setup_gui(self):
        """Set up the GUI components."""
        # Set appearance and theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Bind "q" key for quick exit
        self.bind("<Key>", self.on_key)

        # Header with logos
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", pady=10)

        try:
            meshalyzer_image_pil = Image.open("MeshAlyzer.jpeg")
            stl_image_pil = Image.open("lakelab.jpg")
        except FileNotFoundError:
            meshalyzer_image_pil = Image.new("RGB", (220, 80), color="gray")
            stl_image_pil = Image.new("RGB", (120, 80), color="gray")

        meshalyzer_ctk_image = ctk.CTkImage(dark_image=meshalyzer_image_pil, size=(220, 80))
        stl_ctk_image = ctk.CTkImage(dark_image=stl_image_pil, size=(120, 80))

        meshalyzer_label = ctk.CTkLabel(header_frame, text="", image=meshalyzer_ctk_image)
        meshalyzer_label.pack(side="left", padx=20)
        stl_label = ctk.CTkLabel(header_frame, text="", image=stl_ctk_image)
        stl_label.pack(side="right", padx=20)

        # Main Tabview
        self.tabview = ctk.CTkTabview(self, width=580, height=360)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Option 1: Independent Control")
        self.tabview.add("Option 2: Both Groups Together")
        self.tabview.add("ADC Data Display")

        # -------- Option 1: Independent Control --------
        option1_frame = self.tabview.tab("Option 1: Independent Control")
        title_label1 = ctk.CTkLabel(option1_frame, text="Independent Control of Two Valve Groups", font=("Helvetica", 16, "bold"))
        title_label1.pack(pady=10)
        ctk.CTkLabel(option1_frame, text="Group 1 (Pins 1 & 2):", font=("Helvetica", 14)).pack(pady=(10, 0))
        self.segmented_button_group1 = ctk.CTkSegmentedButton(option1_frame, values=["Deflation", "Neutral", "Inflation"],
                                                               command=lambda choice: self.independent_group_callback(choice, 1))
        self.segmented_button_group1.set("Neutral")
        self.segmented_button_group1.pack(pady=5)

        ctk.CTkLabel(option1_frame, text="Group 2 (Pins 3 & 4):", font=("Helvetica", 14)).pack(pady=(20, 0))
        self.segmented_button_group2 = ctk.CTkSegmentedButton(option1_frame, values=["Deflation", "Neutral", "Inflation"],
                                                               command=lambda choice: self.independent_group_callback(choice, 2))
        self.segmented_button_group2.set("Neutral")
        self.segmented_button_group2.pack(pady=5)

        # -------- Option 2: Both Groups Together --------
        option2_frame = self.tabview.tab("Option 2: Both Groups Together")
        title_label2 = ctk.CTkLabel(option2_frame, text="Control Both Valve Groups Together", font=("Helvetica", 16, "bold"))
        title_label2.pack(pady=10)
        self.segmented_button_both = ctk.CTkSegmentedButton(option2_frame, values=["Deflation", "Neutral", "Inflation"],
                                                              command=self.both_groups_callback)
        self.segmented_button_both.set("Neutral")
        self.segmented_button_both.pack(pady=5)

        # -------- ADC Data Display --------
        adc_frame = self.tabview.tab("ADC Data Display")
        title_label_adc = ctk.CTkLabel(adc_frame, text="Real-Time ADC Data (Channels 0-4)", font=("Helvetica", 16, "bold"))
        title_label_adc.pack(pady=10)

        # Create labels for each ADC channel
        self.adc_labels = {}
        for ch in range(5):
            lbl = ctk.CTkLabel(adc_frame, text=f"Channel {ch}: -- V", font=("Helvetica", 14))
            lbl.pack(pady=2)
            self.adc_labels[ch] = lbl

        # Reference pressure input and data logging button
        ref_frame = ctk.CTkFrame(adc_frame)
        ref_frame.pack(pady=10)
        ctk.CTkLabel(ref_frame, text="Reference Pressure (kPa/PSI):", font=("Helvetica", 12)).grid(row=0, column=0, padx=5)
        self.ref_entry = ctk.CTkEntry(ref_frame, width=100)
        self.ref_entry.grid(row=0, column=1, padx=5)
        self.log_button = ctk.CTkButton(ref_frame, text="Start Data Logging", command=self.start_logging)
        self.log_button.grid(row=0, column=2, padx=5)

    def independent_group_callback(self, choice, group):
        """Callback for independent valve control segmented buttons."""
        set_group(choice, group)
        # Reset Option 2 button to neutral
        self.segmented_button_both.set("Neutral")

    def both_groups_callback(self, choice):
        """Callback for both groups control segmented button."""
        if choice == "Deflation":
            set_deflation()
        elif choice == "Inflation":
            set_inflation()
        else:
            set_neutral()
        # Reset independent control buttons to neutral
        self.segmented_button_group1.set("Neutral")
        self.segmented_button_group2.set("Neutral")

    def update_adc_display(self):
        """Read ADC values and update the display labels."""
        channels = [0, 1, 2, 3, 4]
        adc_values = self.adc.ADS1263_GetAll(channels)
        for ch in channels:
            raw_value = adc_values[ch]
            # Determine sign and convert to voltage based on datasheet conventions
            if raw_value >> 31 == 0:
                voltage = (raw_value * REF) / 0x7fffffff
            else:
                voltage = (REF * 2 - raw_value * REF / 0x80000000)
            self.adc_labels[ch].configure(text=f"Channel {ch}: {voltage:.6f} V")
        # Schedule next update after 100ms
        self.after(100, self.update_adc_display)

    def start_logging(self):
        """Start data logging in a separate thread."""
        ref_pressure = self.ref_entry.get().strip()
        if not ref_pressure:
            messagebox.showerror("Input Error", "Please enter a reference pressure value.")
            return
        try:
            # You may cast ref_pressure to float if needed
            float(ref_pressure)
        except ValueError:
            messagebox.showerror("Input Error", "Reference pressure must be a number.")
            return

        # Disable button to avoid re-entrance
        self.log_button.configure(state="disabled")
        t = Thread(target=self.collect_and_log_data, args=(ref_pressure,))
        t.daemon = True
        t.start()

    def collect_and_log_data(self, ref_pressure):
        """Collect 100 samples from channels 0-4 and log to CSV."""
        samples_per_level = 100
        filename = "adc_data.csv"
        # Write header
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'channel', 'raw ADC value', 'voltage', 'temperature', 'reference_pressure'])
        # Collect samples
        for i in range(samples_per_level):
            data_rows = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            channels = [0, 1, 2, 3, 4]
            adc_values = self.adc.ADS1263_GetAll(channels)
            for ch in channels:
                raw_value = adc_values[ch]
                if raw_value >> 31 == 0:
                    voltage = (raw_value * REF) / 0x7fffffff
                else:
                    voltage = (REF * 2 - raw_value * REF / 0x80000000)
                # 'temperature' is a placeholder ('N/A')
                data_rows.append([timestamp, ch, raw_value, voltage, 'N/A', ref_pressure])
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data_rows)
            time.sleep(0.05)  # Adjust sampling delay as needed
        # After logging, re-enable the button and show a popup message
        self.log_button.configure(state="normal")
        messagebox.showinfo("Data Logging", f"Data logging complete. {samples_per_level} samples collected and saved to {filename}.")

    def on_key(self, event):
        """Bind the 'q' key to quit the application."""
        if event.char.lower() == "q":
            self.on_close()

    def on_close(self):
        """Cleanup on application close."""
        try:
            self.adc.ADS1263_Exit()
        except Exception:
            pass
        lgpio.gpiochip_close(chip)
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
