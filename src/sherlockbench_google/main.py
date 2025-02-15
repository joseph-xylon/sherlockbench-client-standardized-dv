from google import genai
from sherlockbench_client import destructure, post, AccumulatingPrinter, LLMRateLimiter, q, start_run, complete_run

def main():
    config, db_conn, cursor, run_id, attempts, start_time = start_run("openai")

    client = genai.Client(api_key=config['api-keys']['google'])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Explain how AI works",
    )

    print(response.text)
