import matplotlib.pyplot as plt

from charts import (
    PROJECT_ROOT,
    available_categories,
    available_years,
    constructor_points_chart,
    load_season,
    retirements_chart,
    top_riders_chart,
)

years = available_years()
selected_year = int(input(f"Select a season {years}: "))

while selected_year not in years:
    print(f"The {selected_year}'s CSV doesn't exist")
    selected_year = int(input(f"Select a season {years}: "))

df = load_season(selected_year)

output_dir = PROJECT_ROOT / "visualizations" / str(selected_year)
output_dir.mkdir(parents=True, exist_ok=True)

for category in available_categories(df):
    charts = {
        "top10_points": top_riders_chart(df, category, selected_year),
        "constructor_points": constructor_points_chart(df, category, selected_year),
        "retirements": retirements_chart(df, category, selected_year),
    }
    for name, fig in charts.items():
        fig.savefig(output_dir / f"{name}_{category}_{selected_year}.png", dpi=150)
        plt.close(fig)
    print(f"Saved 3 charts for {category} {selected_year}")