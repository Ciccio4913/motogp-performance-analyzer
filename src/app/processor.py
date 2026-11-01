import json

import numpy as np
import pandas as pd

import storage
from config import PROCESSED_DIR, RAW_DIR
from naming import event_code

def bestlap_to_seconds(best_lap):
    if pd.isna(best_lap) or best_lap == "":
        return None
    try:
        minutes, seconds = best_lap.split(":")
        return round(int(minutes) * 60 + float(seconds), 3)
    except ValueError:
        return None

def _field(item, key, field):
    return (item.get(key) or {}).get(field)

def _rows_from_file(path):
    parts = path.stem.split("_")
    if len(parts) != 5:
        return []
    category, year, event, session_type, session_number = parts
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    rows = []
    for p in data.get("classification") or []:
        rows.append({
            "year": year,
            "event": event,
            "category": category,
            "session_type": session_type,
            "session_number": session_number,
            "position": p.get("position"),
            "rider_name": _field(p, "rider", "full_name"),
            "team_name": _field(p, "team", "name"),
            "constructor_name": _field(p, "constructor", "name"),
            "average_speed": p.get("average_speed"),
            "top_speed": p.get("top_speed"),
            "best_lap": _field(p, "best_lap", "time"),
            "total_laps": p.get("total_laps"),
            "points": p.get("points"),
            "status": p.get("status"),
        })
    return rows

def clean_dataframe(df):
    df = df.copy()
    df["year"] = df["year"].astype(int)
    df["session_number"] = pd.to_numeric(df["session_number"], errors="coerce")
    df["position"] = pd.to_numeric(df["position"], errors="coerce").round().astype("Int64")
    for column in ("average_speed", "top_speed", "points"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["average_speed"] = df["average_speed"].replace(0, np.nan)
    df["top_speed"] = df["top_speed"].replace(0, np.nan)
    df["total_laps"] = pd.to_numeric(df["total_laps"], errors="coerce").astype("Int64")
    df["best_lap_seconds"] = pd.to_numeric(df["best_lap"].apply(bestlap_to_seconds), errors="coerce")
    return df

def build_documents_index(year):
    rows = []
    for path in sorted((RAW_DIR / str(year) / "sessions").glob("*.json")):
        try:
            sessions = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for session in sessions or []:
            event = session.get("event") or {}
            category = (session.get("category") or {}).get("name", "").replace("™", "")
            for document, info in (session.get("session_files") or {}).items():
                url = (info or {}).get("url")
                if not url:
                    continue
                rows.append({
                    "year": year,
                    "event": event_code(event),
                    "event_name": event.get("name"),
                    "category": category,
                    "session_type": session.get("type"),
                    "session_number": session.get("number"),
                    "date": session.get("date"),
                    "document": document,
                    "url": url,
                })
    if not rows:
        return 0
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values("date").to_csv(storage.documents_path(year), index=False)
    return len(rows)

def convert_season(year, progress=None, cancel=None):
    report = progress or (lambda percent, message: None)
    files = sorted(storage.raw_dir(year).glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files for {year}: download them first")

    rows, bad_files = [], 0
    for index, path in enumerate(files, 1):
        try:
            rows.extend(_rows_from_file(path))
        except (json.JSONDecodeError, OSError):
            bad_files += 1
        if index % 10 == 0 or index == len(files):
            report(int(90 * index / len(files)), f"Reading JSON {index}/{len(files)}")
    if not rows:
        raise ValueError(f"The JSON files for {year} contain no classification rows")

    report(92, "Cleaning data...")
    df = clean_dataframe(pd.DataFrame(rows))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(storage.csv_path(year), index=False)

    report(96, "Building the documents index...")
    documents = build_documents_index(year)
    report(100, "Done")
    return {"rows": len(df), "documents": documents, "bad_files": bad_files}