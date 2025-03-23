# --- New CalibratePage class ---
import customtkinter as ctk

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
        # For visual feedback, change relief or border width (or color) when selected:
        if self.sensor_selected[sensor_index]:
            new_color = "darkgray"  # slightly different shade when selected
        else:
            new_color = "gray"
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
        # Extract time and pressure_convert values
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
        # Update graph every 1 second
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

            # Update sensor selection based on popup checkboxes.
            self.sensor_selected = [var.get() for var in sensor_vars]
            popup.destroy()
            # Run calibration check in a separate thread to avoid blocking UI.
            threading.Thread(target=self.perform_check_calibration, args=(ref_pressure,), daemon=True).start()

        submit_btn = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_btn.pack(padx=10, pady=10)

    def perform_check_calibration(self, ref_pressure):
        """
        Perform the calibration check process:
        - Depending on sensor selection, call valve supply methods.
        - Activate for 1 second max, then vent for 1.5 seconds.
        - Repeat 5 times and record sensor values from pressure0, pressure1, pressure2.
        - Convert the recorded values.
        - Compare against ref_pressure (+/- 5% tolerance).
        - Update sensor button colors accordingly.
        """
        # This is a placeholder implementation.
        success = [False, False, False]  # flags for sensor 1,2,3

        # For demonstration, we simulate 5 cycles with a simple sleep.
        recorded_values = {0: [], 1: [], 2: []}
        for cycle in range(5):
            # Determine which valves to supply based on sensor selection.
            # If sensor 2 selected, call valve1.supply; if sensor 3 selected, call valve2.supply.
            # If only sensor 1 is selected, call both.
            if self.sensor_selected[1]:
                self.app.valve1.supply()
            if self.sensor_selected[2]:
                self.app.valve2.supply()
            if (self.sensor_selected[0] and not any(self.sensor_selected[1:])):
                self.app.valve1.supply()
                self.app.valve2.supply()
            time.sleep(1)  # Supply period

            # After supply period, start venting.
            self.app.valve1.vent()
            self.app.valve2.vent()
            time.sleep(1.5)  # Vent period

            # Record the current sensor values (using the pressure_sensor_converter as-is)
            rec = self.app.sensor_data[-1]  # get the latest sensor reading
            # Record only for pressure0, pressure1, pressure2
            recorded_values[0].append(rec.get('pressure0_convert', 0))
            recorded_values[1].append(rec.get('pressure1_convert', 0))
            recorded_values[2].append(rec.get('pressure2_convert', 0))

        # Process recorded values (here we simply compute the average for each sensor)
        avg_values = [sum(vals) / len(vals) if vals else 0 for vals in recorded_values.values()]

        # Compare each average value with ref_pressure (+/- 5% tolerance)
        tolerance = 0.05
        for i, avg in enumerate(avg_values):
            if ref_pressure != 0 and abs(avg - ref_pressure) / ref_pressure <= tolerance:
                success[i] = True
            else:
                success[i] = False

        # Update button colors based on calibration success:
        self.update_sensor_buttons(success)

    def update_sensor_buttons(self, success_list):
        # success_list: list of booleans for sensor 1, 2, 3
        # Set color to green if True, else red.
        color_map = {True: "green", False: "red"}
        self.sensor1_button.configure(fg_color=color_map[success_list[0]])
        self.sensor2_button.configure(fg_color=color_map[success_list[1]])
        self.sensor3_button.configure(fg_color=color_map[success_list[2]])

    def start_sensor_calibration(self):
        """
        Start the full sensor calibration process:
         - Prompt the user for a reference pressure of 0 psi.
         - Then, for pressures from 0 to 145 psi in increments of 7.25 psi,
           perform the supply/vent cycle, record sensor data and save to CSV.
         - (Placeholder implementation provided.)
        """
        popup = ctk.CTkToplevel(self)
        popup.title("Calibrate Sensors (0 psi)")

        tk.Label(popup, text="Enter Reference Pressure (should be 0 psi):").pack(padx=10, pady=5)
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
          - Activate supply for 1 second (both valves), then vent for 1.5 seconds.
          - Repeat 5 times and record sensor data from pressure0, pressure1, pressure2.
          - Save the recorded data to a CSV file in a folder named with the calibration date.
        This placeholder should be expanded to include the full calibration loop.
        """
        current_pressure = 0
        increment = 7.25
        calibration_results = []  # list to store calibration data for each step

        while current_pressure <= 145:
            recorded_values = {0: [], 1: [], 2: []}
            for cycle in range(5):
                # Activate both valves supply
                self.app.valve1.supply()
                self.app.valve2.supply()
                time.sleep(1)
                self.app.valve1.vent()
                self.app.valve2.vent()
                time.sleep(1.5)
                rec = self.app.sensor_data[-1]
                recorded_values[0].append(rec.get('pressure0_convert', 0))
                recorded_values[1].append(rec.get('pressure1_convert', 0))
                recorded_values[2].append(rec.get('pressure2_convert', 0))
            # Compute averages for this step
            avg_values = [sum(vals) / len(vals) if vals else 0 for vals in recorded_values.values()]
            calibration_results.append({
                "reference_pressure": current_pressure,
                "avg_pressure0_convert": avg_values[0],
                "avg_pressure1_convert": avg_values[1],
                "avg_pressure2_convert": avg_values[2]
            })
            # Here you may decide to update the UI or log the results.
            current_pressure += increment

        # Save calibration_results to CSV in a folder (e.g., calibration_<date>/raw_<timestamp>_0_psi_calibration.csv)
        calibration_folder = f"calibration_{datetime.datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(calibration_folder):
            os.makedirs(calibration_folder)
        csv_filename = os.path.join(calibration_folder,
                                    f"raw_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_0_psi_calibration.csv")
        import csv
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                "reference_pressure", "avg_pressure0_convert", "avg_pressure1_convert", "avg_pressure2_convert"
            ])
            writer.writeheader()
            for row in calibration_results:
                writer.writerow(row)
        # Optionally, display a popup to indicate calibration is complete.
        complete_popup = ctk.CTkToplevel(self)
        complete_popup.title("Calibration Complete")
        tk.Label(complete_popup, text="Sensor calibration is complete and data has been saved.").pack(padx=10, pady=10)
        ctk.CTkButton(complete_popup, text="OK", command=complete_popup.destroy).pack(pady=5)
