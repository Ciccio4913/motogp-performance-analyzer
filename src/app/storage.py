import shutil

from config import PROCESSED_DIR, RAW_DIR

def raw_dir(year):
    return RAW_DIR / str(year)

def csv_path(year):
    return PROCESSED_DIR / f"motogp_{year}_clean.csv"

def documents_path(year):
    return PROCESSED_DIR / f"motogp_{year}_documents.csv"

def raw_file_count(year):
    folder = raw_dir(year)
    return len(list(folder.glob("*.json"))) if folder.is_dir() else 0

def has_raw(year):
    return raw_file_count(year) > 0

def has_csv(year):
    return csv_path(year).exists()

def has_documents(year):
    return documents_path(year).exists()

def years_with_raw():
    if not RAW_DIR.is_dir():
        return []
    years = [
        int(path.name)
        for path in RAW_DIR.iterdir()
        if path.is_dir() and path.name.isdigit() and has_raw(int(path.name))
    ]
    return sorted(years, reverse=True)

def years_with_csv():
    if not PROCESSED_DIR.is_dir():
        return []
    years = []
    for path in PROCESSED_DIR.glob("motogp_*_clean.csv"):
        year_text = path.stem.split("_")[1]
        if year_text.isdigit():
            years.append(int(year_text))
    return sorted(years, reverse=True)

def deletable_raw_years():
    return [year for year in years_with_raw() if has_csv(year)]

def delete_raw(year):
    shutil.rmtree(raw_dir(year), ignore_errors=True)

def delete_csv(year):
    for path in (csv_path(year), documents_path(year)):
        path.unlink(missing_ok=True)