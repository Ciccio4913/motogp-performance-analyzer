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
top10 = points_per_rider.sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 6))
bars = plt.bar(top10.index, top10.values)
plt.bar_label(bars)
plt.xticks(rotation=45, ha='right')
plt.title(f"Top 10 {category} pilots {selected_year}")
plt.ylabel("Points")
plt.tight_layout()

os.makedirs(f"visualizations/{selected_year}", exist_ok=True)
plt.savefig(f"visualizations/{selected_year}/top10_points_{category}_{selected_year}.png", dpi=150)

plt.show()