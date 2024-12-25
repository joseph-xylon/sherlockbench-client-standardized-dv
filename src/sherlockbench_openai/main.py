from openai import OpenAI
import yaml
import requests
from operator import itemgetter
from .prompts import initial_messages

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

def post(base_url, run_id, path, data=None, headers=None):
    data["run-id"] = run_id

    response = requests.post(base_url + path, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def list_to_map(input_list):
    "openai doesn't like arrays much so just assign arbritray keys"
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: {"type": item} for key, item in zip(keys, input_list)}

def create_completion(client, model, **kwargs):
    return client.chat.completions.create(
        model=model,
        **kwargs
    )

def interrogate_and_verify(postfn, completionfn, attempt_id, arg_spec):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "mystery_function",
                "parameters": {
                    "type": "object",
                    "properties": list_to_map(arg_spec),
                    "required": list(list_to_map(arg_spec).keys())
                },
            },
        }
    ]

    completion = completionfn(
        messages=initial_messages,
        tools=tools
    )

    print(completion.choices[0].message.tool_calls)

def main():
    config_non_sensitive = load_config("resources/config.yaml")
    config = config_non_sensitive | load_config("resources/credentials.yaml")
    
    run_id, attempts = destructure(get(config['base-url'] + "start-run"), "run-id", "attempts")

    client = OpenAI(api_key=config['api-key'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    for attempt in attempts:
        interrogate_and_verify(postfn, completionfn, attempt["attempt-id"], attempt["fn-args"])

        
