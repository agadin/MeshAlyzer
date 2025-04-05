import os
import shutil
import customtkinter as ctk

# --- Core Functions for Settings File Management ---

def load_default_settings():
    """
    Copies default_settings.txt to settings.txt on bootup.
    """
    try:
        shutil.copy("default_settings.txt", "settings.txt")
        print("Default settings loaded.")
    except Exception as e:
        print("Error copying default settings:", e)

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


def write_settings(settings):
    """
    Writes a dictionary of settings back to settings.txt.
    """
    with open("settings.txt", "w") as file:
        for key, value in settings.items():
            file.write(f"{key} = {value}\n")

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, app, *args, **kwargs):
        """
        A settings page that displays each setting as a rounded box with:
          - Title (left)
          - Description (center)
          - Input widget (Entry for text/numbers or Switch for booleans)
          - A checkbox to mark the value as default
        """
        super().__init__(master, *args, **kwargs)
        self.app = app  # reference to the main application
        self.settings = read_settings()  # load current settings from file
        self.settings_definitions = {
            "no_cap": {
                "title": "No Cap",
                "description": "Disable cap functionality.",
                "type": "bool"
            },
            "graph_y_range": {
                "title": "Graph Y Range",
                "description": "Enter Y-axis range as a tuple (e.g., (0,100)).",
                "type": "tuple"
            },
            "graph_time_range": {
                "title": "Graph Time Range",
                "description": "Time range for graph display (seconds).",
                "type": "int"
            },
            "accent_color": {
                "title": "Accent Color",
                "description": "Hex or color name for theme accent.",
                "type": "str"
            },
            # You can add more settings here easily
        }
        self.setting_widgets = {}  # Store widget references for each setting
        self.settings_modified = False

        # --- Create a Scrollable Frame for Settings ---
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Dynamically create a "rounded box" for each setting.
        row = 0
        for key, definition in self.settings_definitions.items():
            frame = ctk.CTkFrame(self.scroll_frame, corner_radius=10, fg_color="lightgray")
            frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            frame.columnconfigure(1, weight=1)

            # Title Label
            title_label = ctk.CTkLabel(frame, text=definition["title"], width=100)
            title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

            # Description Label
            desc_label = ctk.CTkLabel(frame, text=definition["description"])
            desc_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

            # Create input widget based on type
            if definition["type"] == "bool":
                current_val = self.str_to_bool(self.settings.get(key, "False"))
                input_var = ctk.BooleanVar(value=current_val)
                input_widget = ctk.CTkSwitch(frame, variable=input_var,
                                             command=lambda key=key, fr=frame: self.mark_modified(key, fr))
            elif definition["type"] == "dropdown":
                # For drop-down, use the options list from the definition
                current_val = self.settings.get(key, definition["options"][0])
                input_var = ctk.StringVar(value=current_val)
                input_widget = ctk.CTkComboBox(frame, values=definition["options"],
                                               variable=input_var,
                                               command=lambda val, key=key, fr=frame: self.mark_modified(key, fr))
            else:
                # Default: use an entry widget
                current_val = self.settings.get(key, "")
                input_var = ctk.StringVar(value=current_val)
                input_widget = ctk.CTkEntry(frame, textvariable=input_var)
                input_widget.bind("<KeyRelease>", lambda e, key=key, fr=frame: self.mark_modified(key, fr))
            input_widget.grid(row=0, column=2, padx=5, pady=5, sticky="w")

            # Checkbox for "Save as Default" (optional)
            default_var = ctk.BooleanVar(value=False)
            default_checkbox = ctk.CTkCheckBox(frame, text="Default", variable=default_var)
            default_checkbox.grid(row=0, column=3, padx=5, pady=5)

            self.setting_widgets[key] = {
                "frame": frame,
                "input_var": input_var,
                "default_var": default_var,
                "definition": definition
            }
            row += 1

        # --- Control Buttons Frame ---
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", pady=10)
        # Save & Apply button starts disabled.
        self.save_apply_button = ctk.CTkButton(button_frame, text="Save & Apply",
                                               command=self.save_and_apply, state="disabled")
        self.save_apply_button.pack(side="left", padx=10)
        # Restore button to load defaults
        restore_button = ctk.CTkButton(button_frame, text="Restore", command=self.restore_defaults)
        restore_button.pack(side="left", padx=10)

    def str_to_bool(self, s):
        return s.lower() in ("true", "1", "yes")

    def mark_modified(self, key, frame):
        """
        Called when a setting is modified.
        Changes the box color and enables the Save & Apply button.
        """
        frame.configure(fg_color="lightblue")  # Visual indication of change
        self.settings_modified = True
        self.save_apply_button.configure(state="normal", fg_color="green")

    def save_and_apply(self):
        new_settings = {}
        for key, widgets in self.setting_widgets.items():
            definition = widgets["definition"]
            if definition["type"] == "bool":
                value = widgets["input_var"].get()
            else:
                value = widgets["input_var"].get()
            new_settings[key] = value
            widgets["frame"].configure(fg_color="lightgray")
        write_settings(new_settings)
        # Optionally update app attributes, e.g.:
        self.app.no_cap = new_settings.get("no_cap", self.app.no_cap)
        try:
            self.app.graph_y_range = eval(new_settings.get("graph_y_range", str(self.app.graph_y_range)))
        except Exception as e:
            print("Error parsing graph_y_range:", e)
        try:
            self.app.graph_time_range = int(new_settings.get("graph_time_range", self.app.graph_time_range))
        except Exception as e:
            print("Error parsing graph_time_range:", e)
        self.app.accent_color = new_settings.get("accent_color", self.app.accent_color)
        # For a drop-down, update accordingly:
        self.app.color_scheme = new_settings.get("color_scheme", "System")
        self.save_apply_button.configure(state="disabled", fg_color="gray")
        self.settings_modified = False
        print("Settings saved and applied.")

    def restore_defaults(self):
        """
        Restores default settings by copying default_settings.txt into settings.txt,
        then updates the GUI widgets and applies the restored settings.
        """
        try:
            shutil.copy("default_settings.txt", "settings.txt")
            default_settings = read_settings()
            for key, widgets in self.setting_widgets.items():
                if key in default_settings:
                    definition = widgets["definition"]
                    val = default_settings[key]
                    if definition["type"] == "bool":
                        widgets["input_var"].set(self.str_to_bool(val))
                    else:
                        widgets["input_var"].set(val)
                    widgets["frame"].configure(fg_color="lightgray")
            self.save_and_apply()  # Apply the restored defaults
            print("Defaults restored.")
        except Exception as e:
            print("Error restoring defaults:", e)