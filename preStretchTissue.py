#!/usr/bin/python
# -*- coding:utf-8 -*-

import lgpio        # Low‑level GPIO library (assumes lgpio is installed)
import time
from threading import Thread
import customtkinter as ctk
from PIL import Image

# Motor parameters (adjust as needed for your motors)
REV_TIME = 2.4  # seconds per revolution at chosen duty cycle (for a 50RPM motor at 50% duty)
DEFAULT_DUTY = 50  # Duty cycle percentage used for both calibration and stretch

###############################################################################
# Helper classes for lgpio functionality

class LGPIOWrapper:
    """
    A simple wrapper around lgpio to request lines as outputs and set their values.
    (Note: This is a minimal example. The actual lgpio API might require adjustments.)
    """
    def __init__(self):
        # Open chip 0 (adjust if your chip number is different)
        self.chip = lgpio.gpiochip_open(0)
        self.lines = {}  # Maps pin numbers to line handles

    def setup(self, pin):
        # Request the line for output.
        # (The following call is pseudo-code: replace with your actual lgpio output request.)
        # Here we assume lgpio.gpio_request_line returns a handle for the given pin.
        handle = lgpio.gpio_request_line(self.chip, [pin], "lgpio", 0, 0)
        self.lines[pin] = handle

    def output(self, pin, value):
        # Set the pin's output value (value should be True/False).
        # (Replace with your lgpio call to set the line value.)
        # For example, if lgpio has a function named gpio_set_line_value:
        lgpio.gpio_set_line_value(self.lines[pin], value)

    def cleanup(self):
        # Release all requested lines and close the chip.
        for handle in self.lines.values():
            lgpio.gpio_release_line(handle)
        lgpio.gpiochip_close(self.chip)


class LGPIOPWM:
    """
    A lightweight software-PWM class using lgpio outputs.
    (For hardware PWM, you would use the lgpio/hardware-specific functions if available.)
    """
    def __init__(self, lgpio_wrapper, pin, frequency):
        self.lgpio = lgpio_wrapper
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0  # in percent (0-100)
        self.running = False

    def start(self, duty):
        self.duty_cycle = duty
        self.running = True
        self._pwm_thread = Thread(target=self._run_pwm)
        self._pwm_thread.daemon = True
        self._pwm_thread.start()

    def _run_pwm(self):
        period = 1.0 / self.frequency
        while self.running:
            # Calculate on and off times based on duty cycle
            on_time = period * (self.duty_cycle / 100.0)
            off_time = period - on_time
            # Set the pin high for on_time and low for off_time
            self.lgpio.output(self.pin, True)
            time.sleep(on_time)
            self.lgpio.output(self.pin, False)
            time.sleep(off_time)

    def ChangeDutyCycle(self, duty):
        self.duty_cycle = duty

    def stop(self):
        self.running = False


###############################################################################
# ClampingMotorController using lgpio

