import argparse
import sys

import psycopg2
from pypika import Query, Table

from sherlockbench_client.main import load_config
from sherlockbench_client.run_api import is_valid_uuid


def add_label(cursor, run_id, label_value):
    """
    Add a label to the 'labels' array for a run in the database.

    Args:
        cursor: Database cursor
        run_id: The UUID of the run to label
        label_value: String value to add as a label

    Returns:
        bool: True if the run was found and updated, False otherwise
    """
    # First check if the run exists
    check_query = """
    SELECT id FROM runs WHERE id = %s
    """
    cursor.execute(check_query, (str(run_id),))
    result = cursor.fetchone()

    if not result:
        return False

    # Update the labels column by appending the new label
    # Only append if the label doesn't already exist in the array
    update_query = """
    UPDATE runs
    SET labels =
        CASE
            WHEN labels IS NULL THEN ARRAY[%s]
            WHEN %s = ANY(labels) THEN labels
            ELSE array_append(labels, %s)
        END
    WHERE id = %s
    """
    cursor.execute(update_query, (label_value, label_value, label_value, str(run_id)))
    cursor.connection.commit()

    return True


def remove_label(cursor, run_id, label_value):
    """
    Remove a label from the 'labels' array for a run in the database.

    Args:
        cursor: Database cursor
        run_id: The UUID of the run to update
        label_value: String value to remove from labels

    Returns:
        bool: True if the run was found and updated, False otherwise
    """
    # First check if the run exists
    check_query = """
    SELECT id FROM runs WHERE id = %s
    """
    cursor.execute(check_query, (str(run_id),))
    result = cursor.fetchone()

    if not result:
        return False

    # Update the labels column by removing the specified label
    update_query = """
    UPDATE runs
    SET labels = array_remove(labels, %s)
    WHERE id = %s
    """
    cursor.execute(update_query, (label_value, str(run_id)))
    cursor.connection.commit()

    return True


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Manage labels for runs in the database.")

    # Create a group for mutually exclusive label operations
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", "-a", dest="add_label", help="Label to add to the run(s)")
    group.add_argument("--remove", "-r", dest="remove_label", help="Label to remove from the run(s)")

    parser.add_argument("run_ids", nargs="+", help="UUID(s) of the run(s) to modify")

    args = parser.parse_args()
    run_ids = args.run_ids
    add_label_value = args.add_label
    remove_label_value = args.remove_label

    # Keep track of results
    success_count = 0
    not_found_count = 0
    invalid_uuids = []

    # Validate all run_ids are UUIDs
    for run_id in run_ids:
        if not is_valid_uuid(run_id):
            invalid_uuids.append(run_id)

    if invalid_uuids:
        print(f"Error: The following IDs are not valid UUIDs: {', '.join(invalid_uuids)}")
        sys.exit(1)

    try:
        # Load configuration to get database connection info
        config = load_config("resources/credentials.yaml")

        # Connect to postgresql
        db_conn = psycopg2.connect(config["postgres-url"])
        cursor = db_conn.cursor()

        # Process each run ID
        for run_id in run_ids:
            if add_label_value:
                # Add the label
                success = add_label(cursor, run_id, add_label_value)
                if success:
                    print(f"Added label '{add_label_value}' to run '{run_id}'")
                    success_count += 1
                else:
                    print(f"Warning: Run '{run_id}' not found in the database")
                    not_found_count += 1
            elif remove_label_value:
                # Remove the label
                success = remove_label(cursor, run_id, remove_label_value)
                if success:
                    print(f"Removed label '{remove_label_value}' from run '{run_id}'")
                    success_count += 1
                else:
                    print(f"Warning: Run '{run_id}' not found in the database")
                    not_found_count += 1

        # Only exit with error if all runs failed
        if success_count == 0 and not_found_count > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db_conn' in locals() and db_conn:
            db_conn.close()


if __name__ == "__main__":
    main()
