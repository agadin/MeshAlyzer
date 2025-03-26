# valve_control_dropdown.py
import customtkinter as ctk


class ValveControlDropdown(ctk.CTkFrame):
    def __init__(self, master, get_pressures_func, on_vent, on_neutral, on_supply, *args, **kwargs):
        """
        Parameters:
         - master: parent widget.
         - get_pressures_func: a callable that returns a dict with keys:
               "pressure0", "pressure1", and "pressure2".
         - on_vent: callable to execute when button is set to Vent.
         - on_neutral: callable to execute when button is set to Neutral.
         - on_supply: callable to execute when button is set to Supply.
        """
        super().__init__(master, *args, **kwargs)
        self.get_pressures = get_pressures_func
        self.on_vent = on_vent
        self.on_neutral = on_neutral
        self.on_supply = on_supply

        self.inactivity_timer_id = None
        self.dropdown_visible = False

        # Toggle button to open/close the dropdown
        self.toggle_button = ctk.CTkButton(self, text="Valve Control", command=self.toggle_dropdown)
        self.toggle_button.pack(pady=5)

        # Dropdown frame (initially hidden)
        self.dropdown_frame = ctk.CTkFrame(self)

        # Segmented button with three options. Starts at "Neutral".
        self.segmented_button = ctk.CTkSegmentedButton(
            self.dropdown_frame,
            values=["Vent", "Neutral", "Supply"],
            command=self.segmented_button_changed
        )
        self.segmented_button.set("Neutral")
        self.segmented_button.pack(pady=5, padx=5)

        # Warning label below the segmented button
        self.warning_label = ctk.CTkLabel(self.dropdown_frame, text="", text_color="red")
        self.warning_label.pack(pady=5)

        # Start periodic pressure checking (every 500ms)
        self.after(500, self.update_pressures)

    def toggle_dropdown(self):
        """Toggle the dropdown open/closed."""
        if self.dropdown_visible:
            self.hide_dropdown()
        else:
            self.show_dropdown()

    def show_dropdown(self):
        """Show the dropdown and start the inactivity timer."""
        pressures = self.get_pressures()
        if pressures.get("pressure0", 0) < 15:
            self.segmented_button.configure(state="disabled")
            self.warning_label.configure(text="Minimum input pressure is 15psi")
        else:
            self.segmented_button.configure(state="normal")
            self.warning_label.configure(text="")

        self.dropdown_frame.pack(pady=5)
        self.dropdown_visible = True
        self.reset_inactivity_timer()

    def hide_dropdown(self):
        """Hide the dropdown and cancel the inactivity timer."""
        if self.inactivity_timer_id is not None:
            self.after_cancel(self.inactivity_timer_id)
            self.inactivity_timer_id = None
        self.dropdown_frame.pack_forget()
        self.dropdown_visible = False

    def reset_inactivity_timer(self):
        """Reset the 30-second timer that will hide the dropdown after inactivity."""
        if self.inactivity_timer_id is not None:
            self.after_cancel(self.inactivity_timer_id)
        self.inactivity_timer_id = self.after(30000, self.hide_dropdown)

    def segmented_button_changed(self, selected_value):
        """Called when the segmented button selection changes.
           Resets the timer and calls the appropriate valve function."""
        self.reset_inactivity_timer()

        if selected_value == "Vent":
            self.on_vent()
        elif selected_value == "Neutral":
            self.on_neutral()
        elif selected_value == "Supply":
            self.on_supply()

    def update_pressures(self):
        """
        Periodically check pressures:
         - Disables segmented button if pressure0 is below 15.
         - Displays a warning if pressure1 or pressure2 exceeds 80.
         - If either exceeds 100, resets segmented button to Neutral and displays a warning.
        """
        pressures = self.get_pressures()

        if self.dropdown_visible:
            # Check minimum pressure condition
            if pressures.get("pressure0", 0) < 15:
                self.segmented_button.configure(state="disabled")
                self.warning_label.configure(text="Minimum input pressure is 15psi")
            else:
                self.segmented_button.configure(state="normal")
                # Clear warning if no high-pressure condition exists
                if pressures.get("pressure1", 0) < 80 and pressures.get("pressure2", 0) < 80:
                    self.warning_label.configure(text="")

            # Check balloon pressure warnings
            p1 = pressures.get("pressure1", 0)
            p2 = pressures.get("pressure2", 0)
            max_balloon = max(p1, p2)
            if max_balloon > 100:
                # Reset segmented button to "Neutral" and warn that limits are exceeded.
                self.segmented_button.set("Neutral")
                self.warning_label.configure(text="Supply is exceeding its limits")
                self.on_neutral()
            elif max_balloon > 80:
                self.warning_label.configure(text=f"Warning high balloon pressure: {max_balloon:.1f}")

        self.after(500, self.update_pressures)
