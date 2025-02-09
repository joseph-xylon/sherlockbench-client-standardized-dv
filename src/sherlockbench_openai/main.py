from openai import OpenAI, LengthFinishReasonError
import json
import requests
import argparse
from requests import HTTPError
from operator import itemgetter
from .prompts import initial_messages
from .investigate import investigate
from .verify import verify
from . import queries as q
from sherlockbench_client import load_config, destructure, post, AccumulatingPrinter, LLMRateLimiter
from datetime import datetime

# db
import psycopg2

msg_limit = 50

def create_completion(client, model, **kwargs):
    return client.beta.chat.completions.parse(
        model=model,
        **kwargs
    )

def investigate_and_verify(postfn, completionfn, config, attempt_id, arg_spec, run_id, cursor):
    start_time = datetime.now()
    start_api_calls = completionfn.total_call_count

    # setup the printer
    printer = AccumulatingPrinter()

    printer.print("\n### SYSTEM: interrogating function with args", arg_spec)

    messages = initial_messages.copy()
    messages, tool_call_count = investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec)

    printer.print("\n### SYSTEM: verifying function with args", arg_spec)
    verification_result = verify(config, postfn, completionfn, messages, printer, attempt_id)

    time_taken = (datetime.now() - start_time).total_seconds()
    q.add_attempt(cursor, run_id, verification_result, time_taken, tool_call_count, printer, completionfn, start_api_calls, attempt_id)

    return verification_result

def main():
    parser = argparse.ArgumentParser(description="Run SherlockBench with an optional argument.")
    parser.add_argument("arg", nargs="?", default=None, help="The id of an existing run")
    
    args = parser.parse_args()
    
    config_non_sensitive = load_config("resources/config.yaml")
    config = config_non_sensitive | load_config("resources/credentials.yaml")
    
    # connect to postgresql
    db_conn = psycopg2.connect(config["postgres-url"])
    cursor = db_conn.cursor()

    start_time = datetime.now()

    subset = config.get("subset")
    post_data = {"client-id": f"openai/{config['model']}"}

    if subset:
        post_data["subset"] = subset

    if args.arg:
        post_data["existing-run-id"] = args.arg
    
    run_id, benchmark_version, attempts = destructure(post(config['base-url'],
                                                           None,
                                                           "start-run",
                                                           post_data),
                                                      "run-id", "benchmark-version", "attempts")

    print("Starting benchmark with run-id: ", run_id)

    # we create the run table now even though we don't have all the data we need yet
    q.create_run(cursor, config_non_sensitive, run_id, benchmark_version)

    client = OpenAI(api_key=config['api-key'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    completionfn = LLMRateLimiter(rate_limit_seconds=config['rate-limit'],
                                  llmfn=completionfn,
                                  backoff_exceptions=())

    for attempt in attempts:
        investigate_and_verify(postfn, completionfn, config, attempt["attempt-id"], attempt["fn-args"], run_id, cursor)

    run_time, score, percent, problem_names = destructure(postfn("complete-run", {}), "run-time", "score", "percent", "problem-names")

    # we have the problem names now so we can add that into the db
    q.add_problem_names(cursor, problem_names)

    # save the results to the db
    q.save_run_result(cursor, run_id, start_time, score, percent, completionfn)

    # print the results
    print("\n### SYSTEM: run complete for model `" + config["model"] + "`.")
    print("Final score:", score["numerator"], "/", score["denominator"])
    print("Percent:", percent)
    
    # Why do database libraries require so much boilerplate?
    db_conn.commit()
    cursor.close()
    db_conn.close()

if __name__ == "__main__":
    main()
