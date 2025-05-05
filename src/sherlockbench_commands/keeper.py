import argparse
import psycopg2
from pypika import Query, Table
import sys
import uuid
from sherlockbench_client.main import load_config
from sherlockbench_client.run_utils import is_valid_uuid


def set_keeper(cursor, run_id):
    """
    Set the 'keeper' column to True for a run in the database.
    
    Args:
        cursor: Database cursor
        run_id: The UUID of the run to mark as a keeper
    
    Returns:
        bool: True if the run was found and updated, False otherwise
    """
    runs = Table("runs")
    
    # First check if the run exists
    check_query = (
        Query.from_(runs)
        .select(runs.id)
        .where(runs.id == str(run_id))
    )
    
    cursor.execute(str(check_query))
    result = cursor.fetchone()
    
    if not result:
        return False
    
    # Update the keeper column
    update_query = (
        Query.update(runs)
        .set(runs.keeper, True)
        .where(runs.id == str(run_id))
    )
    
    cursor.execute(str(update_query))
    cursor.connection.commit()
    
    return True


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mark runs as keepers in the database.")
    parser.add_argument("run_ids", nargs="+", help="UUID(s) of the run(s) to mark as keepers")
    
    args = parser.parse_args()
    run_ids = args.run_ids
    
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
            # Set the keeper flag
            success = set_keeper(cursor, run_id)
            
            if success:
                print(f"Marked run '{run_id}' as a keeper")
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
