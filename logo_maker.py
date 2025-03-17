import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# Set figure size and remove axes
fig, ax = plt.subplots(figsize=(4,4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Draw a circle outline to represent the boundary of the mesh
circle = Circle((0.5, 0.5), 0.45, edgecolor='black', facecolor='none', linewidth=2)
ax.add_patch(circle)

# Draw a grid (mesh) pattern inside the circle.
# We'll draw horizontal and vertical lines that fall within the circle.
grid_lines = np.linspace(0.15, 0.85, 7)
for x in grid_lines:
    ax.plot([x, x], [0.15, 0.85], color='grey', linestyle='--', linewidth=1, alpha=0.7)
for y in grid_lines:
    ax.plot([0.15, 0.85], [y, y], color='grey', linestyle='--', linewidth=1, alpha=0.7)

# Additionally, draw diagonal lines to simulate a mesh
for i in np.linspace(0.15, 0.85, 5):
    ax.plot([0.15, i], [i, 0.15], color='grey', linestyle=':', linewidth=1, alpha=0.5)
    ax.plot([i, 0.85], [0.85, i], color='grey', linestyle=':', linewidth=1, alpha=0.5)

# Add the text "MeshAlyzer" below the circle
plt.text(0.5, 0.05, "MeshAlyzer", ha='center', va='center', fontsize=16, fontweight='bold')

plt.tight_layout()
plt.show()

