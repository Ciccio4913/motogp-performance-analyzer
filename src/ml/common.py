from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "data" / "models"

KEY = ["year", "event"]
WHO = KEY + ["rider_name"]

PRACTICE = ["FP1", "PR", "FP2"]
QUALIFYING = ["Q1", "Q2"]
WARMUP = "WUP"
PRE_RACE = PRACTICE + QUALIFYING + [WARMUP]
SPRINT = "SPR"
RACE = "RAC"

def session_key(session_type, session_number):
    if pd.isna(session_number):
        return "Q2" if session_type == "Q" else str(session_type)
    return f"{session_type}{int(session_number)}"
