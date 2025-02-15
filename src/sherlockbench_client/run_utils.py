from .main import load_config, destructure, post
from . import queries as q
import argparse
from datetime import datetime
import psycopg2

def start_run(provider):
    """Various things to get the run started:
       - parse the args
       - load the config
       - establish db connection
       - contact the server to start the run
       - add the run info to the db
    """

    parser = argparse.ArgumentParser(description="Run SherlockBench with an optional argument.")
    parser.add_argument("arg", nargs="?", default=None, help="The id of an existing run")

    args = parser.parse_args()

    config_raw = load_config("resources/config.yaml")
    config_non_sensitive = {k: v for k, v in config_raw.items() if k != "providers"} | config_raw["providers"][provider]
    config = config_non_sensitive | load_config("resources/credentials.yaml")

    # connect to postgresql
    db_conn = psycopg2.connect(config["postgres-url"])
    cursor = db_conn.cursor()

    subset = config.get("subset")  # none if key is missing
    post_data = {"client-id": f"{provider}/{config['model']}"}

    if subset:
        post_data["subset"] = subset

    if args.arg:
        post_data["existing-run-id"] = args.arg
    
    run_id, run_type, benchmark_version, attempts = destructure(post(config['base-url'],
                                                                     None,
                                                                     "start-run",
                                                                     post_data),
                                                                "run-id", "run-type", "benchmark-version", "attempts")

    print(f"Starting {run_type} benchmark with run-id: {run_id}")

    config_non_sensitive["run_type"] = run_type

    # we create the run table now even though we don't have all the data we need yet
    q.create_run(cursor, config_non_sensitive, run_id, benchmark_version)
    
    return (config, db_conn, cursor, run_id, attempts, datetime.now())

def complete_run(postfn, db_conn, cursor, run_id, start_time, total_call_count, config):
    run_time, score, percent, problem_names = destructure(postfn("complete-run", {}), "run-time", "score", "percent", "problem-names")

    # we have the problem names now so we can add that into the db
    q.add_problem_names(cursor, problem_names)

    # save the results to the db
    q.save_run_result(cursor, run_id, start_time, score, percent, total_call_count)

    # print the results
    print("\n### SYSTEM: run complete for model `" + config["model"] + "`.")
    print("Final score:", score["numerator"], "/", score["denominator"])
    print("Percent:", percent)
    
    # Why do database libraries require so much boilerplate?
    db_conn.commit()
    cursor.close()
    db_conn.close()
