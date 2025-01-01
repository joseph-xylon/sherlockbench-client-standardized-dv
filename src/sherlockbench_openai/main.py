from openai import OpenAI, LengthFinishReasonError
import yaml
import json
import requests
from requests import HTTPError
from operator import itemgetter
from pydantic import BaseModel
from .prompts import initial_messages, make_verification_message

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

def list_to_map(input_list):
    "openai doesn't like arrays much so just assign arbritray keys"
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: {"type": item} for key, item in zip(keys, input_list)}

def create_completion(client, model, **kwargs):
    return client.beta.chat.completions.parse(
        model=model,
        **kwargs
    )

def normalize_args(input_dict):
    """Converts a dict into a list of values, sorted by the alphabetical order of the keys."""
    return [input_dict[key] for key in sorted(input_dict.keys())]

def handle_tool_call(postfn, attempt_id, call):
    arguments = json.loads(call.function.arguments)
    args_norm = normalize_args(arguments)

    fnoutput = postfn("test-function", {"attempt-id": attempt_id,
                                        "args": args_norm})["output"]

    print("HANDLING TOOL CALL")
    print("args_norm: ", args_norm)
    print("fnoutput", fnoutput)

    function_call_result_message = {
        "role": "tool",
        "content": json.dumps(fnoutput),
        "tool_call_id": call.id
    }

    return function_call_result_message

def make_schema(output_type):
    mapping = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "float": float
    }

    class Prediction(BaseModel):
        """Prediction of the function output."""

        thoughts: str
        expected_output: mapping.get(output_type)

    return Prediction

def interrogate_and_verify(postfn, completionfn, attempt_id, arg_spec):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "mystery_function",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": list_to_map(arg_spec),
                    "required": list(list_to_map(arg_spec).keys()),
                    "additionalProperties": False
                },
            },
        }
    ]

    # call the LLM repeatedly until it stops calling it's tool
    messages = initial_messages.copy()
    while True:
        completion = completionfn(messages=messages, tools=tools)

        response = completion.choices[0]
        message = response.message.content
        tool_calls = response.message.tool_calls

        print("INTERROGATION MESSAGE")
        print(message)
        print()

        if tool_calls:
            messages.append({"role": "assistant",
                             "content": message,
                             "tool_calls": tool_calls})

            for call in tool_calls:
                messages.append(handle_tool_call(postfn, attempt_id, call))

        # if it didn't call the tool we can move on to verifications
        else:
            messages.append({"role": "assistant",
                             "content": message})

            break

    # now it's time for verifications
    while (v_data := postfn("next-verification", {"attempt-id": attempt_id})):
        verification = v_data["next-verification"]
        output_type = v_data["output-type"]

        vmessages = messages + [make_verification_message(verification)]

        try:
            completion = completionfn(messages=vmessages,
                                      response_format=make_schema(output_type))
        except LengthFinishReasonError as e:
            print("Caught a LengthFinishReasonError!")
            print("Completion:", e.completion)

            # well it failed so we break
            break

        response = completion.choices[0]

        thoughts, expected_output = destructure(json.loads(response.message.content), "thoughts", "expected_output")

        print("VERIFICATIONS")
        print("verification: ", verification)
        print("thoughts: ", thoughts)
        print("expected_output", expected_output)

        vstatus = postfn("attempt-verification", {"attempt-id": attempt_id,
                                                  "prediction": expected_output})["status"]

        if vstatus in ("done", "wrong"):
            break


def main():
    config_non_sensitive = load_config("resources/config.yaml")
    config = config_non_sensitive | load_config("resources/credentials.yaml")
    
    run_id, attempts = destructure(get(config['base-url'] + "start-run"), "run-id", "attempts")

    client = OpenAI(api_key=config['api-key'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    for attempt in attempts:
        interrogate_and_verify(postfn, completionfn, attempt["attempt-id"], attempt["fn-args"])

    print(postfn("complete-run", {}))
