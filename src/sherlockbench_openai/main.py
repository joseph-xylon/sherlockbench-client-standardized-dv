from openai import OpenAI, LengthFinishReasonError
import json
import requests
from requests import HTTPError
from operator import itemgetter
from .prompts import initial_messages
from .investigate import investigate
from .verify import verify
from . import queries as q
from sherlockbench_client import load_config, destructure, get, post, AccumulatingPrinter
from datetime import datetime

# db
import psycopg2

msg_limit = 50

def create_completion(client, model, **kwargs):
    return client.beta.chat.completions.parse(
        model=model,
        **kwargs
    )

def investigate_and_verify(postfn, completionfn, config, attempt_id, arg_spec):
    # setup the printer
    printer = AccumulatingPrinter()

    printer.print("\n### SYSTEM: interrogating function with args", arg_spec)

    messages = initial_messages.copy()
    messages, tool_call_count = investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec)

    printer.print("\n### SYSTEM: verifying function with args", arg_spec)
    verification_result = verify(config, postfn, completionfn, messages, printer, attempt_id)

def main():
    config_non_sensitive = load_config("resources/config.yaml")
    config = config_non_sensitive | load_config("resources/credentials.yaml")
    
    # connect to postgresql
    db_conn = psycopg2.connect(config["postgres-url"])
    cursor = db_conn.cursor()

    subset = config.get("subset")
    run_id, benchmark_version, attempts = destructure(get(config['base-url'] + (f"start-run?subset={subset}" if subset else "start-run")), "run-id", "benchmark-version", "attempts")

    # we create the run table now even though we don't have all the data we need yet
    q.create_run(cursor, config_non_sensitive, run_id, benchmark_version)

    client = OpenAI(api_key=config['api-key'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    for attempt in attempts:
        investigate_and_verify(postfn, completionfn, config, attempt["attempt-id"], attempt["fn-args"])

    run_time, score, percent, problem_names = destructure(postfn("complete-run", {}), "run-time", "score", "percent", "problem-names")

    print("\n### SYSTEM: run complete for model `" + config["model"] + "`.")
    print("Final score:", score["numerator"], "/", score["denominator"])
    print("Percent:", percent)
    print("Wrong answers:")
    
    # we have the problem names now so we can add that into the db
    # problem_names is a list of dicts containing "id" and "function_name"
    #q.add_problem_names(cursor, run_id, problem_names)
    

    # Why do database libraries require so much boilerplate?
    db_conn.commit()
    cursor.close()
    db_conn.close()

if __name__ == "__main__":
    main()
