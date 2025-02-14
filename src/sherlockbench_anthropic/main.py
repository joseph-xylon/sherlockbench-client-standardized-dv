import anthropic
from sherlockbench_client import destructure, post, AccumulatingPrinter, LLMRateLimiter, q, start_run

from .prompts import initial_messages
from .investigate import investigate
from .verify import verify

from datetime import datetime
import argparse

def create_completion(client, model, **kwargs):
    """closure to pre-load the model"""
    return client.messages.create(
        model=model,
        **kwargs
    )

def main():
    config, db_conn, cursor, run_id, attempts = start_run("anthropic")

    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=config['api-keys']['anthropic'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    completionfn = LLMRateLimiter(rate_limit_seconds=config['rate-limit'],
                                  llmfn=completionfn,
                                  backoff_exceptions=())

    # todo

if __name__ == "__main__":
    main()
