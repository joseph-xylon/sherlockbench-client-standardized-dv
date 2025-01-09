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

def add_problem_names(cursor, run_id, problem_names):
    True
