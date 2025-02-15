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
        max_tokens=8192,
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

def main():
    config, db_conn, cursor, run_id, attempts = start_run("anthropic")

    start_time = datetime.now()

    client = anthropic.Anthropic(api_key=config['api-keys']['anthropic'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)
    completionfn = lambda **kwargs: create_completion(client, config['model'], **kwargs)

    completionfn = LLMRateLimiter(rate_limit_seconds=config['rate-limit'],
                                  llmfn=completionfn,
                                  backoff_exceptions=())

    for attempt in attempts:
        investigate_and_verify(postfn, completionfn, config, attempt["attempt-id"], attempt["fn-args"], run_id, cursor)

if __name__ == "__main__":
    main()
