import time
import random
import os
import cv2
import numpy as np
import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set up customtkinter appearance (you can adjust the theme as needed)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GraphRecorderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calibrated Pressure Graph Recorder")
        self.geometry("800x600")

        # Data arrays (simulate sensor data updates)
        self.graph_times = []             # Time stamps in seconds
        self.graph_input_pressures = []   # Input Pressure values
        self.graph_pressure1s = []         # Pressure sensor 1 values
        self.graph_pressure2s = []         # Pressure sensor 2 values
        # For demonstration, we leave target_pressure as None
        self.target_pressure = None

        # Create a frame for the graph (mimicking your CalibratePage.graph_frame)
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Create a Matplotlib figure and axis with similar dimensions to your calibrate page
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        # Embed the figure into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")

        # Initialize the starting time for simulation & recording
        self.start_time = time.time()
        self.duration = 30  # Total recording duration in seconds
        self.update_interval_ms = 50  # Update every 50 ms (~20 FPS)

        # Force an initial draw so we know the canvas dimensions
        self.update_idletasks()
        self.fig.canvas.draw()
        width, height = self.fig.canvas.get_width_height()

        # Set up OpenCV VideoWriter to capture the canvas frames
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter('graph_video.avi', fourcc, 20, (width, height))

        # Start the update loop for both graph and recording
        self.update_graph()

    def update_graph(self):
        # Calculate elapsed time
        current_time = time.time() - self.start_time

        # When finished, release video writer and close application
        if current_time > self.duration:
            print("Recording complete. Closing application...")
            self.video_writer.release()
            self.destroy()
            return

        # -- Simulate sensor data update --
        # Append current time and simulate three pressure values (random between 20 and 80 psi)
        self.graph_times.append(current_time)
        self.graph_input_pressures.append(random.uniform(20, 80))
        self.graph_pressure1s.append(random.uniform(20, 80))
        self.graph_pressure2s.append(random.uniform(20, 80))

        # -- Redraw the graph similar to your CalibratePage.update_graph --
        self.ax.clear()
        # Set the background color based on appearance mode ("Dark" mode in this example)
        if ctk.get_appearance_mode() == "Dark":
            app_bg_color = "#1F1F1F"
            text_bg_color = "white"
        else:
            app_bg_color = "#FFFFFF"
            text_bg_color = "black"

        self.fig.patch.set_facecolor(app_bg_color)
        self.ax.set_facecolor(app_bg_color)

        # Set title and axis labels with the same styling
        self.ax.set_title("Calibrated Pressure Sensor Values", color=text_bg_color)
        self.ax.set_xlabel("Time (s)", color=text_bg_color)
        self.ax.set_ylabel("PSI", color=text_bg_color)
        self.ax.tick_params(axis='x', colors=text_bg_color, labelcolor=text_bg_color)
        self.ax.tick_params(axis='y', colors=text_bg_color, labelcolor=text_bg_color)
        # Set spines' colors
        for spine in self.ax.spines.values():
            spine.set_color(text_bg_color)

        # Only plot if at least two data points exist
        if len(self.graph_times) >= 2:
            # Only use data from the last 30 seconds.
            lower_bound = current_time - 30
            filtered = [
                (t, ip, p1, p2)
                for t, ip, p1, p2 in zip(self.graph_times,
                                          self.graph_input_pressures,
                                          self.graph_pressure1s,
                                          self.graph_pressure2s)
                if t >= lower_bound
            ]
            if filtered:
                times, input_pressures, pressure1s, pressure2s = zip(*filtered)
                self.ax.plot(times, input_pressures, label="Input Pressure", zorder=3)
                self.ax.plot(times, pressure1s, label="Pressure 1", zorder=3)
                self.ax.plot(times, pressure2s, label="Pressure 2", zorder=3)
                # If target_pressure is available, plot it.
                if self.target_pressure is not None:
                    # Here we simulate target pressure as a constant (if desired)
                    target = [self.target_pressure for _ in times]
                    self.ax.plot(times, target, label="Target Pressure", zorder=3)
            self.ax.set_ylim(0, 100)
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("PSI")
            self.ax.legend()

        # Redraw the canvas
        self.canvas.draw()

        # -- Capture the current frame from the figure canvas --
        # Use print_to_buffer() to get the RGBA buffer and dimensions.
        buffer, (width, height) = self.fig.canvas.print_to_buffer()
        # Convert the buffer (which has 4 channels: RGBA) to a NumPy array and drop the alpha channel.
        img = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))[:, :, :3]
        # Convert RGB to BGR for OpenCV.
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        # Write the frame to the video
        self.video_writer.write(img)

        # Schedule the next update.
        self.after(self.update_interval_ms, self.update_graph)

if __name__ == "__main__":
    app = GraphRecorderApp()
    app.mainloop()
