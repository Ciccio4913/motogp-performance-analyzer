from pathlib import Path
from matplotlib.patches import Patch

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CATEGORY_ORDER = ["MotoGP", "Moto2", "Moto3"]

BASE_COLORS = {
    "Aprilia": "white",
    "Ducati": "red",
    "KTM": "orange",
    "Yamaha": "blue",
    "Honda": "black",
}

FALLBACK_COLORS = ["tab:green", "tab:purple", "tab:brown", "tab:pink", "tab:cyan", "tab:olive"]

def available_years():
    years = []
    for path in PROCESSED_DIR.glob("motogp_*_clean.csv"):
        year_text = path.stem.split("_")[1]
        years.append(int(year_text))
    return sorted(years)

def load_season(year):
    df = pd.read_csv(PROCESSED_DIR / f"motogp_{year}_clean.csv")
    df["position"] = df["position"].astype("Int64")
    return df

def available_categories(df):
    present = set(df["category"].unique())
    return [category for category in CATEGORY_ORDER if category in present]

def build_color_lookup(constructors):
    lookup = {}
    fallback = iter(FALLBACK_COLORS)
    for name in sorted(constructors):
        if name in BASE_COLORS:
            lookup[name] = BASE_COLORS[name]
        else:
            lookup[name] = next(fallback, "gray")
    return lookup

def _empty_figure(message):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14)
    ax.axis("off")
    return fig

def top_riders_chart(df, category, year, n=10):
    data = df[df["category"] == category]
    points_per_rider = data.groupby("rider_name")["points"].sum()
    top = points_per_rider.sort_values(ascending=False).head(n)

    if top.empty:
        return _empty_figure(f"No data for {category} {year}")

    constructor_of_rider = data.groupby("rider_name")["constructor_name"].first()
    colors = build_color_lookup(data["constructor_name"].unique())

    bar_colors = []
    legend_items = {}
    for rider in top.index:
        constructor = constructor_of_rider[rider]
        color = colors[constructor]
        legend_items[constructor] = color
        bar_colors.append(color)

    patch_list = []
    for name, color in legend_items.items():
        patch_list.append(Patch(facecolor=color, edgecolor="black", label=name))

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(top.index, top.values, color=bar_colors, edgecolor="black")
    ax.bar_label(bars)
    ax.margins(y=0.1)
    ax.set_title(f"Top {len(top)} {category} riders by points - {year}")
    ax.set_ylabel("Points")
    ax.legend(handles=patch_list, title="Constructor")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig

def constructor_points_chart(df, category, year):
    data = df[df["category"] == category]
    points = data.groupby("constructor_name")["points"].sum().sort_values(ascending=False)

    if points.empty or points.sum() == 0:
        return _empty_figure(f"No points for {category} {year}")

    share = points / points.sum() * 100
    colors = build_color_lookup(points.index)

    bar_colors = []
    labels = []
    for name in points.index:
        bar_colors.append(colors[name])
        labels.append(f"{points[name]:g}\n({share[name]:.0f}%)")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(points.index, points.values, color=bar_colors, edgecolor="black")
    ax.bar_label(bars, labels=labels)
    ax.margins(y=0.12)
    ax.set_title(f"Rider points by constructor - {category} {year}")
    ax.set_ylabel("Points")
    fig.tight_layout()
    return fig

def retirements_chart(df, category, year, n=10):
    races = df[(df["category"] == category) & (df["session_type"] == "RAC")]
    not_finished = races[races["status"] != "INSTND"]
    per_team = not_finished.groupby("team_name").size().sort_values(ascending=False).head(n)

    if per_team.empty:
        return _empty_figure(f"No race non-finishes for {category} {year}")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(per_team.index, per_team.values, color="tab:red", edgecolor="black")
    ax.bar_label(bars)
    ax.invert_yaxis()
    ax.set_title(f"Race non-finishes by team - {category} {year}")
    ax.set_xlabel("Non-finishes")
    fig.tight_layout()
    return fig