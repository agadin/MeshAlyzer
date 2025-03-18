#!/usr/bin/python
# -*- coding:utf-8 -*-

import customtkinter as ctk
from PIL import Image
import RPi.GPIO as GPIO
import time
from threading import Thread

# Motor parameters (adjust as needed for your motors)
REV_TIME = 2.4  # seconds per revolution at chosen duty cycle (for a 50RPM motor at 50% duty)
DEFAULT_DUTY = 50  # Duty cycle percentage used for both calibration and stretch

class ClampingMotorController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
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

        # Setup all pins as outputs
        motor_pins = [self.rl_in4, self.rl_in3, self.rl_ena, self.fl_ena,
                      self.fl_in1, self.fl_in2, self.fr_ena, self.fr_in4,
                      self.fr_in3, self.rr_ena, self.rr_in1, self.rr_in2]
        for pin in motor_pins:
            GPIO.setup(pin, GPIO.OUT)

        # Set up PWM channels (100 Hz)
        self.fl_pwm = GPIO.PWM(self.fl_ena, 100)
        self.fr_pwm = GPIO.PWM(self.fr_ena, 100)
        self.rl_pwm = GPIO.PWM(self.rl_ena, 100)
        self.rr_pwm = GPIO.PWM(self.rr_ena, 100)
        self.fl_pwm.start(0)
        self.fr_pwm.start(0)
        self.rl_pwm.start(0)
        self.rr_pwm.start(0)

        # Save the direction control pins for convenience.
        self.fl_in1 = self.fl_in1; self.fl_in2 = self.fl_in2
        self.rl_in3 = self.rl_in3; self.rl_in4 = self.rl_in4
        self.fr_in3 = self.fr_in3; self.fr_in4 = self.fr_in4
        self.rr_in1 = self.rr_in1; self.rr_in2 = self.rr_in2

        # Conversion factor: cm per revolution (set during calibration)
        self.distance_per_rev = None

    def drive_motors(self, l_speed, l_dir, r_speed, r_dir):
        """Drive left and right motors at given speeds (0-100) and direction (True for forward, False for reverse)."""
        self.fl_pwm.ChangeDutyCycle(l_speed)
        self.rl_pwm.ChangeDutyCycle(l_speed)
        self.fr_pwm.ChangeDutyCycle(r_speed)
        self.rr_pwm.ChangeDutyCycle(r_speed)
        # Left side: both motors use same direction signals.
        GPIO.output(self.fl_in1, l_dir)
        GPIO.output(self.fl_in2, not l_dir)
        GPIO.output(self.rl_in3, l_dir)
        GPIO.output(self.rl_in4, not l_dir)
        # Right side:
        GPIO.output(self.fr_in3, r_dir)
        GPIO.output(self.fr_in4, not r_dir)
        GPIO.output(self.rr_in1, r_dir)
        GPIO.output(self.rr_in2, not r_dir)

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
        """Stop motors and clean up GPIO."""
        self.stop()
        GPIO.cleanup()


# ---------------------------
# GUI Application
# ---------------------------
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
