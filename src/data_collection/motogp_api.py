import requests as req

def fetch_https_data(url):
    try:
        response = req.get(url, timeout=10)
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

def select_season_by_year(year):
    for x in res:
        if x['year'] == year:
            return x

url = "https://api.motogp.pulselive.com/motogp/v1/results/seasons"
res = fetch_https_data(url)
year = int(input("Select a season based on its year: "))

if year == 2026:
    print("The selected year still has one season in progress")

x = select_season_by_year(year)
seasonUuid = x['id']
endpoint = "https://api.motogp.pulselive.com/motogp/v1/results/events?seasonUuid=" + seasonUuid + "&isFinished=true"

if res is not None:
    print(type(res))
    if isinstance(res, list):
        print(len(res))
        print(x)
    elif isinstance(res, dict):
        print(res.keys())