import pandas as pd
import os
import time

selected_year = int(input("Select a season based on its year: "))
csv_path = f"data/processed/motogp_{selected_year}_clean.csv"

while not os.path.exists(csv_path):
    print(f"The {selected_year}'s CSV doesn't exist")
    selected_year = int(input("Select a season based on its year: "))
    csv_path = f"data/processed/motogp_{selected_year}_clean.csv"

df = pd.read_csv(csv_path)
os.startfile(os.path.abspath(csv_path))
time.sleep(3)

df['position'] = df['position'].astype('Int64')

print(df.dtypes)

race_only = df[df['session_type'] == 'Q']
print(race_only.sort_values('best_lap_seconds').head(5))

points_per_rider = df.groupby(['category', 'rider_name'])['points'].sum()
print(points_per_rider.sort_values(ascending=False).head(10))

race_status = df[df['session_type'] == 'RAC']
not_finished = race_status[race_status['status'] != 'INSTND']
retirements_per_team = not_finished.groupby('team_name').size()
print(retirements_per_team.sort_values(ascending=False).head(10))