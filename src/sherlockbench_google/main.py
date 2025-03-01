from google import genai
from sherlockbench_client import destructure, post, AccumulatingPrinter, LLMRateLimiter, q, start_run, complete_run

from .investigate import investigate
from .verify import verify

from datetime import datetime

def new_chat(client, model):
    """return a function which generates new chats"""

    def fngen():
        return client.chats.create(model=model).send_message

    return fngen

def investigate_and_verify(postfn, chatfn, config, attempt_id, arg_spec, run_id, cursor):
    start_time = datetime.now()
    start_api_calls = chatfn.total_call_count

    # setup the printer
    printer = AccumulatingPrinter()

    printer.print("\n### SYSTEM: interrogating function with args", arg_spec)

    chatfn.renew_llmfn()
    tool_call_count = investigate(config, postfn, chatfn, printer, attempt_id, arg_spec)

    printer.print("\n### SYSTEM: verifying function with args", arg_spec)
    verification_result = verify(config, postfn, chatfn, printer, attempt_id)

    time_taken = (datetime.now() - start_time).total_seconds()
    q.add_attempt(cursor, run_id, verification_result, time_taken, tool_call_count, printer, chatfn, start_api_calls, attempt_id)

    return verification_result

def main():
    config, db_conn, cursor, run_id, attempts, start_time = start_run("google")

    client = genai.Client(api_key=config['api-keys']['google'])
    chat = new_chat(client, model=config['model'])

    postfn = lambda *args: post(config["base-url"], run_id, *args)

    chatfn = LLMRateLimiter(rate_limit_seconds=config['rate-limit'],
                            llmfn=lambda *args, **kwargs: None,  # noop
                            backoff_exceptions=(genai.errors.ClientError, genai.errors.ServerError),
                            renewfn=new_chat(client, config['model']))

    for attempt in attempts:
        investigate_and_verify(postfn, chatfn, config, attempt["attempt-id"], attempt["arg-spec"], run_id, cursor)

    complete_run(postfn, db_conn, cursor, run_id, start_time, chatfn.total_call_count, config)

if __name__ == "__main__":
    main()
