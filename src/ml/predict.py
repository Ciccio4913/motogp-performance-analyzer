import joblib
import pandas as pd

from common import PROCESSED_DIR, KEY
from evaluation import race_metrics
from features import build_race_table, load_seasons
from train import model_path

def load_bundle(category):
    path = model_path(category)
    return joblib.load(path) if path.exists() else None

def build_table(category):
    return build_race_table(load_seasons(), category)

def events_in_year(table, year):
    codes = list(table.loc[table["year"] == year, "event"].unique())
    names, dates = {}, {}
    documents = PROCESSED_DIR / f"motogp_{year}_documents.csv"
    if documents.exists():
        docs = pd.read_csv(documents)
        names = docs.drop_duplicates("event").set_index("event")["event_name"].to_dict()
        dates = docs.groupby("event")["date"].min().to_dict()
    codes.sort(key=lambda code: (str(dates.get(code, "")), code))
    return [(code, f"{code} - {str(names[code]).title()}" if code in names else code) for code in codes]

def predict_event(table, bundle, year, event):
    race = table[(table["year"] == year) & (table["event"] == event)].copy()
    race["score"] = bundle["model"].predict(race[bundle["features"]])
    race["predicted_rank"] = race["score"].rank(method="first").astype(int)
    race["in_training"] = year in bundle["trained_years"]
    return race.sort_values("predicted_rank"), race_metrics(race)
