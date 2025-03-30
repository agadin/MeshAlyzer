import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set appearance and theme
ctk.set_appearance_mode("System")  # Options: "System", "Light", "Dark"
ctk.set_default_color_theme("blue")  # Options: "blue", "dark-blue", "green"

# Create main application window
app = ctk.CTk()
app.geometry("800x600")
app.title("CustomTkinter Graph Plot")

# Create a frame to hold the plot
plot_frame = ctk.CTkFrame(master=app)
plot_frame.pack(pady=20, padx=20, fill="both", expand=True)

# Create a matplotlib figure and add a subplot
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
ax.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], marker="o")  # A simple quadratic plot
ax.set_title("Quadratic Plot")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")

# Embed the matplotlib figure in the Tkinter frame using FigureCanvasTkAgg
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()
canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

# Start the customtkinter event loop
app.mainloop()