class ClampingMotorController:
    def __init__(self):
        # Initialize our lgpio wrapper (no setmode needed)
        self.lgpio = LGPIOWrapper()
        # --- Left Motor Driver Pins ---
        # For left side, we assume two motors (front and rear) are wired similarly.
        self.rl_in4 = 14
        self.rl_in3 = 15
        self.rl_ena  = 18
        self.fl_ena  = 23
        self.fl_in1  = 24
        self.fl_in2  = 25

        # --- Right Motor Driver Pins ---
        self.fr_ena  = 2
        self.fr_in4  = 3
        self.fr_in3  = 4
        self.rr_ena  = 17
        self.rr_in1  = 27
        self.rr_in2  = 22

        # List of all motor pins
        motor_pins = [self.rl_in4, self.rl_in3, self.rl_ena, self.fl_ena,
                      self.fl_in1, self.fl_in2, self.fr_ena, self.fr_in4,
                      self.fr_in3, self.rr_ena, self.rr_in1, self.rr_in2]

        # Request each pin as an output using our lgpio wrapper
        for pin in motor_pins:
            self.lgpio.setup(pin)

        # Set up PWM channels (100 Hz) for enable pins using our LGPIOPWM class
        self.fl_pwm = LGPIOPWM(self.lgpio, self.fl_ena, 100)
        self.fr_pwm = LGPIOPWM(self.lgpio, self.fr_ena, 100)
        self.rl_pwm = LGPIOPWM(self.lgpio, self.rl_ena, 100)
        self.rr_pwm = LGPIOPWM(self.lgpio, self.rr_ena, 100)
        # Start them with 0% duty cycle
        self.fl_pwm.start(0)
        self.fr_pwm.start(0)
        self.rl_pwm.start(0)
        self.rr_pwm.start(0)

        # Conversion factor: cm per revolution (set during calibration)
        self.distance_per_rev = None

    def drive_motors(self, l_speed, l_dir, r_speed, r_dir):
        """
        Drive left and right motors at given speeds (0-100) and direction
        (True for forward, False for reverse).
        """
        # Update PWM duty cycles for left and right enable pins
        self.fl_pwm.ChangeDutyCycle(l_speed)
        self.rl_pwm.ChangeDutyCycle(l_speed)
        self.fr_pwm.ChangeDutyCycle(r_speed)
        self.rr_pwm.ChangeDutyCycle(r_speed)

        # Left side: both motors use same direction signals.
        self.lgpio.output(self.fl_in1, l_dir)
        self.lgpio.output(self.fl_in2, not l_dir)
        self.lgpio.output(self.rl_in3, l_dir)
        self.lgpio.output(self.rl_in4, not l_dir)
        # Right side:
        self.lgpio.output(self.fr_in3, r_dir)
        self.lgpio.output(self.fr_in4, not r_dir)
        self.lgpio.output(self.rr_in1, r_dir)
        self.lgpio.output(self.rr_in2, not r_dir)

    def stop(self):
        """Stop all motors."""
        self.drive_motors(0, True, 0, True)

    def run_calibration_rotation(self):
        """Rotate both sides for 10 revolutions at DEFAULT_DUTY."""
        total_time = 10 * REV_TIME
        print("Starting calibration rotation for 10 revolutions...")
        self.drive_motors(DEFAULT_DUTY, True, DEFAULT_DUTY, True)
        time.sleep(total_time)
        self.stop()
        print("Calibration rotation complete.")

    def set_calibration(self, measured_distance):
        """
        Given the measured distance (in cm) that the clamps moved during 10 revolutions,
        compute and store the conversion factor (cm per revolution).
        """
        self.distance_per_rev = measured_distance / 10.0
        print(f"Calibration set: {self.distance_per_rev:.2f} cm per revolution.")

    def stretch_tissue(self, sample_length, desired_stretch):
        """
        Calculate the required revolutions to stretch the tissue.
        Each clamp will move half of the desired total stretch.
        """
        if self.distance_per_rev is None:
            print("Error: Calibration not set. Please calibrate first.")
            return
        movement_needed = desired_stretch / 2.0  # Each side moves half the total stretch
        revs_needed = movement_needed / self.distance_per_rev
        duration = revs_needed * REV_TIME
        print(f"Stretching: Each clamp needs to move {movement_needed:.2f} cm "
              f"({revs_needed:.2f} revolutions), duration = {duration:.2f} s.")
        # For stretching, left clamp moves forward while right clamp moves in reverse
        self.drive_motors(DEFAULT_DUTY, True, DEFAULT_DUTY, False)
        time.sleep(duration)
        self.stop()
        print("Stretching complete.")

    def cleanup(self):
        """Stop motors, stop PWM threads and clean up lgpio."""
        self.stop()
        self.fl_pwm.stop()
        self.fr_pwm.stop()
        self.rl_pwm.stop()
        self.rr_pwm.stop()
        self.lgpio.cleanup()


###############################################################################
# GUI Application (unchanged except that it uses the new ClampingMotorController)

class PreStretchTissueApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MeshAlyzer Pre-Stretch Tissue Control")
        self.geometry("600x500")
        self.motor_controller = ClampingMotorController()
        self.setup_gui()

    def setup_gui(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.bind("<Key>", self.on_key)

        # Header with logos
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", pady=10)
        try:
            meshalyzer_img = Image.open("img/MeshAlyzer.jpeg")
            stl_img = Image.open("img/lakelab.jpg")
        except FileNotFoundError:
            meshalyzer_img = Image.new("RGB", (220, 80), color="gray")
            stl_img = Image.new("RGB", (120, 80), color="gray")
        meshalyzer_ctk_img = ctk.CTkImage(dark_image=meshalyzer_img, size=(220, 80))
        stl_ctk_img = ctk.CTkImage(dark_image=stl_img, size=(120, 80))
        meshalyzer_label = ctk.CTkLabel(header_frame, text="", image=meshalyzer_ctk_img)
        meshalyzer_label.pack(side="left", padx=20)
        stl_label = ctk.CTkLabel(header_frame, text="", image=stl_ctk_img)
        stl_label.pack(side="right", padx=20)

        # Main Tabview with two tabs: Calibrate and Stretch Tissue
        self.tabview = ctk.CTkTabview(self, width=580, height=350)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Option 1: Calibrate")
        self.tabview.add("Option 2: Stretch Tissue")

        # ----- Option 1: Calibrate -----
        cal_frame = self.tabview.tab("Option 1: Calibrate")
        cal_title = ctk.CTkLabel(cal_frame, text="Calibration Mode", font=("Helvetica", 16, "bold"))
        cal_title.pack(pady=10)

        info_label = ctk.CTkLabel(cal_frame, text="This will rotate the clamps for 10 revolutions.\n"
                                                    "Measure the distance (cm) that the clamps moved.")
        info_label.pack(pady=5)

        run_button = ctk.CTkButton(cal_frame, text="Run Calibration Rotation", command=self.run_calibration)
        run_button.pack(pady=5)

        self.distance_entry = ctk.CTkEntry(cal_frame, placeholder_text="Measured distance (cm)")
        self.distance_entry.pack(pady=5)

        set_calib_button = ctk.CTkButton(cal_frame, text="Set Calibration Factor", command=self.set_calibration)
        set_calib_button.pack(pady=5)

        # ----- Option 2: Stretch Tissue -----
        stretch_frame = self.tabview.tab("Option 2: Stretch Tissue")
        stretch_title = ctk.CTkLabel(stretch_frame, text="Stretch Tissue Mode", font=("Helvetica", 16, "bold"))
        stretch_title.pack(pady=10)

        self.sample_length_entry = ctk.CTkEntry(stretch_frame, placeholder_text="Sample length (cm)")
        self.sample_length_entry.pack(pady=5)
        self.desired_stretch_entry = ctk.CTkEntry(stretch_frame, placeholder_text="Desired total stretch (cm)")
        self.desired_stretch_entry.pack(pady=5)

        stretch_button = ctk.CTkButton(stretch_frame, text="Stretch Tissue", command=self.stretch_tissue)
        stretch_button.pack(pady=5)

    def run_calibration(self):
        """Runs the calibration rotation on a separate thread."""
        t = Thread(target=self.motor_controller.run_calibration_rotation)
        t.daemon = True
        t.start()

    def set_calibration(self):
        """Reads the measured distance from the entry and sets the conversion factor."""
        try:
            measured_distance = float(self.distance_entry.get())
            self.motor_controller.set_calibration(measured_distance)
        except ValueError:
            ctk.CTkMessagebox(title="Input Error", message="Please enter a valid number for measured distance.")

    def stretch_tissue(self):
        """Reads sample length and desired stretch, then performs the stretch operation."""
        try:
            sample_length = float(self.sample_length_entry.get())
            desired_stretch = float(self.desired_stretch_entry.get())
            t = Thread(target=self.motor_controller.stretch_tissue, args=(sample_length, desired_stretch))
            t.daemon = True
            t.start()
        except ValueError:
            ctk.CTkMessagebox(title="Input Error", message="Please enter valid numbers for sample length and desired stretch.")

    def on_key(self, event):
        if event.char.lower() == "q":
            self.on_close()

    def on_close(self):
        self.motor_controller.cleanup()
        self.destroy()

if __name__ == "__main__":
    app = PreStretchTissueApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
