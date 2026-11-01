from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

API_BASE = "https://api.motogp.pulselive.com/motogp/v1/results"
USER_AGENT = "MotoGPPerformanceAnalyzer/0.1 (student portfolio project)"

MAX_WORKERS = 4
REQUEST_DELAY = 0.1
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

FIRST_SEASON = 1949
EXCLUDED_CATEGORIES = ("MotoE",)