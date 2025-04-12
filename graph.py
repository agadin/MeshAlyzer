import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2
import numpy as np
import time
import random


class VideoRecorderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Graph Recorder")
        self.start_time = time.time()
        self.duration = 30  # seconds to record
        self.fps = 20  # frames per second
        self.interval = int(1000 / self.fps)  # interval in milliseconds

        # Create a Matplotlib figure for the graph
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Live Graph (Simulated)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")
        self.ax.set_xlim(0, self.duration)
        self.ax.set_ylim(0, 10)

        # Initialize data storage and plot line
        self.x_data = []
        self.y_data = []
        self.line, = self.ax.plot([], [], lw=2)

        # Embed the figure in a Tkinter Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()

        # Update the Tk window to ensure canvas dimensions are set
        self.master.update_idletasks()
        self.fig.canvas.draw()
        width, height = self.fig.canvas.get_width_height()

        # Set up the OpenCV VideoWriter to record the figure frames
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('graph_video.avi', fourcc, self.fps, (width, height))

        # Start the update and recording loop
        self.update_plot()

    def update_plot(self):
        """Update the graph, capture the current frame, and write it to the video file."""
        current_time = time.time() - self.start_time
        if current_time > self.duration:
            # Stop recording after 30 seconds
            print("Recording complete.")
            self.out.release()
            self.master.destroy()
            return

        # Append a new data point (simulate live data with a random value)
        self.x_data.append(current_time)
        self.y_data.append(random.uniform(0, 10))
        self.line.set_data(self.x_data, self.y_data)
        # Optionally update the x-axis limit dynamically
        self.ax.set_xlim(0, max(self.duration, current_time + 1))
        self.canvas.draw()

        # Capture the canvas as an RGB image from the figure's buffer
        width, height = self.fig.canvas.get_width_height()
        img = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape((height, width, 3))
        # Convert from RGB to BGR (OpenCV format)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Write the frame to the video file
        self.out.write(img)

        # Schedule the next update call
        self.master.after(self.interval, self.update_plot)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoRecorderApp(root)
    root.mainloop()
