# Re-run the simulation with a square wave target pressure and improved actual response
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

# Simulation parameters
time_steps = 200  # Total time steps
cycle_length = 50  # Time steps per cycle
min_pressure = 101  # in kPa
max_pressure = 1036  # in kPa

# Generate square wave target pressure
time = np.arange(time_steps)
target_pressure = np.where((time // (cycle_length // 2)) % 2 == 0, min_pressure, max_pressure)

# Simulate actual pressure response with a more pronounced initial spike
actual_pressure = np.zeros_like(target_pressure)
for i in range(1, len(actual_pressure)):
    if target_pressure[i] > actual_pressure[i - 1]:  # Increasing phase
        if actual_pressure[i - 1] < target_pressure[i] * 0.85:
            actual_pressure[i] = actual_pressure[i - 1] + random.uniform(50, 100)  # Very fast initial rise
        elif actual_pressure[i - 1] < target_pressure[i] * 0.95:
            actual_pressure[i] = actual_pressure[i - 1] + random.uniform(20, 50)  # Moderate climb
        else:
            actual_pressure[i] = actual_pressure[i - 1] + random.uniform(5, 10)  # Fine-tuning to target
    else:  # Decreasing phase
        actual_pressure[i] = actual_pressure[i - 1] - random.uniform(40, 80)  # Faster decrease

    # Add slight random noise
    actual_pressure[i] += random.uniform(-5, 5)

# Create an animation
fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size here
ax.set_xlim(0, time_steps)
ax.set_ylim(min_pressure - 10, max_pressure + 10)
ax.set_xlabel("Time Steps")
ax.set_ylabel("Pressure (kPa)")
ax.set_title("Balloon Pressure Target vs. Actual Response")

target_line, = ax.plot([], [], 'r-', label="Target Pressure")
actual_line, = ax.plot([], [], 'b-', label="Actual Pressure")
ax.legend(loc='upper right')  # Lock the legend to the top right

def init():
    target_line.set_data([], [])
    actual_line.set_data([], [])
    return target_line, actual_line

def update(frame):
    target_line.set_data(time[:frame], target_pressure[:frame])
    actual_line.set_data(time[:frame], actual_pressure[:frame])
    return target_line, actual_line

ani = animation.FuncAnimation(fig, update, frames=time_steps, init_func=init, blit=True)

# Save the animation as a GIF
gif_filename = "./balloon_pressure_simulation.gif"
ani.save(gif_filename, writer='pillow', fps=20)

# Extract the final frame data
final_frame = time_steps - 1
final_target_pressure = target_pressure[:final_frame]
final_actual_pressure = actual_pressure[:final_frame]

# Plot the final frame
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, time_steps)
ax.set_ylim(min_pressure - 10, max_pressure + 10)
ax.set_xlabel("Time Steps")
ax.set_ylabel("Pressure (kPa)")
ax.set_title("Balloon Pressure Target vs. Actual Response")

ax.plot(time[:final_frame], final_target_pressure, 'r-', label="Target Pressure")
ax.plot(time[:final_frame], final_actual_pressure, 'b-', label="Actual Pressure")
ax.legend(loc='upper right')

# Save the final frame as a PNG file
png_filename = "./balloon_pressure_final_frame.png"
fig.savefig(png_filename)