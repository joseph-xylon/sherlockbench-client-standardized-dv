import argparse
import sys
from sherlockbench_client.main import load_config, get


def main():
    parser = argparse.ArgumentParser(description="List available problem sets.")
    parser.parse_args()

    try:
        # Load configuration
        config = load_config("resources/config.yaml")
        
        # Get problem sets from the server
        response = get(config['base-url'], "problem-sets")
        problem_sets = response.get('problem-sets', {})

        print("Available problem sets:")
        print("======================")

        for category, problems in problem_sets.items():
            print(f"\n{category}:")
            for problem in problems:
                print(f"  - {problem['name']} :: {problem['id']}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
