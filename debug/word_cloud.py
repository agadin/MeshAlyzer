import random
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Step 1: Define your labels
labels = [
    "Time", "LPS Pressure", "LPS Temperature",
    "Pressure Sensor 0", "Converted Pressure 0",
    "Pressure Sensor 1", "Converted Pressure 1",
    "Pressure Sensor 2", "Converted Pressure 2",
    "Pressure Sensor 3", "Valve 1 State", "Valve 2 State",
    "Target Pressure", "Target Time", "Clamp State", "Protocol Step"
]


# Step 2: Assign random frequencies to each phrase
def generate_random_frequencies(labels, min_val=10, max_val=100):
    return {label: random.randint(min_val, max_val) for label in labels}


frequencies = generate_random_frequencies(labels)


# Step 3: Define a custom color function with two alternating colors
class TwoColorFunc:
    def __init__(self, color1, color2):
        self.colors = [color1, color2]

    def __call__(self, *args, **kwargs):
        return random.choice(self.colors)


color_func = TwoColorFunc("#0f4537", "#6b0014")

# Step 4: Generate the word cloud
wordcloud = WordCloud(
    width=1600,
    height=600,
    background_color='white',
    prefer_horizontal=1.0,
    collocations=False
).generate_from_frequencies(frequencies)

# Step 5: Apply the custom color function
wordcloud.recolor(color_func=color_func)

# Step 6: Save as a high-res image
plt.figure(figsize=(10, 4), dpi=500)
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.savefig("word_cloud_poster_highres.png", bbox_inches='tight', pad_inches=0)
plt.close()
