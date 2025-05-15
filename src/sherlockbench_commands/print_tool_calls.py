import argparse
import psycopg2
import sys
import uuid
import re
from sherlockbench_client.main import load_config
from sherlockbench_client.run_api import is_valid_uuid


def get_attempt_log(cursor, attempt_id):
    """
    Retrieves the complete_log for a specified attempt ID.

    Args:
        cursor: Database cursor
        attempt_id: The UUID of the attempt

    Returns:
        tuple: (log, function_name) where log is the complete_log text and function_name is the name of the function
               Returns (None, None) if attempt not found
    """
    query = """
    SELECT complete_log, function_name FROM attempts WHERE id = %s
    """
    cursor.execute(query, (str(attempt_id),))
    result = cursor.fetchone()

    if not result:
        return None, None

    return result[0], result[1]

def parse_tool_calls(log_text):
    # Split the log by "### SYSTEM: calling tool" marker
    tool_call_blocks = re.split(r'\n\s*### SYSTEM: calling tool\n', log_text)

    parsed_calls = []
    for block in tool_call_blocks:
        # Extract content until the next empty line or the end of tool calls
        content_match = re.split(r'\n\s*\n', block, 1)[0]
        if content_match:
            lines = [line.strip() for line in content_match.strip().split('\n')]

            if lines:
                parsed_calls.extend(lines)

    return parsed_calls

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Print the complete log for a specific attempt.")
    parser.add_argument("attempt_id", help="UUID of the attempt to print the log for")

    args = parser.parse_args()
    attempt_id = args.attempt_id

    assert is_valid_uuid(attempt_id)

    # Load configuration to get database connection info
    config = load_config("resources/credentials.yaml")

    # Connect to postgresql
    db_conn = psycopg2.connect(config["postgres-url"])
    cursor = db_conn.cursor()

    # Get the attempt log
    log, function_name = get_attempt_log(cursor, attempt_id)

    assert log

    print(f"=== Log for attempt '{attempt_id}' (function: {function_name}) ===\n")

    # Print the log
    calls = parse_tool_calls(log)

    for call in calls:
        print(call)

    cursor.close()
    db_conn.close()

if __name__ == "__main__":
    main()
