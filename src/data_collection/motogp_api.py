from api_client import fetch_https_data, save_raw_json
import time

seasons_endpoint = "https://api.motogp.pulselive.com/motogp/v1/results/seasons"
seasons = fetch_https_data(seasons_endpoint)

def select_season_by_year(year):
    for x in seasons:
        if x['year'] == year:
            return x

year = int(input("Select a season based on its year: "))
while year > 2026 or year < 1949:
    if year > 2026 or year < 1949:
        print("The selected year is not present in the list")
        year = int(input("Select a season based on its year: "))

season_selected = select_season_by_year(year)
seasonUuid = season_selected['id']

events_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/events?seasonUuid={seasonUuid}&isFinished=true"
categories_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/categories?seasonUuid={seasonUuid}"

events = fetch_https_data(events_endpoint)
categories = fetch_https_data(categories_endpoint)

def build_dynamic_filename(year, event, category, session_type, session_number):
    dynamic_filename = f"{category}_{year}_{event}_{session_type}_{session_number}.json"
    return dynamic_filename

successful_save = 0
failed_calls = []

for e in events[:2]:
    if e['test'] is True:
        continue
    for c in categories:
        if c['name'] == "MotoE™":
            continue
        sessions_endpoint =  f"https://api.motogp.pulselive.com/motogp/v1/results/sessions?eventUuid={e['id']}&categoryUuid={c['id']}"
        sessions = fetch_https_data(sessions_endpoint)
        if sessions is not None:
            time.sleep(0.5)
            for s in sessions:
                ranking_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/session/{s['id']}/classification?test=false"
                ranking = fetch_https_data(ranking_endpoint)
                if ranking is not None:
                    dynamic_filename = build_dynamic_filename(year, e['short_name'], c['name'].replace("™", ""), s['type'], s['number'])
                    save_raw_json(ranking, year, dynamic_filename)
                    successful_save += 1
                    time.sleep(0.5)
                else:
                    failed_calls.append(f"Event:{e} | Category:{c} | Session:{s}\n")
        else:
            failed_calls.append(f"Event:{e} | Category:{c}\n")

print("Successful saves: ", successful_save, "\n")
print("Failed calls log: ", failed_calls)