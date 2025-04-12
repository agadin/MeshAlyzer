#!/usr/bin/env python3
import time
import threading
import cv2
import numpy as np
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Attempt to import your sensor module.
try:
    from PressureSensorReader import PressureReceiver
except ImportError:
    print("PressureSensorReader not found. Sensor values will be simulated.")
    PressureReceiver = None
    import random


class GraphRecorderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calibrated Pressure Graph Recorder")
        self.geometry("800x600")

        # Arrays to store actual sensor data
        self.graph_times = []  # Time stamps (seconds)
        self.graph_input_pressures = []  # For example, sensor 0 values (actual pressure0_convert)
        self.graph_pressure1s = []  # Sensor 1 values
        self.graph_pressure2s = []  # Sensor 2 values
        self.target_pressure = None  # Use if available

        # Record the starting time
        self.start_time = time.time()

        # Create a frame to hold the graph; style similar to your CalibratePage.
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Create a Matplotlib figure and axis
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")

        # Force the Tk window to render so we can get exact canvas dimensions
        self.update_idletasks()
        self.fig.canvas.draw()
        width, height = self.fig.canvas.get_width_height()

        # Set up OpenCV VideoWriter (recording at 20 fps)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter('graph_video.avi', fourcc, 20, (width, height))

        # Start a background thread to update sensor values using actual (or simulated) readings
        threading.Thread(target=self.read_sensors, daemon=True).start()
        # Start the graph update loop (which also records each frame)
        self.update_graph()

    def read_sensors(self):
        """
        Repeatedly read sensor values and append them to the data arrays.
        In your MeshAlyzer app, these values are updated in real time.
        """
        while True:
            current_elapsed = time.time() - self.start_time
            if PressureReceiver is not None:
                try:
                    # Read actual sensor values (expecting at least 3 values)
                    pressures = PressureReceiver.getpressures()
                    if pressures and len(pressures) >= 3:
                        # Here you could apply calibration conversion if needed.
                        # For example, if your app uses self.pressure0_convert, etc.,
                        # you can insert that conversion function here.
                        pressure0, pressure1, pressure2, _ = pressures
                    else:
                        continue
                except Exception as e:
                    print("Sensor reading error:", e)
                    continue
            else:
                # Fall back to simulation if sensor reading fails.
                pressure0 = np.random.uniform(20, 80)
                pressure1 = np.random.uniform(20, 80)
                pressure2 = np.random.uniform(20, 80)

            self.graph_times.append(current_elapsed)
            self.graph_input_pressures.append(pressure0)
            self.graph_pressure1s.append(pressure1)
            self.graph_pressure2s.append(pressure2)
            time.sleep(0.1)  # Adjust the polling rate as necessary

    def update_graph(self):
        """
        Redraw the graph using the actual sensor data in the arrays and capture the frame.
        The graph appearance mirrors your CalibratePage.update_graph implementation.
        """
        elapsed = time.time() - self.start_time
        if elapsed > 30:
            print("Recording complete. Closing application...")
            self.video_writer.release()
            self.destroy()
            return

        self.ax.clear()

        # Set background and text colors per appearance mode (Dark mode used here)
        if ctk.get_appearance_mode() == "Dark":
            app_bg_color = "#1F1F1F"
            text_color = "white"
        else:
            app_bg_color = "#FFFFFF"
            text_color = "black"

        self.fig.patch.set_facecolor(app_bg_color)
        self.ax.set_facecolor(app_bg_color)
        self.ax.set_title("Calibrated Pressure Sensor Values", color=text_color)
        self.ax.set_xlabel("Time (s)", color=text_color)
        self.ax.set_ylabel("PSI", color=text_color)
        self.ax.tick_params(axis='x', colors=text_color, labelcolor=text_color)
        self.ax.tick_params(axis='y', colors=text_color, labelcolor=text_color)
        for spine in self.ax.spines.values():
            spine.set_color(text_color)

        # Only plot if there is at least some sensor data.
        if len(self.graph_times) >= 2:
            lower_bound = elapsed - 30  # Plot only the last 30 seconds
            filtered_data = [
                (t, ip, p1, p2)
                for t, ip, p1, p2 in zip(self.graph_times,
                                         self.graph_input_pressures,
                                         self.graph_pressure1s,
                                         self.graph_pressure2s)
                if t >= lower_bound
            ]
            if filtered_data:
                times, input_pressures, pressure1s, pressure2s = zip(*filtered_data)
                self.ax.plot(times, input_pressures, label="Input Pressure", zorder=3)
                self.ax.plot(times, pressure1s, label="Pressure 1", zorder=3)
                self.ax.plot(times, pressure2s, label="Pressure 2", zorder=3)
                # If you use a target_pressure value, you can plot it here.
                if self.target_pressure is not None:
                    target_line = [self.target_pressure for _ in times]
                    self.ax.plot(times, target_line, label="Target Pressure", zorder=3)
            self.ax.set_ylim(0, 100)
            self.ax.legend()

        self.canvas.draw()

        # Capture the current canvas image via print_to_buffer (returns an RGBA buffer)
        buffer, (width, height) = self.fig.canvas.print_to_buffer()
        img = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))[:, :, :3]  # Remove alpha
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
        self.video_writer.write(img)

        # Schedule the next update call
        self.after(50, self.update_graph)


if __name__ == "__main__":
    app = GraphRecorderApp()
    app.mainloop()
