import time
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import threading
import os

class CalibratePage(ctk.CTkFrame):
    def __init__(self, master, app, *args, **kwargs):
        """
        master: parent frame (e.g. self.content_frame)
        app: reference to the main App instance (providing sensor data, valves, etc.)
        """
        super().__init__(master, *args, **kwargs)
        self.app = app

        # --- Header ---
        self.header_label = ctk.CTkLabel(self, text="Calibrate", font=("Arial", 20, "bold"))
        self.header_label.pack(padx=10, pady=(10, 5))

        # --- Top frame for calibration buttons ---
        self.top_frame = ctk.CTkFrame(self, height=60)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        self.top_frame.columnconfigure((0, 1), weight=1)

        self.check_calib_button = ctk.CTkButton(
            self.top_frame,
            text="Check Calibration",
            command=self.start_check_calibration,
            width=150, height=40,
            font=("Arial", 14)
        )
        self.check_calib_button.grid(row=0, column=0, padx=10, pady=5)

        self.sensor_calib_button = ctk.CTkButton(
            self.top_frame,
            text="Calibrate Pressure Sensors",
            command=self.start_sensor_calibration,
            width=200, height=40,
            font=("Arial", 14)
        )
        self.sensor_calib_button.grid(row=0, column=1, padx=10, pady=5)

        # --- Sensor Values Display (only sensors 0-2) ---
        self.sensor_values_frame = ctk.CTkFrame(self, height=50)
        self.sensor_values_frame.pack(fill="x", padx=10, pady=5)
        self.sensor_values_frame.columnconfigure((0, 1, 2), weight=1)

        self.sensor0_label = ctk.CTkLabel(
            self.sensor_values_frame, text="Sensor 1: N/A", font=("Arial", 16)
        )
        self.sensor0_label.grid(row=0, column=0, padx=5, pady=5)
        self.sensor1_label = ctk.CTkLabel(
            self.sensor_values_frame, text="Sensor 2: N/A", font=("Arial", 16)
        )
        self.sensor1_label.grid(row=0, column=1, padx=5, pady=5)
        self.sensor2_label = ctk.CTkLabel(
            self.sensor_values_frame, text="Sensor 3: N/A", font=("Arial", 16)
        )
        self.sensor2_label.grid(row=0, column=2, padx=5, pady=5)
        self.update_sensor_values()  # Start updating sensor labels

        # --- Graph Frame ---
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(expand=True, fill="both", padx=10, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        self.ax.set_title("Pressure Sensor Raw Values")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("PSI")

        # --- Bottom frame for sensor toggle buttons ---
        self.bottom_frame = ctk.CTkFrame(self, height=60)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)
        self.bottom_frame.columnconfigure((0, 1, 2), weight=1)

        self.sensor1_button = ctk.CTkButton(
            self.bottom_frame,
            text="Pressure Sensor 1",
            fg_color="gray",
            width=150, height=40,
            font=("Arial", 14),
            command=lambda: self.toggle_sensor(0)
        )
        self.sensor1_button.grid(row=0, column=0, padx=10, pady=5)

        self.sensor2_button = ctk.CTkButton(
            self.bottom_frame,
            text="Pressure Sensor 2",
            fg_color="gray",
            width=150, height=40,
            font=("Arial", 14),
            command=lambda: self.toggle_sensor(1)
        )
        self.sensor2_button.grid(row=0, column=1, padx=10, pady=5)

        self.sensor3_button = ctk.CTkButton(
            self.bottom_frame,
            text="Pressure Sensor 3",
            fg_color="gray",
            width=150, height=40,
            font=("Arial", 14),
            command=lambda: self.toggle_sensor(2)
        )
        self.sensor3_button.grid(row=0, column=2, padx=10, pady=5)

        self.sensor_selected = [False, False, False]

        # Start the graph update loop.
        self.update_graph()

    def update_sensor_values(self):
        try:
            # Format values to 2 decimal places if numeric; otherwise show N/A.
            value0 = f"{self.app.pressure0_convert:.2f}" if hasattr(self.app, "pressure0_convert") and isinstance(
                self.app.pressure0_convert, (int, float)) else "N/A"
            value1 = f"{self.app.pressure1_convert:.2f}" if hasattr(self.app, "pressure1_convert") and isinstance(
                self.app.pressure1_convert, (int, float)) else "N/A"
            value2 = f"{self.app.pressure2_convert:.2f}" if hasattr(self.app, "pressure2_convert") and isinstance(
                self.app.pressure2_convert, (int, float)) else "N/A"
            self.sensor0_label.configure(text=f"Sensor 0: {value0}")
            self.sensor1_label.configure(text=f"Sensor 1: {value1}")
            self.sensor2_label.configure(text=f"Sensor 2: {value2}")
        except Exception as e:
            print(f"Error updating sensor values: {e}")
        self.after(500, self.update_sensor_values)

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
        try:
            # Clear the axis and set the background color based on appearance mode.
            self.ax.clear()
            if ctk.get_appearance_mode() == "Dark":
                app_bg_color = "#1F1F1F"
            else:
                app_bg_color = "#FFFFFF"
            self.fig.patch.set_facecolor(app_bg_color)
            self.ax.set_facecolor(app_bg_color)

            # Check if enough data is available.
            if len(self.app.graph_times) < 2:
                print("[CalibratePage.update_graph] Not enough data to plot. Latest entries:",
                      self.app.graph_times[-5:] if self.app.graph_times else "No data")
            else:
                # Only use data from the last 30 seconds.
                current_time = self.app.graph_times[-1]
                lower_bound = current_time - 30  # Last 30 seconds

                # Filter the data arrays.
                filtered_data = [
                    (t, ip, p1, p2)
                    for t, ip, p1, p2 in zip(self.app.graph_times, self.app.graph_input_pressures,
                                             self.app.graph_pressure1s, self.app.graph_pressure2s)
                    if t >= lower_bound
                ]
                if filtered_data:
                    times, input_pressures, pressure1s, pressure2s = zip(*filtered_data)
                    self.ax.plot(times, input_pressures, label="Input Pressure")
                    self.ax.plot(times, pressure1s, label="Pressure 1")
                    self.ax.plot(times, pressure2s, label="Pressure 2")
                    if self.app.target_pressure is not None:
                        filtered_target = [
                            tp for t, tp in zip(self.app.graph_times, self.app.target_pressure) if t >= lower_bound
                        ]
                        self.ax.plot(times, filtered_target, label="Target Pressure")
                self.ax.set_ylim(0, 100)
                self.ax.set_xlabel("Time (s)")
                self.ax.set_ylabel("PSI")
                self.ax.legend()

            self.canvas.draw()
        except Exception as e:
            print(f"Error updating calibrate page graph: {e}")
        self.after(500, self.update_graph)

    def prompt_measured_pressure_before(self, target_pressure):
        """
        Displays a popup prompting the user to input a measured pressure value
        for the given target pressure BEFORE the air supply is activated.
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
        popup.wait_window()
        return result[0] if result else 0

    def start_check_calibration(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Check Calibration")
        tk.Label(popup, text="Enter Reference Pressure (max 100 psi):").pack(padx=10, pady=5)
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
            if ref_pressure > 100:
                tk.Label(popup, text="Reference pressure must be ≤ 100 psi.", fg="red").pack()
                return
            self.sensor_selected = [var.get() for var in sensor_vars]
            popup.destroy()
            threading.Thread(target=self.perform_check_calibration, args=(ref_pressure,), daemon=True).start()

        submit_btn = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_btn.pack(padx=10, pady=10)

    def perform_check_calibration(self, ref_pressure):
        # (For check calibration, we simply supply for 5 seconds and record one set of readings.)
        if self.sensor_selected[1]:
            self.app.valve1.supply()
        if self.sensor_selected[2]:
            self.app.valve2.supply()
        if self.sensor_selected[0] and not any(self.sensor_selected[1:]):
            self.app.valve1.supply()
            self.app.valve2.supply()
        print("Check Calibration: Valves activated. Recording sensor data for 5 seconds...")
        start_time = time.time()
        readings = []
        while time.time() - start_time < 5:
            time_diff = time.time() - start_time
            LPS_pressure = self.app.lps.pressure
            LPS_temperature = self.app.lps.temperature
            valve1_state = self.app.valve1.get_state()
            valve2_state = self.app.valve2.get_state()
            reading = {
                'time': time_diff,
                'LPS_pressure': LPS_pressure,
                'LPS_temperature': LPS_temperature,
                'pressure0': self.app.pressure0,
                'pressure1': self.app.pressure1,
                'pressure2': self.app.pressure2,
                'pressure3': self.app.pressure3,
                'valve1_state': valve1_state,
                'valve2_state': valve2_state,
                'Target_pressure': self.app.target_pressure,
                'Target_time': self.app.target_time,
                'clamp_state': self.app.clamp_state,
                'self_protocol_step': self.app.protocol_step
            }
            readings.append(reading)
            time.sleep(0.01)
        self.app.valve1.neutral()
        self.app.valve2.neutral()
        print("Check Calibration: Valves set to neutral.")

        base_folder = "calibration_data"
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)
            print(f"Created base folder: {base_folder}")
        calibration_folder = os.path.join(base_folder, f"calibration_{datetime.datetime.now().strftime('%Y%m%d')}")
        if not os.path.exists(calibration_folder):
            os.makedirs(calibration_folder)
            print(f"Created calibration folder: {calibration_folder}")
        csv_filename = os.path.join(
            calibration_folder,
            f"check_calibration_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        print(f"Saving check calibration data to CSV file: {csv_filename}")
        import csv
        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = list(readings[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in readings:
                writer.writerow(row)
        print("Check Calibration: Data successfully saved.")

    def start_sensor_calibration(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Calibrate Sensors (0 psi)")
        desired_pressures = [round(i * 7.25, 2) for i in range(int(100 / 7.25) + 1)]
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
        while current_pressure <= 100:
            print(f"Calibrating at target {current_pressure} psi...")
            measured_pressure = self.prompt_measured_pressure_before(current_pressure)
            print(f"User entered measured pressure: {measured_pressure} psi for target {current_pressure} psi")
            self.app.valve1.supply()
            self.app.valve2.supply()
            print("Valves activated for 5 seconds. Recording sensor data...")
            start_time = time.time()
            readings = []
            while time.time() - start_time < 5:
                time_diff = time.time() - start_time
                LPS_pressure = self.app.lps.pressure
                LPS_temperature = self.app.lps.temperature
                valve1_state = self.app.valve1.get_state()
                valve2_state = self.app.valve2.get_state()
                reading = {
                    'time': time_diff,
                    'LPS_pressure': LPS_pressure,
                    'LPS_temperature': LPS_temperature,
                    'pressure0': self.app.pressure0,
                    'pressure1': self.app.pressure1,
                    'pressure2': self.app.pressure2,
                    'pressure3': self.app.pressure3,
                    'valve1_state': valve1_state,
                    'valve2_state': valve2_state,
                    'self_target_pressure': self.app.target_pressure,
                    'self_target_time': self.app.target_time,
                    'clamp_state': self.app.clamp_state,
                    'self_protocol_step': self.app.protocol_step,
                    'Measured_pressure': measured_pressure
                }
                readings.append(reading)
                time.sleep(0.01)
            self.app.valve1.neutral()
            self.app.valve2.neutral()
            print("Valves set to neutral after 5 seconds.")

            csv_filename = os.path.join(
                calibration_folder,
                f"calibration_{measured_pressure}_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            )
            print(f"Saving calibration data for target {measured_pressure} psi to file: {csv_filename}")
            import csv
            with open(csv_filename, "w", newline="") as csvfile:
                fieldnames = list(readings[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in readings:
                    writer.writerow(row)
            print(f"Calibration data for {current_pressure} psi saved successfully.")
            current_pressure += increment

        print("Full sensor calibration complete. All data saved.")
        complete_popup = ctk.CTkToplevel(self)
        complete_popup.title("Calibration Complete")
        tk.Label(complete_popup, text="Sensor calibration is complete and all data has been saved.").pack(padx=10, pady=10)
        ctk.CTkButton(complete_popup, text="OK", command=complete_popup.destroy).pack(pady=5)

    def update_sensor_buttons(self, success_list):
        color_map = {True: "green", False: "red"}
        self.sensor1_button.configure(fg_color=color_map[success_list[0]])
        self.sensor2_button.configure(fg_color=color_map[success_list[1]])
        self.sensor3_button.configure(fg_color=color_map[success_list[2]])
