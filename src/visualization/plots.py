from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import pandas as pd
import os

selected_year = int(input("Select a season based on its year: "))
csv_path = f"data/processed/motogp_{selected_year}_clean.csv"

while not os.path.exists(csv_path):
    print(f"The {selected_year}'s CSV doesn't exist")
    selected_year = int(input("Select a season based on its year: "))
    csv_path = f"data/processed/motogp_{selected_year}_clean.csv"

df = pd.read_csv(csv_path)

df['position'] = df['position'].astype('Int64')

category = "MotoGP"
category_only = df[df['category'] == category]
points_per_rider = category_only.groupby(['rider_name'])['points'].sum()
constructor_of_rider = category_only.groupby('rider_name')['constructor_name'].first()

color_map = {"Aprilia": "white", "Ducati": "red", "KTM": "orange", "Yamaha": "blue", "Honda": "black"}

top10 = points_per_rider.sort_values(ascending=False).head(10)

bar_colors = []
legend_items = {}
for rider in top10.index:
    constructor = constructor_of_rider[rider]
    color = color_map.get(constructor, "gray")
    legend_items[constructor] = color
    bar_colors.append(color)

patch_list = []
for name, color in legend_items.items():
    patch = Patch(facecolor=color, edgecolor="black", label=name)
    patch_list.append(patch)

plt.figure(figsize=(10, 6))
bars = plt.bar(top10.index, top10.values, color=bar_colors, edgecolor="black")
plt.bar_label(bars)
plt.xticks(rotation=45, ha='right')
plt.title(f"Top 10 {category} pilots {selected_year}")
plt.ylabel("Points")
plt.legend(handles=patch_list, title="Constructor")
plt.tight_layout()

os.makedirs(f"visualizations/{selected_year}", exist_ok=True)
plt.savefig(f"visualizations/{selected_year}/top10_points_{category}_{selected_year}.png", dpi=150)

plt.show()