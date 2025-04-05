import shutil
import customtkinter as ctk
import multiprocessing.shared_memory as sm
from tkinter import Canvas, Frame, Scrollbar, filedialog
from PIL import Image, ImageTk, ImageOps
import webbrowser
import subprocess


from tkinter import StringVar
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
import queue
import traceback
import threading
import sys
import os
import filecmp
import threading
import cairosvg
import xml.etree.ElementTree as ET
from tkinter import messagebox
from PIL import Image, ImageTk


# lps22
import board
import busio
import adafruit_lps2x
import warnings
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names, but StandardScaler was fitted with feature names",
    category=UserWarning
)
import numpy as np
# Sensor import
from PressureSensorReader import PressureReceiver
from ValveController import ValveController
from clamp_motor import MotorController
from calibrate_page import CalibratePage
from valve_control_dropdown import ValveControlDropdown
from joblib import load
from calibrating_pressure_transducers.getCalibrationData import PressureCalibrator
from settings_page import SettingsPage

class ProtocolViewer(ctk.CTkFrame):
    def __init__(self, master, protocol_folder, protocol_var, app, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.app = app
        self.protocol_folder = protocol_folder
        self.protocol_var = protocol_var

        self.protocol_steps = []  # List of parsed protocol steps
        self.step_widgets = []  # References to step widgets for updating
        # opacity

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=400, height=800)
        self.scrollable_frame.pack(fill="both", expand=True)

        # Dynamically update current step opacity
        self.update_current_step()

    def load_protocol(self, protocol_var):
        # Clear existing steps
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.step_widgets = []
        self.protocol_steps = []
        print("Loading protocolh:", protocol_var)
        # Get the protocol path
        protocol_path = os.path.join(self.protocol_folder, protocol_var)

        # Read and parse the protocol
        if os.path.exists(protocol_path):
            with open(protocol_path, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                step_num = i + 1
                step_details = self.parse_step(line.strip())
                self.protocol_steps.append((step_num, *step_details))
                self.create_step_widget(step_num, *step_details)

    def parse_step(self, line):
        """Parse a protocol step from the line."""
        if ":" in line:
            step_name, details = line.split(":", 1)
        else:
            step_name, details = line, ""
        return step_name, details.strip()

    def create_step_widget(self, step_num, step_name, details):
        """Create a rounded box for a protocol step."""
        frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        frame.pack(fill="x", padx=5, pady=5)

        # Step number
        step_num_label = ctk.CTkLabel(frame, text=f"Step {step_num}", width=10)
        step_num_label.grid(row=0, column=0, padx=5, pady=5)

        # Step name and details
        step_name_label = ctk.CTkLabel(frame, text=f"{step_name}: {details}", anchor="w")
        step_name_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Checkbox
        checkbox_var = ctk.BooleanVar(value=True)
        checkbox = ctk.CTkCheckBox(
            frame,
            text="",
            variable=checkbox_var
        )
        # TODO: Add a command for there to be an effect with the check box
        checkbox.grid(row=0, column=2, padx=5, pady=5)

        self.step_widgets.append((frame, step_num))

    def update_current_step(self):
        """Update opacity dynamically based on the current step."""
        try:
            current_step = self.app.protocol_step
            current_step = int(current_step) if current_step else None
        except (ValueError, TypeError):
            current_step = None

        # Update frame background color to simulate opacity
        for frame, step_num in self.step_widgets:
            if current_step == step_num:
                frame.configure(fg_color="lightblue")  # Simulate higher opacity
            else:
                frame.configure(fg_color="lightgray")  # Simulate lower opacity

        self.after(500, self.update_current_step)  # Check every 500ms

def read_settings():
    settings = {}
    if os.path.exists("settings.txt"):
        with open("settings.txt", "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    settings[key.strip()] = value.strip()
    return settings


def load_default_settings(app=None):
    """
    Copies default_settings.txt to settings.txt and, if an app instance is provided,
    updates the app's settings attributes with the defaults.
    """
    try:
        shutil.copy("default_settings.txt", "settings.txt")
        print("Default settings loaded.")
        # Read the defaults from the settings file
        default_settings = read_settings()
        if app is not None:
            # Update boolean setting (convert string to bool)
            app.no_cap = default_settings.get("no_cap", "False").lower() in ("true", "1", "yes")
            # Update tuple setting (using eval to convert string to tuple)
            try:
                app.graph_y_range = eval(default_settings.get("graph_y_range", str(app.graph_y_range)))
            except Exception as e:
                print("Error evaluating graph_y_range:", e)
            # Update integer setting
            try:
                app.graph_time_range = int(default_settings.get("graph_time_range", app.graph_time_range))
            except Exception as e:
                print("Error parsing graph_time_range:", e)
            # Update string setting
            app.accent_color = default_settings.get("accent_color", app.accent_color)
            print("App settings updated with defaults.")
    except Exception as e:
        print("Error copying default settings:", e)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()  # Initialize the parent class
        self.splash_canvas = None
        self.graph_y_range = None
        self.no_cap = None
        self.init = None
        self.graph_frame = None
        self.sampleID = None
        self.running = True  # Initialize the running attribute
        self.stop_flag = False  # Initialize the stop flag
        self.distance_left = 0.0
        self.distance_right = 0.0
        self.selected_motor = "both"
        self.graph_time_range = 30  # Default time range in seconds (can be set to 15 or 60 as needed)
        ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
        self.accent_color = "blue"  # Light blue color
        # set default color theme
        ctk.set_default_color_theme(self.accent_color)

        load_default_settings(self)
        icon_path = os.path.abspath('./img/ratfav.ico')
        png_icon_path = os.path.abspath('./img/ratfav.png')
        try:
            img = Image.open(icon_path)
            img.save(png_icon_path)
            self.icon_img = ImageTk.PhotoImage(file=png_icon_path)
            self.iconphoto(False, self.icon_img)

        except Exception as e:
            print(f"Failed to set icon: {e}")

        self.show_boot_animation()

        # Window configuration
        self.title("MeshAlyzer")
        self.resizable(False, False)
        # Calculate the center of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (1800 // 2)
        y_coordinate = (screen_height // 2) - (920 // 2)

        self.geometry(f"1800x920+{x_coordinate}+{y_coordinate}")

        # Protocol Handling dictionary inti
        self.data_dict = {}
        self.protocol_step = None
        self.target_pressure = None
        self.protocol_command = None
        self.target_time = None
        self.protocol_running = False  # Flag to indicate if the protocol is running
        self.total_steps = 0
        self.moving_steps_total = 0
        self.graph_times = []
        self.graph_input_pressures = []
        self.graph_pressure1s = []
        self.graph_pressure2s = []

        # Initialize PressureReceiver
        self.pressure_receiver = PressureReceiver()
        self.pressure_thread = threading.Thread(target=self.pressure_receiver.run, daemon=True)
        self.pressure_thread.start()

        ## clamp state
        self.clamp_state = None
        self.clamp_state = False  # or True, depending on your system

        # --------------------------
        # input/output init
        # --------------------------

        self.valve1 = ValveController(supply_pins=[20], vent_pins=[27])
        self.valve2 = ValveController(supply_pins=[12], vent_pins=[24])
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.lps = adafruit_lps2x.LPS22(self.i2c)
        # self.lps.pressure
        # self.lps.temperature

        # --------------------------
        # Top Navigation Bar Section
        # --------------------------

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=5)

        # Left frame for the logo
        self.nav_left_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.nav_left_frame.pack(side="left")

        # Right frame for nav buttons
        self.nav_right_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.nav_right_frame.pack(side="right", padx=20)

        # --- Logo on Left Side ---
        # Create a white icon from the SVG file
        icon_size = (20, 20)

        # Create CTkImage for the first logo (lake logo)
        logo_image = ctk.CTkImage(
            light_image=Image.open("./img/lakelogo_dark.png"),  # For light mode
            dark_image=Image.open("./img/lakelogo.png"),  # For dark mode
            size=(60, 60)
        )

        # Create the first CTkButton with the lake logo
        self.logo_button = ctk.CTkButton(
            self.nav_left_frame,
            image=logo_image,
            text="",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_home
        )
        self.logo_button.pack(side="left", padx=1)

        high_res_mesh_logo_dark = Image.open("./img/meshlogo_dark.png")
        high_res_mesh_logo = Image.open("./img/meshlogo.png")

        # Resize it to the target dimensions using a high-quality filter
        high_res_mesh_logo_dark = high_res_mesh_logo_dark.resize((80, 60), Image.LANCZOS)
        resized_mesh_logo = high_res_mesh_logo.resize((80, 60), Image.LANCZOS)

        # Create CTkImage for the second logo (mesh logo)
        mesh_logo_image = ctk.CTkImage(
            light_image=high_res_mesh_logo_dark,  # Use same image for both modes, or adjust if needed
            dark_image=resized_mesh_logo,
            size=(80, 60)
        )

        # Create a second CTkButton with the mesh logo
        self.mesh_logo_button = ctk.CTkButton(
            self.nav_left_frame,
            image=mesh_logo_image,
            text="",
            hover_color="gray",
            fg_color="transparent",
            command=self.open_twitter  # Updated command
        )
        self.mesh_logo_button.pack(side="left", padx=1)

        # Load the PNG images
        home_icon_image = Image.open("./img/fa-home.png")
        protocol_icon_image = Image.open("./img/fa-tools.png")
        calibrate_icon_image = Image.open("./img/fa-tachometer-alt.png")
        settings_icon_image = Image.open("./img/fa-cog.png")

        # Create CTkImage objects
        home_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-home_dark.png"),
            dark_image=Image.open("./img/fa-home.png"),
            size=(20, 20)
        )

        protocol_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-tools_dark.png"),
            dark_image=Image.open("./img/fa-tools.png"),
            size=(20, 20)
        )

        calibrate_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-tachometer-alt_dark.png"),
            dark_image=Image.open("./img/fa-tachometer-alt.png"),
            size=(20, 20)
        )

        settings_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-cog_dark.png"),
            dark_image=Image.open("./img/fa-cog.png"),
            size=(20, 20)
        )

        # --- Navigation Buttons on Right Side ---
        self.settings_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Settings",
            text_color="white",
            image=settings_icon,
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_settings
        )
        self.settings_button.pack(side="right", padx=20)

        self.inspector_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Calibrate",
            text_color="white",
            image=calibrate_icon,
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_calibrate
        )
        self.inspector_button.pack(side="right", padx=20)

        self.protocol_builder_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Protocol Builder",
            image=protocol_icon,
            text_color="white",
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_protocol_builder
        )
        self.protocol_builder_button.pack(side="right", padx=20)

        self.home_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Home",
            image=home_icon,
            text_color="white",
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_home
        )
        self.home_button.pack(side="right", padx=20)

        # --------------------------
        # Main Content Frame
        # --------------------------
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", pady=10)

        self.home_frame = None
        self.protocol_builder_frame = None
        self.inspector_frame = None
        self.settings_frame = None

        # set up readvalues
        self.sensor_data = []
        self.calibrator = PressureCalibrator()
        self.calibrator.models = load('calibrating_pressure_transducers/trained_pressure_calibrator_multioutput.joblib')

        # Start the sensor reading in a separate daemon thread
        self.update_queue = queue.Queue()
        self.sensor_thread = threading.Thread(target=self.read_sensors, daemon=True)
        self.sensor_thread.start()
        self.process_queue()

        ## apperance defults
        self.darkmodeToggle = False

        if self.darkmodeToggle:
            # Light/dark mode automatic toggle
            current_hour = datetime.datetime.now().hour
            default_mode = "Dark" if current_hour >= 18 or current_hour < 6 else "Light"
            ctk.set_appearance_mode(default_mode)
        else:
            ctk.set_appearance_mode("Dark")

        # clampmotor setup
        try:
            self.motor_controller = MotorController(port="/dev/ttyACM0", baudrate=9600)
        except Exception as e:
            print(f"Failed to initialize MotorController: {e}")

        # Variables to track button hold state
        self.motor_forward_pressed = False
        self.motor_forward_active = False
        self.motor_reverse_pressed = False
        self.motor_reverse_active = False

        # Initialize the home display
        self.show_home()

    def show_boot_animation(self):
        # Remove title bar for splash screen effect
        video_thread = threading.Thread(target=self.play_video_thread, daemon=True)
        video_thread.start()

        self.overrideredirect(True)

        # Set the desired window size (720p video dimensions)
        window_width = 854
        window_height = 480

        # Calculate the center of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (window_width // 2)
        y_coordinate = (screen_height // 2) - (window_height // 2)

        # Position the window at the center of the screen
        self.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Create a canvas for video and text overlay
        canvas = Canvas(self, bg="black", highlightthickness=0)
        canvas.pack(expand=True, fill="both")

        # Variable for overlay text
        setup_status = StringVar()
        setup_status.set("")

        # Function to play video
        def play_video():
            video_path = "./img/MeshAlyzer_.mp4"
            video = cv2.VideoCapture(video_path)

            setup_steps = [
                ("", 4),
                ("", 2),
                ("", 4),
                ("", 6),
            ]

            current_step_index = 0
            next_step_time = setup_steps[current_step_index][1]
            start_time = time.time()

            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break

                # Convert frame to ImageTk format
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image = ImageTk.PhotoImage(image)

                # Display video frame on the canvas
                canvas.create_image(0, 0, anchor="nw", image=image)
                canvas.image = image  # Keep a reference to avoid garbage collection

                # Update overlay text based on time
                elapsed_time = time.time() - start_time
                if current_step_index < len(setup_steps) and elapsed_time >= next_step_time:
                    setup_status.set(setup_steps[current_step_index][0])
                    current_step_index += 1
                    if current_step_index < len(setup_steps):
                        next_step_time = elapsed_time + setup_steps[current_step_index][1]

                # Overlay text on the canvas
                canvas.delete("text")
                canvas.create_text(
                    canvas.winfo_width() // 2,
                    (canvas.winfo_height() // 2) - 50,
                    text=setup_status.get(),
                    font=("Arial", 24),
                    fill="white",
                    tags="text",
                )

                self.update()
                time.sleep(1 / video.get(cv2.CAP_PROP_FPS))

            video.release()
            canvas.destroy()

        # Start the video playback
        play_video()
        self.overrideredirect(False)

    def show_error_dialog(self, title, message):
        """Display a user-friendly error dialog."""
        messagebox.showerror(title, message)

    def update_splash_canvas(self, photo):
        """Update the splash canvas with the new video frame."""
        self.splash_canvas.create_image(0, 0, anchor="nw", image=photo)
        # Keep a reference to avoid garbage collection
        self.splash_canvas.image = photo

    def update_splash_image(self, pil_image):
        """
        This method runs on the main thread.
        It converts the PIL image to a PhotoImage and updates the canvas.
        """
        try:
            photo = ImageTk.PhotoImage(pil_image)
            self.splash_canvas.create_image(0, 0, anchor="nw", image=photo)
            # Keep a reference to avoid garbage collection.
            self.splash_canvas.image = photo
        except Exception as e:
            self.show_error_dialog("Image Error", f"Failed to update image: {e}")

    def play_video_thread(self):
        """Run video playback in a separate thread to keep the UI responsive."""
        video_path = "./img/MeshAlyzer_.mp4"
        if not os.path.exists(video_path):
            self.after(0, lambda: self.show_error_dialog("Video Error", f"Video file not found:\n{video_path}"))
            return

        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            self.after(0, lambda: self.show_error_dialog("Video Error", "Unable to open video file."))
            return

        fps = video.get(cv2.CAP_PROP_FPS)
        fps = fps if fps > 0 else 25  # Fallback if FPS is not available
        delay = 1.0 / fps

        while video.isOpened():
            ret, frame = video.read()
            if not ret:
                break

            # Convert the frame to RGB and then to a PIL Image.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # Schedule the update of the canvas on the main thread.
            self.after(0, self.update_splash_image, pil_image)
            time.sleep(delay)

        video.release()
        # After video ends, schedule removal of the splash canvas.
        self.after(0, self.splash_canvas.destroy)


    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def open_twitter(self):
        """
        Opens the MeshToTheMax Twitter page in Chromium.
        """
        try:
            subprocess.Popen(["chromium-browser", "https://x.com/MeshToTheMax"])
        except Exception as e:
            print("Failed to open Chromium browser:", e)

    def update_pressure_values(self):
        pressure0, pressure1, pressure2, pressure3 = PressureReceiver.getpressures()
        self.pressure0 = pressure0
        self.pressure1 = pressure1
        self.pressure2 = pressure2
        self.pressure3 = pressure3

    def show_home(self):
        self.clear_content_frame()
        self.home_displayed = True
        self.update_app_settings()

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=300)
        self.sidebar_frame.pack(side="left", fill="y", padx=15)

        # Calibrate button
        self.calibrate_button = ctk.CTkButton(self.sidebar_frame, text="Calibrate", command=self.show_calibrate)
        self.calibrate_button.pack(pady=15, padx=15)

        # Protocol selector
        self.protocol_label = ctk.CTkLabel(self.sidebar_frame, text="Select a Protocol:")
        self.protocol_label.pack(pady=15, padx=15)

        self.protocol_folder = './protocols'
        self.protocol_files = [f for f in os.listdir(self.protocol_folder) if
                               os.path.isfile(os.path.join(self.protocol_folder, f))]
        self.protocol_var = ctk.StringVar(value=self.protocol_files[0])

        self.protocol_dropdown = ctk.CTkComboBox(self.sidebar_frame, values=self.protocol_files,
                                                 variable=self.protocol_var)
        self.protocol_dropdown.pack(pady=15)

        self.run_button = ctk.CTkButton(self.sidebar_frame, text="Run Protocol", command=self.run_protocol)
        self.run_button.pack(pady=15)

        # Add Stop Protocol button to the sidebar
        self.stop_protocol_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Stop Protocol",
            command=self.stop_protocol
        )
        self.stop_protocol_button.pack(pady=5)



        # Motor buttons frame
        motor_button_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        motor_button_frame.pack(pady=10)

        # --- New: Segmented Button for Motor Control ---
        self.motor_segmented_button = ctk.CTkSegmentedButton(
            self.sidebar_frame,
            values=["Left", "Both", "Right"],
            command=self.set_motor_control
        )
        self.motor_segmented_button.set("Both")  # Default to Both (middle option)
        self.motor_segmented_button.pack(pady=5)

        # --- New: Reset Buttons in Sidebar ---
        self.reset_left_button_sidebar = ctk.CTkButton(
            self.sidebar_frame, text="Reset Left Distance", command=self.reset_left_distance
        )
        self.reset_left_button_sidebar.pack(pady=5)

        self.reset_right_button_sidebar = ctk.CTkButton(
            self.sidebar_frame, text="Reset Right Distance", command=self.reset_right_distance
        )
        self.reset_right_button_sidebar.pack(pady=5)


        self.motor_forward_button = ctk.CTkButton(motor_button_frame, text="Advance Motor", fg_color="transparent")
        self.motor_forward_button.pack(side="left", padx=5)
        self.motor_forward_button.bind("<ButtonPress-1>", self.start_motor_forward)
        self.motor_forward_button.bind("<ButtonRelease-1>", self.stop_motor_forward)

        self.motor_reverse_button = ctk.CTkButton(motor_button_frame, text="Reverse Motor", fg_color="transparent")
        self.motor_reverse_button.pack(side="left", padx=5)
        self.motor_reverse_button.bind("<ButtonPress-1>", self.start_motor_reverse)
        self.motor_reverse_button.bind("<ButtonRelease-1>", self.stop_motor_reverse)

        # Light/Dark mode toggle
        self.mode_toggle = ctk.CTkSwitch(self.sidebar_frame, text="Dark/Light Mode", command=self.toggle_mode)
        self.mode_toggle.pack(pady=15)

        self.lps_info_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="LPS: N/A | N/A",
            text_color="darkgrey",
            font=("Arial", 10)
        )
        self.lps_info_label.pack(side="bottom", pady=10, padx=10)

        # add status lights below lps_info_label
        # Container frame for status boxes
        self.status_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.status_frame.pack(side="bottom", pady=10, padx=10)

        # RPI Box – will check PressureReceiver status
        self.rpi_box = ctk.CTkFrame(self.status_frame, width=80, height=40, corner_radius=10, fg_color="gray")
        self.rpi_box.grid(row=0, column=0, padx=5)
        self.rpi_label = ctk.CTkLabel(self.rpi_box, text="RPI", font=("Arial", 10, "bold"))
        self.rpi_label.place(relx=0.5, rely=0.5, anchor="center")

        # UNO Box – will check self.motor_controller status
        self.uno_box = ctk.CTkFrame(self.status_frame, width=80, height=40, corner_radius=10, fg_color="gray")
        self.uno_box.grid(row=0, column=1, padx=5)
        self.uno_label = ctk.CTkLabel(self.uno_box, text="UNO", font=("Arial", 10, "bold"))
        self.uno_label.place(relx=0.5, rely=0.5, anchor="center")

        # BLK Box – dummy for now
        self.blk_box = ctk.CTkFrame(self.status_frame, width=80, height=40, corner_radius=10, fg_color="gray")
        self.blk_box.grid(row=0, column=2, padx=5)
        self.blk_label = ctk.CTkLabel(self.blk_box, text="BLK", font=("Arial", 10, "bold"))
        self.blk_label.place(relx=0.5, rely=0.5, anchor="center")


        # Valve control dropdown
        self.valve_control = ValveControlDropdown(
            self.sidebar_frame,
            get_pressures_func=lambda: {
                "pressure0": self.pressure0_convert,
                "pressure1": self.pressure1_convert,
                "pressure2": self.pressure2_convert,
            },
            on_vent=lambda: (self.valve1.vent(), self.valve2.vent()),
            on_neutral=lambda: (self.valve1.neutral(), self.valve2.neutral()),
            on_supply=lambda: (self.valve1.supply(), self.valve2.supply())
        )
        self.valve_control.pack(pady=10)

        # add a input box in the side frame that says sample ID and have that set to self.sampleID
        self.sample_id_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Sample ID")
        self.sample_id_entry.pack(pady=15, padx=15)
        self.sample_id_entry.bind("<FocusOut>", self.update_sample_id)



        # Main content area
        self.main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_frame.pack(side="left", expand=True, fill="both", padx=10)

        self.protocol_name_label = ctk.CTkLabel(self.main_frame, text="Current Protocol: None", anchor="w",
                                                font=("Arial", 35, "bold"))
        self.protocol_name_label.pack(pady=10, padx=20, anchor="w")



        display_style = {
            "width": 200,
            "height": 100,
            "corner_radius": 20,
            "fg_color": "lightblue",
            "text_color": "black",
            "font": ("Arial", 45, "bold"),
        }
        # === Main Display Section ===
        display_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        display_container.pack(pady=20)

        # === Top Section: Sensor Metrics ===
        sensor_section = ctk.CTkFrame(display_container, fg_color="transparent")
        sensor_section.pack(pady=10)

        # sensor_title = ctk.CTkLabel(sensor_section, text="Live Sensor Metrics", font=("Arial", 18, "bold"))
        # sensor_title.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        self.time_display = ctk.CTkLabel(sensor_section, text="Time\n--:--.--", **display_style)
        self.time_display.grid(row=1, column=0, padx=10, pady=5)

        self.step_display = ctk.CTkLabel(sensor_section, text="Steps\nN/A", **display_style)
        self.step_display.grid(row=1, column=1, padx=10, pady=5)

        self.angle_display = ctk.CTkLabel(sensor_section, text="Angle\nN/A°", **display_style)
        self.angle_display.grid(row=1, column=2, padx=10, pady=5)

        self.force_display_frame = ctk.CTkLabel(sensor_section, text="Force\n-- | --", **display_style)
        self.force_display_frame.grid(row=1, column=3, padx=10, pady=5)

        # === Bottom Section: System Info ===
        system_section = ctk.CTkFrame(display_container, fg_color="transparent")
        system_section.pack(pady=10)

        # system_title = ctk.CTkLabel(system_section, text="Protocol & System Info", font=("Arial", 18, "bold"))
        # system_title.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        self.protocol_step_counter = ctk.CTkLabel(system_section, text="Protocol\nStep N/A", **display_style)
        self.protocol_step_counter.grid(row=1, column=0, padx=10, pady=5)

        self.valve_display = ctk.CTkLabel(system_section, text="Valves\nN/A", **display_style)
        self.valve_display.grid(row=1, column=1, padx=10, pady=5)

        self.left_distance_label = ctk.CTkLabel(system_section, text="Left\n0.00 mm", **display_style)
        self.left_distance_label.grid(row=1, column=2, padx=10, pady=5)

        self.right_distance_label = ctk.CTkLabel(system_section, text="Right\n0.00 mm", **display_style)
        self.right_distance_label.grid(row=1, column=3, padx=10, pady=5)

        # make transparent graph here
        # === ADD TRANSPARENT GRAPH BELOW THE DISPLAYS ===
        if self.graph_frame is not None and self.graph_frame.winfo_exists():
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
        self.graph_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.graph_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.fig, self.ax = plt.subplots(figsize=(6, 4))  # Adjust the figure size as needed
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill="both")


        # === END GRAPH SETUP ===
        # Add a "Clear Graph" button underneath the graph
        self.clear_graph_button = ctk.CTkButton(
            self.main_frame,
            text="Clear Graph",
            command=self.clear_graph_data
        )
        self.clear_graph_button.pack(pady=(0, 10))

        # Initialize ProtocolViewer and start queue processing
        self.initialize_protocol_viewer()
        self.process_queue()

    def run_protocol(self):
        if self.protocol_running:
            print("Protocol is already running.")
            return
        protocol_name = self.protocol_var.get()
        self.protocol_name_label.configure(text=f"Current Protocol: {protocol_name}")
        print(f"Running Protocol: {protocol_name}")

        self.protocol_name_current = protocol_name
        # Start the protocol in a separate thread
        self.protocol_thread = threading.Thread(target=self.process_protocol, args=(protocol_name,))
        self.protocol_thread.start()
        self.protocol_running = True
        self.show_overlay_notification("Protocol started")
        print(f"Running Protocol: {protocol_name}")

    def update_sample_id(self, event):
        self.sampleID = self.sample_id_entry.get()

    def initialize_protocol_viewer(self):
        # Initialize ProtocolViewer directly
        self.protocol_viewer = ProtocolViewer(
            self.main_frame,
            protocol_folder=self.protocol_folder,
            protocol_var=self.protocol_var,
            app=self
        )
        self.protocol_viewer.pack(fill="both", expand=True, pady=10)

        # Trace for protocol_var to update ProtocolViewer when protocol changes
        self.protocol_var.trace("w", self.update_protocol_viewer)

    def update_protocol_viewer(self, *args):
        # Update the protocol viewer synchronously when protocol_var changes
        protocol_name = self.protocol_var.get()
        print(f"Updating ProtocolViewer with: {protocol_name}")  # Debug print
        self.protocol_viewer.load_protocol(protocol_name)

    def show_protocol_builder(self):
        self.home_displayed = False  # Set to False to indicate home is not displayed
        """Display the protocol builder page with a sidebar and main content area."""
        self.clear_content_frame()

    def toggle_mode(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)
        if mode == "Light":
            self.inspector_button.configure(text_color="black")
            self.settings_button.configure(text_color="black")
            self.home_button.configure(text_color="black")
            self.protocol_builder_button.configure(text_color="black")
            self.motor_forward_button.configure(text_color="black")
            self.motor_reverse_button.configure(text_color="black")
        else:
            self.inspector_button.configure(text_color="white")
            self.settings_button.configure(text_color="white")
            self.home_button.configure(text_color="white")
            self.protocol_builder_button.configure(text_color="white")
            self.motor_forward_button.configure(text_color="white")
            self.motor_reverse_button.configure(text_color="white")


    def show_calibrate(self):
        self.home_displayed = False  # Set to False to indicate home is not displayed
        # create a side bar that has a drop down menu for the user to select the trial they want to inspect. The trials will be read by reading the folders in ./data directory. If there are no trials in the directory the user will be prompted by a pop up window to got to the home page to run a protocol or can manually select one which will open up a file path dialog box for them to select the trial they want to inspect. Automatically create the figures for the trial and display them in the main frame
        # On the side bar also have a mannual upload box, save all figures button. Add a button if the slider is currently modified that says download cropped data. If slider is not modified, then the button will be greyed out. This button will trigger a popup that will have the default new file name as the folder name but with _cropped appended to the end. The user can change the name if they want. The .csv should be saved to the trial folder

        # once a trial has been selected, open the .csv file and read the data. See logic below on what figures to produce and how to handle the data. At the top of the main frame parse date, animal_ID, trial #, and provided_name (if there). The folder name format will either be f"{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}" or f"./data/{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}". Neatly display this information. Below that Neatly format the figures on the main frame, place a save figure button for each graph (which saves the figure to the current folder selected in ./data). At the bottom of the main frame make a dragable slider that allows the user to set the start and end data displayed. Have this update everything automtaically. In the data the final column is the step column and each step nin the slider should corespond to a step. Make sure to plot an axis for this slider.
        # Get available trials
        self.clear_content_frame()  # Clear existing content in the frame

    def show_settings(self):
        self.home_displayed = False  # Set to False to indicate home is not displayed
        self.clear_content_frame()
        settings_page = SettingsPage(self.content_frame, app=self)
        settings_page.pack(fill="both", expand=True)

    def set_motor_control(self, value):
        self.selected_motor = value.lower()  # Converts "Left"/"Both"/"Right" to lowercase for the command string

    def convert_duration_to_distance(self, duration, direction):
        """
        Temporary method to convert a duration into a distance.
        For now, 1 second yields 1.0 unit of distance.
        Forward movement is positive, reverse negative.
        """
        distance = duration * 1.0
        if direction.lower() == "reverse":
            return -distance
        return distance


    def start_motor_forward(self, event):
        # When the button is pressed, record the time and set the flag.
        self.motor_forward_pressed = True
        self.motor_forward_press_time = time.time()
        # After 300ms (debounce delay), check if still pressed.
        self.after(300, self.check_motor_forward_hold)

    def check_motor_forward_hold(self):
        # If the button is still pressed and 0.3 seconds have passed, start motor activity.
        if self.motor_forward_pressed and (time.time() - self.motor_forward_press_time >= 0.3):
            self.motor_forward_active = True
            self.send_motor_forward_command()

    def send_motor_forward_command(self):
        if self.motor_forward_active:
            # Send the forward command using the selected motor.
            command_str = f"forward,{self.selected_motor},0.1"
            self.motor_controller.send_command(command_str)

            # Convert the duration (0.1 sec) to distance.
            distance_increment = self.convert_duration_to_distance(0.1, "forward")
            if self.selected_motor == "left":
                self.distance_left += distance_increment
            elif self.selected_motor == "right":
                self.distance_right += distance_increment
            elif self.selected_motor == "both":
                self.distance_left += distance_increment
                self.distance_right += distance_increment


            self.after(100, self.send_motor_forward_command)

    def stop_motor_forward(self, event):
        # On button release, stop the motor activity.
        self.motor_forward_pressed = False
        self.motor_forward_active = False
        # Send a stop command to the motor controller.
        self.motor_controller.send_command("stop")

    def start_motor_reverse(self, event):
        # When the button is pressed, record the time and set the flag.
        self.motor_reverse_pressed = True
        self.motor_reverse_press_time = time.time()
        # After 300ms, check if the button is still pressed.
        self.after(300, self.check_motor_reverse_hold)

    def check_motor_reverse_hold(self):
        # If still pressed after 0.3s, start the reverse motor command.
        if self.motor_reverse_pressed and (time.time() - self.motor_reverse_press_time >= 0.3):
            self.motor_reverse_active = True
            self.send_motor_reverse_command()

    def send_motor_reverse_command(self):
        if self.motor_reverse_active:
            # Send the reverse command using the selected motor.
            command_str = f"reverse,{self.selected_motor},0.1"
            self.motor_controller.send_command(command_str)

            # Convert the duration (0.1 sec) to distance (note: reverse yields negative distance).
            distance_increment = self.convert_duration_to_distance(0.1, "reverse")
            if self.selected_motor == "left":
                self.distance_left += distance_increment
            elif self.selected_motor == "right":
                self.distance_right += distance_increment
            elif self.selected_motor == "both":
                self.distance_left += distance_increment
                self.distance_right += distance_increment

            # Update the distance display labels (if they exist).
            if hasattr(self, "left_distance_label"):
                self.left_distance_label.configure(text=f"Left: {self.distance_left:.2f}")
            if hasattr(self, "right_distance_label"):
                self.right_distance_label.configure(text=f"Right: {self.distance_right:.2f}")

            self.after(100, self.send_motor_reverse_command)

    def stop_motor_reverse(self, event):
        # On button release, stop the reverse motor activity.
        self.motor_reverse_pressed = False
        self.motor_reverse_active = False
        # Send a stop command to the motor controller.
        self.motor_controller.send_command("stop")

    def reset_left_distance(self):
        self.distance_left = 0.0
        if hasattr(self, "left_distance_label"):
            self.left_distance_label.configure(text="Left: 0.00")

    def reset_right_distance(self):
        self.distance_right = 0.0
        if hasattr(self, "right_distance_label"):
            self.right_distance_label.configure(text="Right: 0.00")

    def update_displays(self, step_count, current_input_pressure, current_pressure1, current_pressure2,
                        minutes, seconds, milliseconds, lps_temp, lps_pressure, valve1_state, valve2_state):
        # Helper to safely update a widget.
        def safe_configure(widget, **kwargs):
            try:
                if widget is not None and hasattr(widget, "winfo_exists") and widget.winfo_exists():
                    widget.configure(**kwargs)
            except Exception as e:
                print(f"Error updating widget {widget}: {e}")

        # --- Always update sensor data arrays, regardless of the current page ---
        # Use one of the pressures if the other is None.
        if current_pressure2 is None:
            current_pressure2 = current_pressure1
        if current_pressure1 is None:
            current_pressure1 = current_pressure2

        current_time_val = minutes * 60 + seconds + milliseconds / 1000.0
        self.graph_times.append(current_time_val)
        self.graph_input_pressures.append(current_input_pressure)
        self.graph_pressure1s.append(current_pressure1)
        self.graph_pressure2s.append(current_pressure2)

        # --- Update home page widgets if the home page is displayed ---
        if self.home_displayed:
            try:
                safe_configure(self.time_display, text=f"{int(minutes):02}:{int(seconds):02}.{milliseconds:03}")
                safe_configure(self.step_display, text=f"{step_count} / {self.moving_steps_total}")
                safe_configure(self.angle_display, text=f"{current_input_pressure:.2f} PSI")
                safe_configure(self.right_distance_label, text=f"Right: {self.distance_right:.2f}")
                safe_configure(self.left_distance_label, text=f"Left: {self.distance_left:.2f}")

                avg_force = (current_pressure1 + current_pressure2) / 2
                safe_configure(self.force_display_frame,
                               text=f"{avg_force:.2f} PSI\n{current_pressure1:.2f} PSI | {current_pressure2:.2f} PSI")

                # Update status boxes (RPI, UNO, BLK)
                try:
                    rpi_status = self.pressure_receiver.status()
                except Exception as e:
                    print(f"Error checking PressureReceiver status: {e}")
                    rpi_status = False
                try:
                    uno_status = self.motor_controller.status()
                except Exception as e:
                    print(f"Error checking MotorController status: {e}")
                    uno_status = False

                rpi_color = "green" if rpi_status else "red"
                uno_color = "green" if uno_status else "red"
                blk_color = "green"  # Assuming BLK status is always OK
                safe_configure(self.rpi_box, fg_color=rpi_color)
                safe_configure(self.uno_box, fg_color=uno_color)
                safe_configure(self.blk_box, fg_color=blk_color)

                protocol_step = self.protocol_step if self.protocol_step is not None else 0
                safe_configure(self.protocol_step_counter, text=f"Step: {protocol_step} / {self.total_steps}")
                safe_configure(self.valve_display, text=f"{valve1_state} | {valve2_state}")

                # Also update the home page graph if its canvas exists.
                if hasattr(self, "canvas") and self.canvas is not None:
                    if ctk.get_appearance_mode() == "Dark":
                        app_bg_color = "#1F1F1F"
                        text_bg_color = "white"
                    else:
                        app_bg_color = "#FFFFFF"
                        text_bg_color = "black"
                    self.fig.patch.set_facecolor(app_bg_color)
                    self.ax.set_facecolor(app_bg_color)

                    if len(self.graph_times) < 2:
                        print("[update_displays] Not enough data to plot. Latest entries:",
                              self.graph_times[-5:] if self.graph_times else "No data")
                    else:
                        # Determine the lower time bound (last 30 seconds)
                        current_time = self.graph_times[-1]
                        lower_bound = current_time - self.graph_time_range  # graph_time_range is set to 30 seconds

                        # Filter the data points within the last 30 seconds
                        filtered_data = [
                            (t, ip, p1, p2)
                            for t, ip, p1, p2 in
                            zip(self.graph_times, self.graph_input_pressures, self.graph_pressure1s,
                                self.graph_pressure2s)
                            if t >= lower_bound
                        ]

                        if filtered_data:
                            self.ax.clear()
                            if self.no_cap is True:
                                self.ax.plot(self.graph_times, self.graph_input_pressures, label="Input Pressure")
                                self.ax.plot(self.graph_times, self.graph_pressure1s, label="Pressure 1")
                                self.ax.plot(self.graph_times, self.graph_pressure2s, label="Pressure 2")
                            else:
                                times, input_pressures, pressure1s, pressure2s = zip(*filtered_data)
                                self.ax.clear()
                                self.ax.plot(times, input_pressures, label="Input Pressure")
                                self.ax.plot(times, pressure1s, label="Pressure 1")
                                self.ax.plot(times, pressure2s, label="Pressure 2")
                            # If target_pressure is a list parallel to graph_times, filter it similarly:
                            if self.target_pressure is not None:
                                filtered_target = [
                                    tp for t, tp in zip(self.graph_times, self.target_pressure) if t >= lower_bound
                                ]
                                self.ax.plot(self.graph_times, self.target_pressure, label="Target Pressure",
                                             color=text_bg_color)
                            if self.graph_y_range is not None:
                                # extract numbers from the graph_y_range tuple
                                low_y = self.graph_y_range[0]
                                high_y= self.graph_y_range[1]
                                self.ax.set_ylim(low_y, high_y)
                            self.ax.set_xlabel("Time (s)", color=text_bg_color)
                            self.ax.set_ylabel("PSI", color=text_bg_color)
                            self.ax.tick_params(axis='x', colors=text_bg_color)
                            self.ax.tick_params(axis='y', colors=text_bg_color)
                            self.ax.title.set_color(text_bg_color)
                            self.ax.legend()
                            legend = self.ax.legend()
                            legend.get_frame().set_facecolor(app_bg_color)
                            legend.get_frame().set_edgecolor(app_bg_color)
                            for text in legend.get_texts():
                                text.set_color(text_bg_color)
                            self.canvas.draw()
            except Exception as e:
                print(f"Error updating home displays: {e}")

        # --- Update the Calibrate button regardless of current page ---
        try:
            calibration_level = 0  # Adjust this logic as needed.
            if calibration_level == 0:
                safe_configure(self.calibrate_button, fg_color="red")
            elif calibration_level == 1:
                safe_configure(self.calibrate_button, fg_color="yellow")
            elif calibration_level == 2:
                safe_configure(self.calibrate_button, fg_color="green")
            else:
                safe_configure(self.calibrate_button, fg_color="gray")
        except Exception as e:
            print(f"Error updating Calibrate button: {e}")
            try:
                safe_configure(self.calibrate_button, fg_color="gray")
            except Exception as inner_e:
                print(f"Also failed to update calibrate button: {inner_e}")

        # --- Update the LPS info label ---
        try:
            safe_configure(self.lps_info_label, text=f"{lps_pressure:.3f} hPa | {lps_temp:.3f} °C")
        except Exception as e:
            print(f"Error updating lps_info_label: {e}")

    def clear_graph_data(self):
        # Reset the lists holding the graph data
        self.graph_times = []
        self.graph_input_pressures = []
        self.graph_pressure1s = []
        self.graph_pressure2s = []
        # Clear the current graph
        self.ax.cla()
        self.ax.set_facecolor("none")
        self.fig.patch.set_facecolor("none")
        self.canvas.draw()

    def update_graph_view(self, mode):
        # Clear the current graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Initialize variables
        self.angle_data = []
        self.force_data = []
        self.time_data = []

        # Create a new Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(6, 4))  # Adjust the figure size as needed
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill="both")

    def stop_protocol(self):
        self.stop_flag = "1"
        print("Stop flag set. Protocol will be halted.")

    def variable_saver(self, variable_name, user_input):
        with open('variables.txt', 'a') as file:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            file.write(f"{current_time}, {variable_name}, {user_input}\n")

    def get_from_dict(self, dict_key, variable_name):
        # Retrieve the dictionary from the class attribute
        data_dict = self.data_dict.get(dict_key, {})

        # Check if the variable name exists in the dictionary
        if variable_name in data_dict:
            return data_dict[variable_name]
        else:
            return None

    def save_to_dict(self, dict_key, variable_name, value):
        # Retrieve the dictionary from the class attribute
        data_dict = self.data_dict.get(dict_key, {})

        # Update the dictionary
        data_dict[variable_name] = value

        # Save the updated dictionary back to the class attribute
        self.data_dict[dict_key] = data_dict

    def string_to_value_checker(self, string_input, type_s="int"):
        try:
            # Try to convert the input directly to an integer or float
            if type_s == "float":
                return float(string_input)
            else:
                return int(string_input)
        except ValueError:
            if string_input.startswith("(") and string_input.endswith(")"):
                inner_expr = string_input[1:-1]  # Extract content inside parentheses
                # Define angle_value from Redis
                angle_value = self.get_from_dict('set_vars', inner_expr)
                if angle_value is None:
                    raise ValueError("Variable 'angle_value' not found in Redis.")
                angle_value = float(angle_value)  # Convert to float for calculations

                # Replace 'angle_value' with its value in the expression
                expr_with_value = inner_expr.replace(string_input, str(angle_value))
                try:
                    # Evaluate the expression and return the result
                    result = eval(expr_with_value)
                    if type_s == "float":
                        return float(result)
                    else:
                        return int(result)
                except Exception as e:
                    raise ValueError(f"Invalid expression in input: {string_input}. Error: {e}")
            # If no parentheses, check if it's a variable and look up in Redis
            angle_value = self.get_from_dict('set_vars', string_input)
            if angle_value is None:
                raise ValueError(f"Variable '{string_input}' not found in Redis.")
            elif isinstance(angle_value, str):
                cycle_count = 0
                while isinstance(angle_value, str) and cycle_count < 10:
                    angle_value = self.get_from_dict('set_vars', angle_value)
                    cycle_count += 1
                if isinstance(angle_value, str):
                    raise ValueError(f"Value for '{string_input}' in Redis is not a valid number after 10 cycles.")
            try:
                if type_s == "float":
                    return float(angle_value)
                else:
                    return int(float(angle_value))
            except ValueError:
                raise ValueError(f"Value for '{string_input}' in Redis is not a valid number.")

    def calculate_metric(metric, protocol_step):
        with open('data.csv', 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            data = [row for row in reader if int(row[6]) == protocol_step]

        if not data:
            raise ValueError(f"No data found for protocol step {protocol_step}")

        if metric == "min_force":
            return min(float(row[2]) for row in data)
        elif metric == "max_force":
            return max(float(row[2]) for row in data)
        elif metric == "final_force":
            return float(data[-1][2])
        elif metric == "final_angle":
            return float(data[-1][1])
        elif metric == "max_angle":
            return max(float(row[1]) for row in data)
        elif metric == "min_angle":
            return min(float(row[1]) for row in data)
        elif metric == "final_time":
            return float(data[-1][0])
        elif metric == "start_time":
            return float(data[0][0])
        elif metric == "total_time":
            return float(data[-1][0]) - float(data[0][0])
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def process_protocol(self, protocol_path):
        protocol_filename = os.path.basename(protocol_path)
        # turn protocol_path to the full path including file name
        protocol_path = os.path.join(self.protocol_folder, protocol_path)
        with open(protocol_path, 'r') as file:
            commands = file.readlines()
            step_number = 0
            data_saved = False
            folder_name = None

        # calculate total number of commands
        self.total_commands = len(commands)

        # clear previous data
        self.data_dict = {}
        self.init = True  # Initialize the protocol processing
        for command in commands:
            command = command.strip()
            if not command:
                continue
            step_number += 1
            self.protocol_command = command
            self.protocol_step = step_number
            stop_flag = self.stop_flag
            if stop_flag == "1":
                print("Protocol stopped.")
                break

            if command.startswith("Inflate"):
                parts = command.split(":")[1].split(",")

                # Extract and parse the inputs
                time_or_pressure = parts[0].strip()
                value = float(parts[1].strip())
                valve = parts[2].strip() if len(parts) > 2 else "Both"

                # Process the inputs
                value = self.string_to_value_checker(value, type_s='float')

                # Example usage of the parsed inputs
                print(f"Time/Pressure: {time_or_pressure}, Value: {value}, Valve: {valve}")
                self.inflate(time_or_pressure, value, valve)
                if len(parts) > 3:
                    for i in range(1, len(parts), 2):
                        metric = str(parts[i].strip())
                        variable_name = str(parts[i + 1].strip()) if i + 1 < len(parts) else metric
                        metric_value = self.calculate_metric(metric, self.protocol_step)
                        self.variable_saver(variable_name, metric_value)
                        self.save_to_dict('set_vars', variable_name, metric_value)
            elif command.startswith("Deflate"):
                parts = command.split(":")[1].split(",")

                # Extract and parse the inputs
                time_or_pressure = parts[0].strip()
                value = float(parts[1].strip())
                valve = parts[2].strip() if len(parts) > 2 else "Both"

                # Process the inputs
                value = self.string_to_value_checker(value, type_s='float')

                # Example usage of the parsed inputs
                print(f"Time/Pressure: {time_or_pressure}, Value: {value}, Valve: {valve}")
                self.deflate(time_or_pressure, value, valve)
                if len(parts) > 1:
                    for i in range(1, len(parts), 2):
                        metric = str(parts[i].strip())
                        variable_name = str(parts[i + 1].strip()) if i + 1 < len(parts) else metric
                        metric_value = self.calculate_metric(metric, self.protocol_step)
                        self.variable_saver(variable_name, metric_value)
                        self.save_to_dict('set_vars', variable_name, metric_value)


            elif command.startswith("Wait_for_user_input"):
                self.wait_for_user_input(command)
            elif command.startswith("no_save"):
                data_saved = True
            elif command.startswith("End"):
                self.end_all_commands()
                break
            print(f" Data saved: {data_saved}")

        self.end_all_commands()
        if not data_saved:
            # Set the name to the current date and time
            data_saved = self.create_folder_with_files(folder_name)
        self.protocol_running = False

    # Add save as file name ability

    def wait_for_user_input(self, command):
        parts = command.split(":")[1].split(",")
        popup_name = parts[0].strip()
        variable_name = parts[1].strip()
        response_type = parts[2].strip()

        def on_submit():
            user_input = entry.get()
            try:
                if response_type == "int":
                    user_input = int(user_input)
                elif response_type == "float":
                    user_input = float(user_input)
                elif response_type == "string":
                    user_input = str(user_input)
                else:
                    raise ValueError("Invalid response type")

                self.save_to_dict('set_vars', variable_name, user_input)
                # replace this with save_to_dict
                self.variable_saver(variable_name, user_input)
                popup.destroy()
            except ValueError:
                error_label.config(text=f"Invalid input type. Expected {response_type}.")

        popup = ctk.CTk()
        popup.title(popup_name)

        label = ctk.CTkLabel(popup, text=f"Enter {response_type} value:")
        label.pack(pady=10)

        entry = ctk.CTkEntry(popup)
        entry.pack(pady=5)

        submit_button = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_button.pack(pady=5)

        error_label = ctk.CTkLabel(popup, text="", fg_color="red")
        error_label.pack(pady=5)

        popup.mainloop()

    def end_all_commands(self):
        self.protocol_step = None

    def inflate(self, time_or_pressure, value, valve):
        if valve == "valve1" or valve == "both":
            self.valve1.supply()
        if valve == "valve2" or valve == "both":
            self.valve2.supply()

        if time_or_pressure == "time":
            time.sleep(value)
        elif time_or_pressure == "pressure":
            while self.lps.pressure < value:
                time.sleep(0.01)

        self.valve1.neutral()
        self.valve2.neutral()
        print(f"Inflating {valve} for {time_or_pressure} with value {value}")

    def deflate(self, time_or_pressure, value, valve):
        # Placeholder for the actual inflation logic
        print(f"Inflating {valve} for {time_or_pressure} with value {value}")

    def wait(self, wait_time):
        print(f"Waiting for {wait_time} seconds")
        time.sleep(wait_time)

    def wait_for_user_input(self, command):
        parts = command.split(":")[1].split(",")
        popup_name = parts[0].strip()
        variable_name = parts[1].strip()
        response_type = parts[2].strip()

        def on_submit():
            user_input = entry.get()
            try:
                if response_type == "int":
                    user_input = int(user_input)
                elif response_type == "float":
                    user_input = float(user_input)
                elif response_type == "string":
                    user_input = str(user_input)
                else:
                    raise ValueError("Invalid response type")

                self.save_to_dict('set_vars', variable_name, user_input)
                self.variable_saver(variable_name, user_input)
                popup.destroy()
            except ValueError:
                error_label.config(text=f"Invalid input type. Expected {response_type}.")

        popup = ctk.CTk()
        popup.title(popup_name)

        label = ctk.CTkLabel(popup, text=f"Enter {response_type} value:")
        label.pack(pady=10)

        entry = ctk.CTkEntry(popup)
        entry.pack(pady=5)

        submit_button = ctk.CTkButton(popup, text="Submit", command=on_submit)
        submit_button.pack(pady=5)

        error_label = ctk.CTkLabel(popup, text="", fg_color="red")
        error_label.pack(pady=5)

        popup.mainloop()

    def update_app_settings(self):
        """
        Reads settings.txt, converts each value to its proper type if possible,
        and updates the app's settings by doing:
            self.<key> = <converted_value>
        This function scans the whole file and applies all settings.
        """
        # Read current settings from file.
        settings = read_settings()  # Assumes read_settings() is defined and accessible.
        for key, value in settings.items():
            try:
                # Try to convert the value using eval (e.g., "True" becomes True, "(0, 100)" becomes a tuple, etc.)
                converted_value = eval(value)
            except Exception:
                # If eval fails, leave the value as a string.
                converted_value = value
            # Set the attribute on self with the name of the key.
            setattr(self, key, converted_value)
            print(f"Updated self.{key} = {converted_value}")


    def write_sensor_data_to_csv(self):
        # Define the CSV file name
        csv_file = 'data.csv'

        # Open the CSV file in write mode
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)

            # Write the headers
            headers = [
                'time', 'LPS_pressure', 'LPS_temperature', 'pressure0', 'pressure0_convert',
                'pressure1', 'pressure1_convert', 'pressure2', 'pressure2_convert',
                'pressure3', 'valve1_state', 'valve2_state',
                'self_target_pressure', 'self_target_time', 'clamp_state', 'self_protocol_step'
            ]
            writer.writerow(headers)

            # Write the sensor data
            for data in self.sensor_data:
                row = [
                    data['time'], data['LPS_pressure'], data['LPS_temperature'], data['pressure0'],
                    data['pressure0_convert'],
                    data['pressure1'], data['pressure1_convert'], data['pressure2'], data['pressure2_convert'],
                    data['pressure3'], data['valve1_state'], data['valve2_state'],
                    data['self_target_pressure'], data['self_target_time'], data['clamp_state'],
                    data['self_protocol_step']
                ]
                writer.writerow(row)

    def show_overlay_notification(self, message, auto_dismiss_ms=5000):
        """
        Displays a temporary overlay notification in the center of the window.

        Args:
            message (str): The message to display.
            auto_dismiss_ms (int): Time in milliseconds after which the notification auto-dismisses.
        """
        # Create a notification frame that will overlay on top of all other widgets.
        notification = ctk.CTkFrame(self, fg_color="green", corner_radius=10)
        # Place it in the center of the window.
        notification.place(relx=0.5, rely=0.5, anchor="s")
        # Bring the notification to the front.
        notification.tkraise()

        # Create a label with white text for the message.
        label = ctk.CTkLabel(notification, text=message, text_color="white", bg_color="transparent", font=("Arial", 12))
        label.pack(side="left", padx=(10, 5), pady=5)

        # Create a close button to allow manual dismissal.
        close_button = ctk.CTkButton(
            notification,
            text="X",
            width=20,
            fg_color="transparent",
            text_color="white",
            font=("Arial", 12),
            command=notification.destroy
        )
        close_button.pack(side="right", padx=(5, 10), pady=5)

        # Automatically dismiss the notification after auto_dismiss_ms milliseconds.
        if auto_dismiss_ms is not None:
            notification.after(auto_dismiss_ms, notification.destroy)


    def read_sensors(self):
        print("[read_sensors] Sensor thread started.")
        iteration_count = 0
        try:
            while True:
                iteration_count += 1
                current_iter_time = time.time()

                pressures = PressureReceiver.getpressures()
                if not pressures or len(pressures) < 4:
                    print(f"[read_sensors] Pressure data not available: {pressures}")
                    time.sleep(0.1)
                    continue
                pressure0, pressure1, pressure2, pressure3 = pressures

                # Initialize data_packet so it's always defined
                data_packet = None

                if self.protocol_step is not None and self.protocol_step > 0:
                    if self.init is not None:
                        self.protocol_start_time = time.time()
                        time_diff = 0
                        self.sensor_data = []  # Reset sensor data for the new protocol
                        self.init = None
                        self.clear_graph_data()
                        print("[read_sensors] Protocol started, sensor data reset.")
                    else:
                        time_diff = time.time() - self.protocol_start_time

                    LPS_pressure = self.lps.pressure
                    LPS_temperature = self.lps.temperature
                    self.update_pressure_values()
                    (self.pressure0_convert,
                     self.pressure1_convert,
                     self.pressure2_convert) = self.pressure_sensor_converter(
                        pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature)

                    valve1_state = self.valve1.get_state()
                    valve2_state = self.valve2.get_state()

                    self.sensor_data.append({
                        'time': time_diff,
                        'LPS_pressure': LPS_pressure,
                        'LPS_temperature': LPS_temperature,
                        'pressure0': pressure0,
                        'pressure0_convert': self.pressure0_convert,
                        'pressure1': pressure1,
                        'pressure1_convert': self.pressure1_convert,
                        'pressure2': pressure2,
                        'pressure2_convert': self.pressure2_convert,
                        'pressure3': pressure3,
                        'valve1_state': valve1_state,
                        'valve2_state': valve2_state,
                        'self_target_pressure': self.target_pressure,
                        'self_target_time': self.target_time,
                        'clamp_state': self.clamp_state,
                        'self_protocol_step': self.protocol_step
                    })

                    data_packet = {
                        'step_count': self.protocol_step,
                        'current_input_pressure': self.pressure0_convert,
                        'current_pressure1': self.pressure1_convert,
                        'current_pressure2': self.pressure2_convert,
                        'minutes': int(time_diff // 60),
                        'seconds': int(time_diff % 60),
                        'milliseconds': int((time_diff * 1000) % 1000),
                        'LPS_pressure': LPS_pressure,
                        'LPS_temperature': LPS_temperature,
                        'valve1_state': valve1_state,
                        'valve2_state': valve2_state
                    }
                else:
                    # Non-protocol branch: Use elapsed time even when protocol is not running.
                    current_time = time.time()
                    if not hasattr(self, 'non_protocol_start'):
                        self.non_protocol_start = current_time
                    time_diff = current_time - self.non_protocol_start
                    minutes = int(time_diff // 60)
                    seconds = int(time_diff % 60)
                    milliseconds = int((time_diff * 1000) % 1000)

                    LPS_pressure = self.lps.pressure
                    LPS_temperature = self.lps.temperature
                    self.update_pressure_values()
                    (self.pressure0_convert,
                     self.pressure1_convert,
                     self.pressure2_convert) = self.pressure_sensor_converter(
                        pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature)

                    valve1_state = self.valve1.get_state()
                    valve2_state = self.valve2.get_state()

                    self.sensor_data.append({
                        'time': time_diff,
                        'LPS_pressure': LPS_pressure,
                        'LPS_temperature': LPS_temperature,
                        'pressure0': pressure0,
                        'pressure0_convert': self.pressure0_convert,
                        'pressure1': pressure1,
                        'pressure1_convert': self.pressure1_convert,
                        'pressure2': pressure2,
                        'pressure2_convert': self.pressure2_convert,
                        'pressure3': pressure3,
                        'valve1_state': valve1_state,
                        'valve2_state': valve2_state,
                        'self_target_pressure': self.target_pressure,
                        'self_target_time': self.target_time,
                        'clamp_state': self.clamp_state,
                        'self_protocol_step': self.protocol_step
                    })

                    data_packet = {
                        'step_count': self.protocol_step,
                        'current_input_pressure': self.pressure0_convert,
                        'current_pressure1': self.pressure1_convert,
                        'current_pressure2': self.pressure2_convert,
                        'minutes': minutes,
                        'seconds': seconds,
                        'milliseconds': milliseconds,
                        'LPS_pressure': LPS_pressure,
                        'LPS_temperature': LPS_temperature,
                        'valve1_state': valve1_state,
                        'valve2_state': valve2_state
                    }
                # Queue the data packet
                if data_packet is not None:
                    self.update_queue.put(data_packet)

                time.sleep(0.1)
        except Exception as e:
            print(f"[read_sensors] Error: {e}")

    def pressure_sensor_converter(self, pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature):
        # Convert raw sensor values to calibrated pressures for each sensor.
        conv_pressure0, conv_pressure1, conv_pressure2 = self.calibrator.pressure_sensor_converter_main(
            pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature
        )

        return conv_pressure0, conv_pressure1, conv_pressure2

    def process_queue(self):
        try:
            while True:
                q_size = self.update_queue.qsize()
                data = self.update_queue.get_nowait()

                self.update_displays(
                    step_count=data['step_count'],
                    current_input_pressure=data['current_input_pressure'],
                    current_pressure1=data['current_pressure1'],
                    current_pressure2=data['current_pressure2'],
                    minutes=data['minutes'],
                    seconds=data['seconds'],
                    milliseconds=data['milliseconds'],
                    lps_temp=data.get('LPS_temperature', None),
                    lps_pressure=data.get('LPS_pressure', None),
                    valve1_state=data.get('valve1_state', None),
                    valve2_state=data.get('valve2_state', None)
                )

        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def create_folder_with_files(self, provided_name=None, special=False):
        self.write_sensor_data_to_csv()
        animal_id = self.get_from_dict('set_vars', 'animal_id')
        if animal_id is None:
            animal_id = "0000"

        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        trial_number = 1

        if provided_name is not None:
            exact_folder_name = original_folder_name = f"{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}"
            folder_name = original_folder_name
            if os.path.exists(f"./data/{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}"):
                while os.path.exists(folder_name):
                    trial_number += 1
                    folder_name = f"./data/{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}"
            else:
                folder_name = f"./data/{timestamp}_{animal_id}_{trial_number:02d}"
        else:
            exact_folder_name = original_folder_name = f"{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}"
            folder_name = original_folder_name
            if os.path.exists(f"./data/{timestamp}_{animal_id}_{trial_number:02d}"):
                while os.path.exists(f"./data/{timestamp}_{animal_id}_{trial_number:02d}"):
                    trial_number += 1
                    folder_name = f"./data/{timestamp}_{animal_id}_{trial_number:02d}"
            else:
                folder_name = f"./data/{timestamp}_{animal_id}_{trial_number:02d}"
        # create the folder
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        else:
            print(f"Error: Folder '{folder_name}' already exists.")
            # TODO: Handle this error
        # Copy and rename `calibrate.txt`
        # copy everything into folder
        print(f"Copying files to {folder_name}")
        if os.path.exists('calibration.csv'):
            if provided_name is not None:
                shutil.copy('calibration.csv', os.path.join(folder_name, 'calibration.csv'))

        else:
            print("Error: `calibration.txt` not found.")

        # copy current protocol into folder check redis current_protocol_out for base name and add ./protocols/
        current_protocol_out = self.protocol_name_current
        if current_protocol_out is not None:
            protocol_path = os.path.join('protocols', current_protocol_out)
            if os.path.exists(protocol_path):
                shutil.copy(protocol_path, os.path.join(folder_name, current_protocol_out))
            else:
                print(f"Error: Protocol file not found: {protocol_path}")

        with open('data.csv', 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            data = [row for row in reader]
            self.total_time = data[-1][0]
            self.total_steps = len(data[6])

        # Copy and rename `data.csv`
        data_csv_path = 'data.csv'
        renamed_csv_path = os.path.join(folder_name, f"{exact_folder_name}.csv")
        if os.path.exists(data_csv_path):
            shutil.copy(data_csv_path, os.path.join(folder_name, f"{exact_folder_name}.csv"))
            self.verify_and_wipe_data_csv(data_csv_path, renamed_csv_path)
        else:
            print("Error: `data.csv` not found.")

        # check redis for selected_arm
        selected_arm = None
        if selected_arm is None:
            selected_arm = "Unknown"

        # Create and save `information.txt` with the current date
        info_path = os.path.join(folder_name, 'information.txt')
        with open(info_path, 'w') as info_file:
            current_date =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            info_file.write(f"Created on: {current_date}\n")
            info_file.write(f"Total time: {self.total_time}\n")
            info_file.write(f"Total steps: {self.total_steps}\n")
            info_file.write(f"Animal ID: {animal_id}\n")
            info_file.write(f"Selected arm: {selected_arm}\n")

        # variables.txt
        current_date =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # get all from  def get_from_dict(self, dict_key, variable_name):
        #         # Retrieve the dictionary from the class attribute
        #         data_dict = self.data_dict.get(dict_key, {})
        #
        #         # Check if the variable name exists in the dictionary
        #         if variable_name in data_dict:
        #             return data_dict[variable_name]
        #         else:
        #             return None
        set_vars = self.data_dict.get('set_vars', {})
        with open('variables.txt', 'a') as file:
            for key, value in set_vars.items():
                file.write(f"{current_date}, {key}, {value}\n")
        if os.path.exists('variables.txt'):
            shutil.copy('variables.txt', os.path.join(folder_name, 'variables.txt'))
        else:
            print("Error: `variables.txt` not found.")
        self.verify_and_wipe_data_csv('variables.txt', os.path.join(folder_name, 'variables.txt'))

        return True

    def verify_and_wipe_data_csv(self, original_path, copied_path):
        # Verify that the contents of the original and copied files match
        if filecmp.cmp(original_path, copied_path, shallow=False):
            print("Verification successful: The copied file matches the original.")
            # Wipe out the original data.csv
            with open(original_path, 'w') as file:
                file.truncate(0)
            print("Original data.csv has been wiped out.")
        else:
            print("Verification failed: The copied file does not match the original.")

    def on_closing(self):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()
        self.destroy()

    def update_output_window(self):
        # Define the method's functionality here
        pass

    def show_calibrate(self):
        self.home_displayed = False  # Indicate that the home page is not displayed
        self.clear_content_frame()
        # Create a frame for the calibrate page
        calibrate_frame = CalibratePage(self.content_frame, app=self)
        calibrate_frame.pack(fill="both", expand=True, padx=20, pady=20)


if __name__ == "__main__":
    # Load the pre-trained models from the saved joblib file.
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()


# add to settings page: self.no_cap, self.graph_y_range (tuple), self.graph_time_range, self.accent_color