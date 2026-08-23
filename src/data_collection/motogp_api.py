import requests as req

def fetch_https_data(endpoint):
    try:
        response = req.get(endpoint, timeout=10)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except req.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
    except req.exceptions.ConnectionError:
        print(f"Connection error: Unable to reach URL")
    except req.exceptions.Timeout:
        print("Request timeout")
    except Exception as err:
        print(f"A generic error occurred: {err}")

    return None

seasons_endpoint = "https://api.motogp.pulselive.com/motogp/v1/results/seasons"
seasons = fetch_https_data(seasons_endpoint)

def select_season_by_year(year):
    for x in seasons:
        if x['year'] == year:
            return x

year = int(input("Select a season based on its year: "))
while year >= 2026 or year < 1949:
    if year == 2026:
        print("The selected year still has one season in progress")
        year = int(input("Select a season based on its year: "))
    if year > 2026 or year < 1949:
        print("The selected year is not present in the list")
        year = int(input("Select a season based on its year: "))

season_selected = select_season_by_year(year)
seasonUuid = season_selected['id']

events_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/events?seasonUuid={seasonUuid}&isFinished=true"
categories_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/categories?seasonUuid={seasonUuid}"

events = fetch_https_data(events_endpoint)
categories = fetch_https_data(categories_endpoint)

eventUuid = events[0]['id']
categoryUuid = categories[0]['id']

sessions_endpoint = f"https://api.motogp.pulselive.com/motogp/v1/results/sessions?eventUuid={eventUuid}&categoryUuid={categoryUuid}"
sessions = fetch_https_data(sessions_endpoint)

if events is not None:
    print(type(events))
    if isinstance(events, list):
        print(len(events))
        print(events[0])
    elif isinstance(events, dict):
        print(events.keys())
    
if categories is not None:
    print(type(categories))
    if isinstance(categories, list):
        print(len(categories))
        print(categories[0])
        print(categories[1])
        print(categories[2])
        print(categories[3])
    elif isinstance(categories, dict):
        print(categories.keys())

if sessions is not None:
    print(type(sessions))
    if isinstance(sessions, list):
        print(len(sessions))
        for s in sessions:
            print(s['type'], s['number'])
    elif isinstance(sessions, dict):
        print(sessions.keys())