from openai import OpenAI, LengthFinishReasonError
import json
import requests
from requests import HTTPError
from operator import itemgetter
from .prompts import initial_messages, make_verification_message
from .investigate import investigate
from .verify import verify
from sherlockbench_client import load_config, destructure, get, post, AccumulatingPrinter

msg_limit = 50

def create_completion(client, model, **kwargs):
    return client.beta.chat.completions.parse(
        model=model,
        **kwargs
    )

def interrogate_and_verify(postfn, completionfn, config, attempt_id, arg_spec):
    # setup the printer
    printer = AccumulatingPrinter()

    printer.print("\n### SYSTEM: interrogating function with args", arg_spec)

    # call the LLM repeatedly until it stops calling it's tool
    messages = initial_messages.copy()
    messages, tool_call_count = investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec)

    printer.print("\n### SYSTEM: verifying function with args", arg_spec)
    verification_result = verify(config, postfn, completionfn, messages, printer, attempt_id)

def main():
    config_non_sensitive = load_config("resources/config.yaml")
    config = config_non_sensitive | load_config("resources/credentials.yaml")
    
    run_id, attempts = destructure(get(config['base-url'] + "start-run"), "run-id", "attempts")

    client = OpenAI(api_key=config['api-key'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    for attempt in attempts:
        interrogate_and_verify(postfn, completionfn, config, attempt["attempt-id"], attempt["fn-args"])

    print(postfn("complete-run", {}))
