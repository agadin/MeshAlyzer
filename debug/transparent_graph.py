import io
import customtkinter as ctk
import matplotlib.pyplot as plt
from PIL import Image
# If you're using customtkinter v5.0 or higher, CTkImage is built in.
# Otherwise, you might need to adapt the image handling as needed.

# Set up the customtkinter window
root = ctk.CTk()
root.geometry("600x400")
root.title("Transparent Graph Demo")

# Create a matplotlib figure and axis
fig, ax = plt.subplots()

# Plot example data
ax.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], marker="o", label="Square Numbers")
ax.legend()

# Set both the figure and axes backgrounds to be transparent
fig.patch.set_alpha(0.0)
ax.set_facecolor((0, 0, 0, 0))

# Save the figure to a bytes buffer as a PNG with transparency
buf = io.BytesIO()
fig.savefig(buf, format='png', transparent=True)
buf.seek(0)

# Load the image using PIL
image = Image.open(buf)

# Create a CTkImage (this will be used in both light and dark modes)
ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(600, 400))

# Display the image in a label
label = ctk.CTkLabel(root, image=ctk_image, text="")  # text is empty so only the image is shown
label.pack(fill="both", expand=True)

root.mainloop()
