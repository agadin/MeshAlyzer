# --- New CalibratePage class (updated with 7.25 psi increments) ---
import customtkinter as ctk
import shutil
import multiprocessing.shared_memory as sm
from tkinter import Canvas, Frame, Scrollbar, filedialog, StringVar
from PIL import Image, ImageTk, ImageOps
import cv2
import queue
import time
import struct
import csv
from collections import defaultdict
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import seaborn as sns
from tkinter import ttk
import matplotlib.ticker as ticker
import datetime
import tkinter as tk
import subprocess
import threading
import sys
import os
import filecmp
import cairosvg
import xml.etree.ElementTree as ET

# lps22
import board
import busio
import adafruit_lps2x

class CalibratePage(ctk.CTkFrame):
    def __init__(self, master, app, *args, **kwargs):
        """
        master: the parent frame (self.content_frame)
        app: a reference to the App instance so that we can access valves, sensor_data, etc.
        """
        super().__init__(master, *args, **kwargs)
        self.app = app  # reference to main App instance

        # Top frame with calibration control buttons
        self.top_frame = ctk.CTkFrame(self, height=50)
        self.top_frame.pack(fill="x", padx=10, pady=5)

        self.check_calib_button = ctk.CTkButton(self.top_frame, text="Check Calibration",
                                                command=self.start_check_calibration)
        self.check_calib_button.pack(side="left", padx=10)

        self.sensor_calib_button = ctk.CTkButton(self.top_frame, text="Calibrate Pressure Sensors",
                                                 command=self.start_sensor_calibration)
        self.sensor_calib_button.pack(side="left", padx=10)

        # Graph frame in the middle to show pressure values
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(expand=True, fill="both", padx=10, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        self.ax.set_title("Pressure Sensor Raw Values")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pressure Value")

        # Bottom frame with sensor toggle buttons
        self.bottom_frame = ctk.CTkFrame(self, height=50)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)

        self.sensor1_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 1", fg_color="gray",
                                            command=lambda: self.toggle_sensor(0))
        self.sensor1_button.pack(side="left", padx=10)

        self.sensor2_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 2", fg_color="gray",
                                            command=lambda: self.toggle_sensor(1))
        self.sensor2_button.pack(side="left", padx=10)

        self.sensor3_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 3", fg_color="gray",
                                            command=lambda: self.toggle_sensor(2))
        self.sensor3_button.pack(side="left", padx=10)

        self.sensor_selected = [False, False, False]
        self.update_graph()

    def toggle_sensor(self, sensor_index):
        self.sensor_selected[sensor_index] = not self.sensor_selected[sensor_index]
        new_color = "darkgray" if self.sensor_selected[sensor_index] else "gray"
        if sensor_index == 0:
            self.sensor1_button.configure(fg_color=new_color)
        elif sensor_index == 1:
            self.sensor2_button.configure(fg_color=new_color)
        elif sensor_index == 2:
            self.sensor3_button.configure(fg_color=new_color)

    def update_graph(self):
        self.ax.cla()
        self.ax.set_title("Pressure Sensor Raw Values")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pressure Value")
        times = [data['time'] for data in self.app.sensor_data if data['time'] >= 0]
        if times:
            p0 = [data['pressure0'] for data in self.app.sensor_data if data['time'] >= 0]
            p1 = [data['pressure1'] for data in self.app.sensor_data if data['time'] >= 0]
            p2 = [data['pressure2'] for data in self.app.sensor_data if data['time'] >= 0]
            p3 = [data['pressure3'] for data in self.app.sensor_data if data['time'] >= 0]
            self.ax.plot(times, p0, label="Pressure0")
            self.ax.plot(times, p1, label="Pressure1")
            self.ax.plot(times, p2, label="Pressure2")
            self.ax.plot(times, p3, label="Pressure3")
            self.ax.legend()
        self.canvas.draw()
        self.after(1000, self.update_graph)

    def start_check_calibration(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Check Calibration")
        tk.Label(popup, text="Enter Reference Pressure:").pack(padx=10, pady=5)
        ref_entry = ctk.CTkEntry(popup)
        ref_entry.pack(padx=10, pady=5)
        tk.Label(popup, text="Select sensors experiencing the reference pressure:").pack(padx=10, pady=5)
        sensor_vars = [tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()]
        ctk.CTkCheckBox(popup, text="Pressure Sensor 1", variable=sensor_vars[0]).pack(padx=10, pady=2)
        ctk.CTkCheckBox(popup, text="Pressure Sensor 2", variable=sensor_vars[1]).pack(padx=10, pady=2)
        ctk.CTkCheckBox(popup, text="Pressure Sensor 3", variable=sensor_vars[2]).pack(padx=10, pady=2)

        def on_submit():
            try:
                ref_pressure = float(ref_entry.get())
            except ValueError:
                tk.Label(popup, text="Invalid input, please enter a number.", fg="red").pack()
                return
            self.sensor_selected = [var.get() for var in sensor_vars]
            popup.destroy()
            threading.Thread(target=self.perform_check_calibration, args=(ref_pressure,), daemon=True).start()

        submit_btn = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_btn.pack(padx=10, pady=10)

    def perform_check_calibration(self, ref_pressure):
        if self.sensor_selected[1]:
            self.app.valve1.supply()
        if self.sensor_selected[2]:
            self.app.valve2.supply()
        if self.sensor_selected[0] and not any(self.sensor_selected[1:]):
            self.app.valve1.supply()
            self.app.valve2.supply()
        print("Check Calibration: Valves activated. Waiting 10 seconds...")
        time.sleep(10)
        self.app.valve1.neutral()
        self.app.valve2.neutral()
        print("Check Calibration: Valves set to neutral.")
        rec = self.app.sensor_data[-1]
        avg_values = [
            rec.get('pressure0', 0),
            rec.get('pressure1', 0),
            rec.get('pressure2', 0)
        ]
        tolerance = 0.05
        success = [False, False, False]
        for i, avg in enumerate(avg_values):
            if ref_pressure != 0 and abs(avg - ref_pressure) / ref_pressure <= tolerance:
                success[i] = True
            else:
                success[i] = False
        self.update_sensor_buttons(success)
        print(f"Check Calibration: Sensor readings: {avg_values}. Success flags: {success}")

    def start_sensor_calibration(self):
        """
        Sensor calibration process:
         - Prompt the user for a reference pressure (should be 0 psi) once.
         - For each target pressure (0 to 145 psi in 7.25 psi increments):
             * Prompt the user to enter the measured pressure for that target (before supplying air).
             * Activate both valves for 10 seconds.
             * Call the neutral methods to stop the air supply.
             * Save a separate CSV file (for that target pressure) under the base folder 'calibration_data'.
        """
        popup = ctk.CTkToplevel(self)
        popup.title("Calibrate Sensors (0 psi)")
        desired_pressures = [round(i * 7.25, 2) for i in range(int(145 / 7.25) + 1)]
        prompt_text = ("Calibration will be performed for target pressures:\n" +
                       ", ".join(str(p) + " psi" for p in desired_pressures) +
                       "\n\nEnter reference pressure (should be 0 psi):")
        tk.Label(popup, text=prompt_text).pack(padx=10, pady=5)
        ref_entry = ctk.CTkEntry(popup)
        ref_entry.pack(padx=10, pady=5)

        def on_submit():
            try:
                ref_pressure = float(ref_entry.get())
            except ValueError:
                tk.Label(popup, text="Invalid input, please enter a number.", fg="red").pack()
                return
            if ref_pressure != 0:
                tk.Label(popup, text="Reference pressure must be 0 psi for sensor calibration.", fg="red").pack()
                return
            popup.destroy()
            threading.Thread(target=self.perform_sensor_calibration, args=(ref_pressure,), daemon=True).start()

        submit_btn = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_btn.pack(padx=10, pady=10)

    def prompt_measured_pressure_before(self, target_pressure):
        """
        Displays a popup prompting the user to input the measured pressure
        for the given target pressure before the air supply is activated.
        Returns the entered value as a float.
        """
        result = []
        popup = ctk.CTkToplevel(self)
        popup.title("Enter Measured Pressure")
        tk.Label(popup, text=f"Set value of pressure close to ~{target_pressure} psi:").pack(padx=10, pady=5)
        entry = ctk.CTkEntry(popup)
        entry.pack(padx=10, pady=5)

        def on_submit():
            try:
                val = float(entry.get())
            except ValueError:
                tk.Label(popup, text="Invalid input. Please enter a number.", fg="red").pack()
                return
            result.append(val)
            popup.destroy()

        submit_btn = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_btn.pack(padx=10, pady=10)
        popup.wait_window()  # Wait until the popup is closed.
        return result[0] if result else 0

    def perform_sensor_calibration(self, ref_pressure):
        current_pressure = 0
        increment = 7.25
        base_folder = "calibration_data"
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)
            print(f"Created base folder: {base_folder}")
        calibration_folder = os.path.join(base_folder, f"calibration_{datetime.datetime.now().strftime('%Y%m%d')}")
        if not os.path.exists(calibration_folder):
            os.makedirs(calibration_folder)
            print(f"Created calibration folder: {calibration_folder}")

        print("Starting full sensor calibration...")
        while current_pressure <= 145:
            print(f"Calibrating at target {current_pressure} psi...")
            # Prompt the user for the measured pressure for the current target BEFORE supplying air.
            measured_pressure = self.prompt_measured_pressure_before(current_pressure)
            print(f"User entered measured pressure: {measured_pressure} psi for target {current_pressure} psi")

            # Supply air for 10 seconds.
            self.app.valve1.supply()
            self.app.valve2.supply()
            print("Valves activated for 10 seconds...")
            time.sleep(10)
            # Stop air supply.
            self.app.valve1.neutral()
            self.app.valve2.neutral()
            print("Valves set to neutral after 10 seconds.")

            # Save a separate CSV file for this target pressure.
            csv_filename = os.path.join(
                calibration_folder,
                f"calibration_{current_pressure}_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            )
            print(f"Saving calibration data for target {current_pressure} psi to file: {csv_filename}")
            import csv
            with open(csv_filename, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["target_pressure", "measured_pressure"])
                writer.writeheader()
                writer.writerow({
                    "target_pressure": current_pressure,
                    "measured_pressure": measured_pressure
                })
            print(f"Calibration data for {current_pressure} psi saved successfully.")
            current_pressure += increment

        print("Full sensor calibration complete. All data saved.")
        complete_popup = ctk.CTkToplevel(self)
        complete_popup.title("Calibration Complete")
        tk.Label(complete_popup, text="Sensor calibration is complete and all data has been saved.").pack(padx=10,
                                                                                                          pady=10)
        ctk.CTkButton(complete_popup, text="OK", command=complete_popup.destroy).pack(pady=5)

    def update_sensor_buttons(self, success_list):
        color_map = {True: "green", False: "red"}
        self.sensor1_button.configure(fg_color=color_map[success_list[0]])
        self.sensor2_button.configure(fg_color=color_map[success_list[1]])
        self.sensor3_button.configure(fg_color=color_map[success_list[2]])
