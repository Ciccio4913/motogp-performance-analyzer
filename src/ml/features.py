import numpy as np
import pandas as pd

from common import (
    KEY, PRACTICE, PRE_RACE, PROCESSED_DIR, QUALIFYING, RACE, SPRINT, WHO, session_key,
)

FEATURES = [
    "grid_position",
    "quali_gap_pct",
    "practice_gap_pct",
    "fp1_gap_pct", "pr_gap_pct", "fp2_gap_pct", "wup_gap_pct",
    "sprint_position",
    "top_speed_rel",
    "rider_prev_avg_finish",
    "constructor_prev_avg_finish",
]

def load_seasons():
    frames = [pd.read_csv(path) for path in sorted(PROCESSED_DIR.glob("motogp_*_clean.csv"))]
    if not frames:
        raise FileNotFoundError("No clean CSV found in data/processed/: download and convert a season first")
    df = pd.concat(frames, ignore_index=True)
    df["session"] = [session_key(t, n) for t, n in zip(df["session_type"], df["session_number"])]
    return df

def _gap_pct(d, sessions, name):
    sub = d[d["session"].isin(sessions)]
    best = sub.groupby(WHO, as_index=False)["best_lap_seconds"].min()
    best["weekend_best"] = best.groupby(KEY)["best_lap_seconds"].transform("min")
    best[name] = (best["best_lap_seconds"] - best["weekend_best"]) / best["weekend_best"] * 100
    return best[WHO + [name]]

def _grid_positions(d):
    q1 = d[d["session"] == "Q1"][WHO + ["position"]].rename(columns={"position": "q1_pos"})
    q2 = d[d["session"] == "Q2"][WHO + ["position"]].rename(columns={"position": "q2_pos"})
    q2["in_q2"] = True
    grid = q2.merge(q1, on=WHO, how="outer")
    if grid.empty:
        return pd.DataFrame(columns=WHO + ["grid_position"])
    grid["in_q2"] = grid["in_q2"].eq(True)
    grid["n_q2"] = grid.groupby(KEY)["in_q2"].transform("sum")
    grid["grid_position"] = grid["q2_pos"].where(grid["in_q2"])
    outside = ~grid["in_q2"]
    order_in_q1 = grid[outside].groupby(KEY)["q1_pos"].rank(method="first")
    grid.loc[outside, "grid_position"] = order_in_q1 + grid.loc[outside, "n_q2"]
    return grid[WHO + ["grid_position"]]

def _sprint_positions(d):
    sprint = d[d["session"] == SPRINT][WHO + ["position"]]
    return sprint.rename(columns={"position": "sprint_position"})

def _top_speed_rel(d):
    sub = d[d["session"].isin(PRE_RACE)]
    speed = sub.groupby(WHO, as_index=False)["top_speed"].max()
    speed["weekend_max"] = speed.groupby(KEY)["top_speed"].transform("max")
    speed["top_speed_rel"] = (speed["top_speed"] / speed["weekend_max"] - 1) * 100
    return speed[WHO + ["top_speed_rel"]]

def _add_history(table):
    finished = table[table["race_position"].notna()]
    rider = (finished.groupby(["year", "rider_name"], as_index=False)["race_position"].mean()
             .rename(columns={"race_position": "rider_prev_avg_finish"}))
    rider["year"] += 1
    constructor = (finished.groupby(["year", "constructor_name"], as_index=False)["race_position"].mean()
                   .rename(columns={"race_position": "constructor_prev_avg_finish"}))
    constructor["year"] += 1
    table = table.merge(rider, on=["year", "rider_name"], how="left")
    return table.merge(constructor, on=["year", "constructor_name"], how="left")

def build_race_table(df, category="MotoGP"):
    d = df[df["category"] == category]
    if d.empty:
        raise ValueError(f"No data for category {category}")

    race = d[d["session"] == RACE][WHO + ["team_name", "constructor_name", "position", "status"]]
    table = race.rename(columns={"position": "race_position"}).drop_duplicates(WHO)

    for session in ("FP1", "PR", "FP2", "WUP"):
        table = table.merge(_gap_pct(d, [session], f"{session.lower()}_gap_pct"), on=WHO, how="left")
    table = table.merge(_gap_pct(d, PRACTICE, "practice_gap_pct"), on=WHO, how="left")
    table = table.merge(_gap_pct(d, QUALIFYING, "quali_gap_pct"), on=WHO, how="left")
    table = table.merge(_grid_positions(d), on=WHO, how="left")
    table = table.merge(_sprint_positions(d), on=WHO, how="left")
    table = table.merge(_top_speed_rel(d), on=WHO, how="left")
    table = _add_history(table)

    for column in FEATURES:
        if column not in table:
            table[column] = np.nan
    return table.sort_values(KEY + ["race_position"]).reset_index(drop=True)
