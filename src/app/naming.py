import re

def clean_part(value):
    text = str(value).replace("™", "")
    text = re.sub(r'[<>:"/\\|?*_\s]+', "-", text).strip("-")
    return text or "NA"

def event_code(event):
    return event.get("short_name") or str(event.get("id", ""))[:8] or "NA"

def build_filename(category, year, event, session_type, session_number):
    parts = [category, year, event, session_type, session_number]
    return "_".join(clean_part(part) for part in parts) + ".json"