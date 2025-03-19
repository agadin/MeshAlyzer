#!/usr/bin/python
# -*- coding:utf-8 -*-

import customtkinter as ctk
from PIL import Image
import ADS1263         # Ensure ADS1263.py is in the same directory.
import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime
from threading import Thread
from tkinter import messagebox
import bme680

# ---------------------------
# BME680 SENSOR FUNCTIONS
# ---------------------------
def setup_sensor():
    """Initialize and configure the BME680 sensor."""
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    return sensor

def read_sensor_data(sensor):
    """Read data from the BME680 sensor."""
    if sensor.get_sensor_data():
        return {
            "temperature": sensor.data.temperature,
            "pressure": sensor.data.pressure,
            "humidity": sensor.data.humidity,
        }
    else:
        return None

# ---------------------------
# GLOBAL CONSTANTS
# ---------------------------
REF = 5.08  # Reference voltage for ADC conversion

# ---------------------------
# GPIO SETUP (using RPi.GPIO)
# ---------------------------
GPIO.setmode(GPIO.BCM)
# Valve control pins
PIN1 = 5    # Inflation valve group 1
PIN2 = 27   # Deflation valve group 1
PIN3 = 23   # Inflation valve group 2
PIN4 = 24   # Deflation valve group 2

# Setup pins as outputs and initialize them to LOW
for pin in (PIN1, PIN2, PIN3, PIN4):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# ---------------------------
# VALVE CONTROL FUNCTIONS
# ---------------------------
def set_inflation():
    """Activate inflation valves (Pins 1 & 3) and deactivate deflation valves."""
    GPIO.output(PIN1, GPIO.HIGH)
    GPIO.output(PIN3, GPIO.HIGH)
    GPIO.output(PIN2, GPIO.LOW)
    GPIO.output(PIN4, GPIO.LOW)

def set_deflation():
    """Activate deflation valves (Pins 2 & 4) and deactivate inflation valves."""
    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN3, GPIO.LOW)
    GPIO.output(PIN2, GPIO.HIGH)
    GPIO.output(PIN4, GPIO.HIGH)

def set_neutral():
    """Set all valves to neutral (off)."""
    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN2, GPIO.LOW)
    GPIO.output(PIN3, GPIO.LOW)
    GPIO.output(PIN4, GPIO.LOW)

def set_group(mode, group):
    """
    Controls a single group of valves (group 1 or 2).
    mode: "Deflation", "Neutral", or "Inflation".
    """
    if group == 1:
        if mode == "Deflation":
            GPIO.output(PIN1, GPIO.LOW)
            GPIO.output(PIN2, GPIO.HIGH)
        elif mode == "Inflation":
            GPIO.output(PIN1, GPIO.HIGH)
            GPIO.output(PIN2, GPIO.LOW)
        else:
            GPIO.output(PIN1, GPIO.LOW)
            GPIO.output(PIN2, GPIO.LOW)
    elif group == 2:
        if mode == "Deflation":
            GPIO.output(PIN3, GPIO.LOW)
            GPIO.output(PIN4, GPIO.HIGH)
        elif mode == "Inflation":
            GPIO.output(PIN3, GPIO.HIGH)
            GPIO.output(PIN4, GPIO.LOW)
        else:
            GPIO.output(PIN3, GPIO.LOW)
            GPIO.output(PIN4, GPIO.LOW)

