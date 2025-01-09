from pypika import Query, Table
from datetime import datetime
import json

def create_run(cursor, config_non_sensitive, run_id, benchmark_version):
    start_time = datetime.now()
    run_data = {"id": run_id,
                "model_identifier": config_non_sensitive["model"],
                "benchmark_version": benchmark_version.split('.', 1)[0],
                "config": json.dumps(config_non_sensitive),
                "datetime_start": start_time.strftime('%Y-%m-%d %H:%M:%S')
                }

    runs = Table("runs")
    insert_query = Query.into(runs).columns(*run_data.keys()).insert(*run_data.values())
    cursor.execute(str(insert_query))

def add_attempt(cursor, run_id, verification_result, time_taken, tool_call_count, printer, completionfn, start_api_calls, attempt_id):
    attempt_data = {"id": attempt_id,
                    "run_id": run_id,
                    "result": verification_result,
                    "time_taken": time_taken,
                    "tool_calls": tool_call_count,
                    "complete_log": printer.retrieve(),
                    "api_calls": completionfn.total_call_count - start_api_calls}

    insert_query = Query.into(Table("attempts")).columns(*attempt_data.keys()).insert(*attempt_data.values())
    cursor.execute(str(insert_query))

def add_problem_names(cursor, run_id, problem_names):
    True

