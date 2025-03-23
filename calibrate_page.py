# --- New CalibratePage class (modified) ---
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

        # Graph frame in the middle to show pressureX_convert values
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(expand=True, fill="both", padx=10, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        self.ax.set_title("Pressure Sensor Converted Values")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pressure Convert Value")

        # Bottom frame with sensor toggle buttons
        self.bottom_frame = ctk.CTkFrame(self, height=50)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)

        # Create three sensor buttons – default color is gray.
        self.sensor1_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 1", fg_color="gray",
                                            command=lambda: self.toggle_sensor(0))
        self.sensor1_button.pack(side="left", padx=10)

        self.sensor2_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 2", fg_color="gray",
                                            command=lambda: self.toggle_sensor(1))
        self.sensor2_button.pack(side="left", padx=10)

        self.sensor3_button = ctk.CTkButton(self.bottom_frame, text="Pressure Sensor 3", fg_color="gray",
                                            command=lambda: self.toggle_sensor(2))
        self.sensor3_button.pack(side="left", padx=10)

        # Sensor selection state (True if selected)
        self.sensor_selected = [False, False, False]

        # Start a periodic update of the graph
        self.update_graph()

    def toggle_sensor(self, sensor_index):
        # Toggle selection state and update button color (still gray if not yet calibrated)
        self.sensor_selected[sensor_index] = not self.sensor_selected[sensor_index]
        new_color = "darkgray" if self.sensor_selected[sensor_index] else "gray"
        if sensor_index == 0:
            self.sensor1_button.configure(fg_color=new_color)
        elif sensor_index == 1:
            self.sensor2_button.configure(fg_color=new_color)
        elif sensor_index == 2:
            self.sensor3_button.configure(fg_color=new_color)

    def update_graph(self):
        # Clear the axes and plot current data from app.sensor_data
        self.ax.cla()
        self.ax.set_title("Pressure Sensor Converted Values")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pressure Convert Value")
        times = [data['time'] for data in self.app.sensor_data if data['time'] >= 0]
        if times:
            p0 = [data['pressure0_convert'] for data in self.app.sensor_data if data['time'] >= 0]
            p1 = [data['pressure1_convert'] for data in self.app.sensor_data if data['time'] >= 0]
            p2 = [data['pressure2_convert'] for data in self.app.sensor_data if data['time'] >= 0]
            p3 = [data['pressure3_convert'] for data in self.app.sensor_data if data['time'] >= 0]
            self.ax.plot(times, p0, label="Pressure0_convert")
            self.ax.plot(times, p1, label="Pressure1_convert")
            self.ax.plot(times, p2, label="Pressure2_convert")
            self.ax.plot(times, p3, label="Pressure3_convert")
            self.ax.legend()
        self.canvas.draw()
        self.after(1000, self.update_graph)

    def start_check_calibration(self):
        # Popup to prompt the user for a reference pressure and sensor selection
        popup = ctk.CTkToplevel(self)
        popup.title("Check Calibration")

        tk.Label(popup, text="Enter Reference Pressure:").pack(padx=10, pady=5)
        ref_entry = ctk.CTkEntry(popup)
        ref_entry.pack(padx=10, pady=5)

        tk.Label(popup, text="Select sensors experiencing the reference pressure:").pack(padx=10, pady=5)
        sensor_vars = [tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()]
        ctk.CTkCheckBox(popup, text="Pressure Sensor 1 (Pressure0)", variable=sensor_vars[0]).pack(padx=10, pady=2)
        ctk.CTkCheckBox(popup, text="Pressure Sensor 2 (Pressure1)", variable=sensor_vars[1]).pack(padx=10, pady=2)
        ctk.CTkCheckBox(popup, text="Pressure Sensor 3 (Pressure2)", variable=sensor_vars[2]).pack(padx=10, pady=2)

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
        """
        Calibration check process:
          - Depending on sensor selection, call valve supply methods.
          - Activate the valves continuously for 10 seconds.
          - After 10 seconds, call the neutral method on both valves.
          - Record the latest sensor values and perform a calibration check.
        """
        if self.sensor_selected[1]:
            self.app.valve1.supply()
        if self.sensor_selected[2]:
            self.app.valve2.supply()
        if self.sensor_selected[0] and not any(self.sensor_selected[1:]):
            self.app.valve1.supply()
            self.app.valve2.supply()

        time.sleep(10)  # Continuous supply for 10 seconds

        # Turn off the supply by setting valves to neutral
        self.app.valve1.neutral()
        self.app.valve2.neutral()

        rec = self.app.sensor_data[-1]
        avg_values = [
            rec.get('pressure0_convert', 0),
            rec.get('pressure1_convert', 0),
            rec.get('pressure2_convert', 0)
        ]
        tolerance = 0.05
        success = [False, False, False]
        for i, avg in enumerate(avg_values):
            if ref_pressure != 0 and abs(avg - ref_pressure) / ref_pressure <= tolerance:
                success[i] = True
            else:
                success[i] = False
        self.update_sensor_buttons(success)

    def start_sensor_calibration(self):
        """
        Sensor calibration process:
         - Prompt the user for a reference pressure of 0 psi.
         - Display a prompt indicating that calibration will be done for pressures
           increasing by 7.25 psi from 0 up to 145 psi.
         - For each desired pressure:
             - Activate both valves continuously for 10 seconds.
             - Then set the valves to neutral and record a sensor reading.
         - Save the collected data to a CSV file.
         - No venting is performed.
        """
        popup = ctk.CTkToplevel(self)
        popup.title("Calibrate Sensors (0 psi)")
        # Updated prompt showing desired pressures from 0 to 145 psi in 7.25 psi increments.
        desired_pressures = [round(i * 7.25, 2) for i in range(int(145 / 7.25) + 1)]
        prompt_text = ("Calibrate sensors for desired pressures:\n" +
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

    def perform_sensor_calibration(self, ref_pressure):
        """
        For each calibration step from 0 psi to 145 psi (increment 7.25 psi):
          - Activate both valves continuously for 10 seconds.
          - After 10 seconds, set valves to neutral.
          - Record a single sensor reading.
          - Save the collected data to a CSV file.
        """
        current_pressure = 0
        increment = 7.25
        calibration_results = []  # store calibration data for each step

        while current_pressure <= 145:
            self.app.valve1.supply()
            self.app.valve2.supply()
            time.sleep(10)
            self.app.valve1.neutral()
            self.app.valve2.neutral()
            rec = self.app.sensor_data[-1]
            avg_values = [
                rec.get('pressure0_convert', 0),
                rec.get('pressure1_convert', 0),
                rec.get('pressure2_convert', 0)
            ]
            calibration_results.append({
                "reference_pressure": current_pressure,
                "avg_pressure0_convert": avg_values[0],
                "avg_pressure1_convert": avg_values[1],
                "avg_pressure2_convert": avg_values[2]
            })
            current_pressure += increment

        # Create CSV folder if it doesn't exist
        calibration_folder = f"calibration_{datetime.datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(calibration_folder):
            os.makedirs(calibration_folder)
        csv_filename = os.path.join(
            calibration_folder,
            f"raw_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_0_psi_calibration.csv"
        )
        import csv
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                "reference_pressure", "avg_pressure0_convert", "avg_pressure1_convert", "avg_pressure2_convert"
            ])
            writer.writeheader()
            for row in calibration_results:
                writer.writerow(row)
        complete_popup = ctk.CTkToplevel(self)
        complete_popup.title("Calibration Complete")
        tk.Label(complete_popup, text="Sensor calibration is complete and data has been saved.").pack(padx=10, pady=10)
        ctk.CTkButton(complete_popup, text="OK", command=complete_popup.destroy).pack(pady=5)

    def update_sensor_buttons(self, success_list):
        color_map = {True: "green", False: "red"}
        self.sensor1_button.configure(fg_color=color_map[success_list[0]])
        self.sensor2_button.configure(fg_color=color_map[success_list[1]])
        self.sensor3_button.configure(fg_color=color_map[success_list[2]])