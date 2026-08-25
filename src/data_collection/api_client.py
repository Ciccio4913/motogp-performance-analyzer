import requests
import json
import os

def fetch_https_data(endpoint):
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
    except requests.exceptions.ConnectionError:
        print(f"Connection error: Unable to reach URL")
    except requests.exceptions.Timeout:
        print("Request timeout")
    except Exception as err:
        print(f"A generic error occurred: {err}")

    return None

def save_raw_json(data, year, filename):
    os.makedirs(f"data/raw/{year}", exist_ok=True)
    with open(f"data/raw/{year}/{filename}", "w") as f:
        json.dump(data, f, indent=2)