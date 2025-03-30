import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Create the customtkinter window
app = ctk.CTk()
app.geometry("600x400")
app.configure(bg="#242424")  # Use a hex code for consistency

# Retrieve the background color from the app
app_bg_color = app.cget("bg")

# Create a matplotlib figure and axis
fig, ax = plt.subplots()
fig.patch.set_facecolor(app_bg_color)  # Set figure background to match the app
ax.set_facecolor(app_bg_color)           # Set axis background to match the app

# Plot a simple graph
ax.plot([1, 2, 3, 4], [10, 20, 25, 30], marker='o', color='cyan')
ax.set_title("Sample Plot", color='white')  # Set title color to ensure visibility
ax.tick_params(colors='white')              # Change tick colors for visibility

# Embed the matplotlib figure in the customtkinter app
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.draw()  # Force a draw of the canvas
canvas.get_tk_widget().pack(fill="both", expand=True)

# Start the customtkinter main loop
app.mainloop()
