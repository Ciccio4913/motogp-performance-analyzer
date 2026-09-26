import glob
import json
import os
import pandas as pd

def bestlap_to_sec(best_lap):
    if pd.isna(best_lap) or best_lap == '':
        return None
    parts = best_lap.split(":")
    mins = int(parts[0])
    sec = float(parts[1])
    return (mins * 60) + sec

selected_year = int(input("Select a season based on its year: "))

while not os.path.isdir(f"data/raw/{selected_year}"):
    print(f"The {selected_year}'s directory doesn't exist")
    selected_year = int(input("Select a season based on its year: "))

file_paths = glob.glob(f"data/raw/{selected_year}/*.json")
print("File paths lenght:", len(file_paths))
print("First file path name:", file_paths[0])

rows = []

for file_path in file_paths:
    with open(file_path, "r") as f:
        data = json.load(f)

    filename = os.path.basename(file_path)
    parts = filename.split("_")

    category = parts[0]
    year = parts[1]
    event = parts[2]
    session_type = parts[3]
    session_number = parts[4].replace(".json", "")

    for p in data['classification']:
        row = {
            "year": year,
            "event": event,
            "category": category,
            "session_type": session_type,
            "session_number": session_number,
            "position": p.get("position"),
            "rider_name": p.get("rider",  {}).get("full_name"),
            "team_name": p.get("team", {}).get("name"),
            "constructor_name": p.get("constructor", {}).get("name"),
            "average_speed": p.get("average_speed"),
            "top_speed": p.get("top_speed"),
            "best_lap": p.get("best_lap", {}).get("time"),
            "total_laps": p.get("total_laps"),
            "points": p.get("points"),
            "status": p.get("status"),
        }

        rows.append(row)

print("Total rows:", len(rows))
print(rows[-1])

df = pd.DataFrame(rows)

print("All position sorted:", sorted(df['position'].dropna().unique()))
print("All points sorted:", sorted(df['points'].dropna().unique()))
print("Total best_lap None:", df['best_lap'].isna().sum())
print(df[df['best_lap'] == ''].shape)
print(df[df['best_lap'] == ''].head())

df['year'] = df['year'].astype(int)
df['session_number'] = df["session_number"].replace('None', pd.NA)
df['session_number'] = pd.to_numeric(df["session_number"])
df['position'] = df['position'].astype('Int64')
df['best_lap_seconds'] = df['best_lap'].apply(bestlap_to_sec)

print(df[['best_lap', 'best_lap_seconds']].head(10))

print(df.shape)
print(df.columns)
print(df.head())
print(df.dtypes)

print(df[df["session_number"].isna()].head())