# ---------------------------
# MAIN APPLICATION CLASS
# ---------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MeshAlyzer: Pressure Sensor Verification Test")
        self.geometry("600x700")

        # Initialize the ADS1263 ADC (using ADC1 in differential mode)
        self.adc = self.adc_init()

        # Initialize the BME680 sensor
        self.bme_sensor = setup_sensor()

        # Set up the GUI components
        self.setup_gui()

        # Start live ADC data updates
        self.update_adc_display()

    def adc_init(self):
        """Initialize the ADS1263 ADC for ADC1."""
        adc = ADS1263.ADS1263()
        if adc.ADS1263_init_ADC1('ADS1263_400SPS') == -1:
            self.destroy()
            raise Exception("Failed to initialize ADS1263 ADC.")
        # Set to differential mode so channels 0-4 are available
        adc.ADS1263_SetMode(1)
        return adc

    def setup_gui(self):
        """Set up the GUI layout and widgets."""
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.bind("<Key>", self.on_key)

        # Header with logos
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", pady=10)
        try:
            meshalyzer_img = Image.open("MeshAlyzer.jpeg")
            stl_img = Image.open("lakelab.jpg")
        except FileNotFoundError:
            meshalyzer_img = Image.new("RGB", (220, 80), color="gray")
            stl_img = Image.new("RGB", (120, 80), color="gray")
        meshalyzer_ctk_img = ctk.CTkImage(dark_image=meshalyzer_img, size=(220, 80))
        stl_ctk_img = ctk.CTkImage(dark_image=stl_img, size=(120, 80))
        meshalyzer_label = ctk.CTkLabel(header_frame, text="", image=meshalyzer_ctk_img)
        meshalyzer_label.pack(side="left", padx=20)
        stl_label = ctk.CTkLabel(header_frame, text="", image=stl_ctk_img)
        stl_label.pack(side="right", padx=20)

        # Main Tabview with two tabs: Option 1 and Option 2
        self.tabview = ctk.CTkTabview(self, width=580, height=480)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Option 1: Independent Control")
        self.tabview.add("Option 2: Both Groups Together")

        # --- Option 1: Independent Control ---
        option1_frame = self.tabview.tab("Option 1: Independent Control")
        title_label1 = ctk.CTkLabel(option1_frame, text="Independent Control of Two Valve Groups",
                                    font=("Helvetica", 16, "bold"))
        title_label1.pack(pady=10)
        ctk.CTkLabel(option1_frame, text="Group 1 (Pins 1 & 2):", font=("Helvetica", 14)).pack(pady=(10, 0))
        self.segmented_button_group1 = ctk.CTkSegmentedButton(option1_frame,
                                                               values=["Deflation", "Neutral", "Inflation"],
                                                               command=lambda choice: self.independent_group_callback(choice, 1))
        self.segmented_button_group1.set("Neutral")
        self.segmented_button_group1.pack(pady=5)
        ctk.CTkLabel(option1_frame, text="Group 2 (Pins 3 & 4):", font=("Helvetica", 14)).pack(pady=(20, 0))
        self.segmented_button_group2 = ctk.CTkSegmentedButton(option1_frame,
                                                               values=["Deflation", "Neutral", "Inflation"],
                                                               command=lambda choice: self.independent_group_callback(choice, 2))
        self.segmented_button_group2.set("Neutral")
        self.segmented_button_group2.pack(pady=5)
        # Live ADC Data Display for Option 1
        adc_frame1 = ctk.CTkFrame(option1_frame)
        adc_frame1.pack(pady=10)
        adc_title1 = ctk.CTkLabel(adc_frame1, text="Live ADC Data (Channels 0-4)", font=("Helvetica", 14, "bold"))
        adc_title1.pack(pady=(0, 5))
        self.adc_labels_option1 = {}
        for ch in range(5):
            lbl = ctk.CTkLabel(adc_frame1, text=f"Channel {ch}: -- V", font=("Helvetica", 12))
            lbl.pack(pady=2)
            self.adc_labels_option1[ch] = lbl

        # --- Option 2: Both Groups Together ---
        option2_frame = self.tabview.tab("Option 2: Both Groups Together")
        title_label2 = ctk.CTkLabel(option2_frame, text="Control Both Valve Groups Together",
                                    font=("Helvetica", 16, "bold"))
        title_label2.pack(pady=10)
        self.segmented_button_both = ctk.CTkSegmentedButton(option2_frame,
                                                             values=["Deflation", "Neutral", "Inflation"],
                                                             command=self.both_groups_callback)
        self.segmented_button_both.set("Neutral")
        self.segmented_button_both.pack(pady=5)
        # Live ADC Data Display for Option 2
        adc_frame2 = ctk.CTkFrame(option2_frame)
        adc_frame2.pack(pady=10)
        adc_title2 = ctk.CTkLabel(adc_frame2, text="Live ADC Data (Channels 0-4)", font=("Helvetica", 14, "bold"))
        adc_title2.pack(pady=(0, 5))
        self.adc_labels_option2 = {}
        for ch in range(5):
            lbl = ctk.CTkLabel(adc_frame2, text=f"Channel {ch}: -- V", font=("Helvetica", 12))
            lbl.pack(pady=2)
            self.adc_labels_option2[ch] = lbl

        # --- Logging Section (common to both tabs) ---
        # This section now includes two input fields: one for the "Reference Pressure"
        # (e.g., the expected pressure from the sensor's calibration) and one for the
        # "Actual Pressure" provided by your calibrated air regulator.
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(pady=10)
        # Reference pressure entry
        ctk.CTkLabel(log_frame, text="Reference Pressure (kPa/PSI):", font=("Helvetica", 12)).grid(row=0, column=0, padx=5)
        self.ref_entry = ctk.CTkEntry(log_frame, width=100)
        self.ref_entry.grid(row=0, column=1, padx=5)
        # Actual known pressure entry
        ctk.CTkLabel(log_frame, text="Actual Pressure (kPa/PSI):", font=("Helvetica", 12)).grid(row=1, column=0, padx=5)
        self.actual_entry = ctk.CTkEntry(log_frame, width=100)
        self.actual_entry.grid(row=1, column=1, padx=5)
        # Logging button
        self.log_button = ctk.CTkButton(log_frame, text="Start Data Logging", command=self.start_logging)
        self.log_button.grid(row=0, column=2, rowspan=2, padx=5)

    def independent_group_callback(self, choice, group):
        """Callback for independent valve control buttons."""
        set_group(choice, group)
        self.segmented_button_both.set("Neutral")

    def both_groups_callback(self, choice):
        """Callback for both groups control button."""
        if choice == "Deflation":
            set_deflation()
        elif choice == "Inflation":
            set_inflation()
        else:
            set_neutral()
        self.segmented_button_group1.set("Neutral")
        self.segmented_button_group2.set("Neutral")

    def update_adc_display(self):
        """Update live ADC data on both Option 1 and Option 2 displays every 100 ms."""
        channels = [0, 1, 2, 3, 4]
        adc_values = self.adc.ADS1263_GetAll(channels)
        for ch in channels:
            raw_value = adc_values[ch]
            if raw_value >> 31 == 0:
                voltage = (raw_value * REF) / 0x7fffffff
            else:
                voltage = (REF * 2 - raw_value * REF / 0x80000000)
            if ch in self.adc_labels_option1:
                self.adc_labels_option1[ch].configure(text=f"Channel {ch}: {voltage:.6f} V")
            if ch in self.adc_labels_option2:
                self.adc_labels_option2[ch].configure(text=f"Channel {ch}: {voltage:.6f} V")
        self.after(100, self.update_adc_display)

    def start_logging(self):
        """Start data logging when the user clicks the logging button."""
        ref_pressure = self.ref_entry.get().strip()
        actual_pressure = self.actual_entry.get().strip()
        if not ref_pressure or not actual_pressure:
            messagebox.showerror("Input Error", "Please enter both the reference and actual pressure values.")
            return
        try:
            float(ref_pressure)
            float(actual_pressure)
        except ValueError:
            messagebox.showerror("Input Error", "Both pressure values must be numbers.")
            return
        self.log_button.configure(state="disabled")
        t = Thread(target=self.collect_and_log_data, args=(ref_pressure, actual_pressure))
        t.daemon = True
        t.start()

    def collect_and_log_data(self, ref_pressure, actual_pressure):
        """Collect 100 samples from ADC and BME680 sensors and log them to a CSV file."""
        samples_per_level = 100
        filename = "sensor_data.csv"
        # CSV header includes timestamp, reference_pressure, actual_pressure,
        # ADC readings (channels 0-4), and BME680 sensor readings.
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'timestamp', 'reference_pressure', 'actual_pressure',
                'ADC_channel_0', 'ADC_channel_1', 'ADC_channel_2', 'ADC_channel_3', 'ADC_channel_4',
                'BME680_pressure', 'BME680_temperature', 'BME680_humidity'
            ])
        for i in range(samples_per_level):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            channels = [0, 1, 2, 3, 4]
            adc_values = self.adc.ADS1263_GetAll(channels)
            adc_readings = []
            for ch in channels:
                raw_value = adc_values[ch]
                if raw_value >> 31 == 0:
                    voltage = (raw_value * REF) / 0x7fffffff
                else:
                    voltage = (REF * 2 - raw_value * REF / 0x80000000)
                adc_readings.append(voltage)
            # Read BME680 sensor data
            bme_data = read_sensor_data(self.bme_sensor)
            if bme_data is None:
                bme_pressure = ""
                bme_temperature = ""
                bme_humidity = ""
            else:
                bme_pressure = bme_data['pressure']
                bme_temperature = bme_data['temperature']
                bme_humidity = bme_data['humidity']
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp, ref_pressure, actual_pressure,
                    adc_readings[0], adc_readings[1], adc_readings[2], adc_readings[3], adc_readings[4],
                    bme_pressure, bme_temperature, bme_humidity
                ])
            time.sleep(0.05)  # Adjust sampling rate as needed
        self.log_button.configure(state="normal")
        messagebox.showinfo("Data Logging", f"Data logging complete. {samples_per_level} samples saved to {filename}.")

    def on_key(self, event):
        """Bind the 'q' key to exit the application."""
        if event.char.lower() == "q":
            self.on_close()

    def on_close(self):
        """Cleanup resources on application close."""
        try:
            self.adc.ADS1263_Exit()
        except Exception:
            pass
        GPIO.cleanup()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
