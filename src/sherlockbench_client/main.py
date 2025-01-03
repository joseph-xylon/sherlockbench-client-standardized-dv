import yaml
import requests
from requests import HTTPError


def load_config(filepath):
    with open(filepath, "r") as file:
        config = yaml.safe_load(file)

    # Ensure "debug" is always a list
    if "debug" in config:
        if config["debug"] is None:
            config["debug"] = []

    return config

def destructure(dictionary, *keys):
    """it boggles my mind that Python doesn't have destructuring"""
    return (dictionary[key] for key in keys)

def get(url, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an error for HTTP issues
    return response.json()

def post(base_url, run_id, path, data):
    data["run-id"] = run_id

    try:
        response = requests.post(base_url + path, json=data)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")

        if response.json()["error"] == "your arguments don't comply with the schema":
            return {"output": "your arguments don't comply with the schema"}
        
    return response.json()

