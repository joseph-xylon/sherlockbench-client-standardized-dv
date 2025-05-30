from anthropic.types import TextBlock, ToolUseBlock, ThinkingBlock, RedactedThinkingBlock
from pprint import pprint
from sherlockbench_client import destructure, AccumulatingPrinter, q

import json
from datetime import datetime
from .prompts import make_initial_message, make_decision_messages
from .verify import verify

def list_to_map(input_list):
    """assign arbritray keys to each argument and format it how Anthropic likes"""
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: {"type": item} for key, item in zip(keys, input_list)}

def normalize_args(input_dict):
    """Converts a dict into a list of values, sorted by the alphabetical order of the keys."""
    return [input_dict[key] for key in sorted(input_dict.keys())]

class NoToolException(Exception):
    """When the LLM doesn't use it's tool when it was expected to."""
    pass

class MsgLimitException(Exception):
    """When the LLM uses too many messages."""
    pass

def print_tool_call(printer, args, result):
    printer.indented_print("(" + ", ".join(map(str, args)) + ")", "→", result)

def parse_completion(content):
    #text = next((d["text"] for d in content if d.get("type") == "text"), None)
    #tool = next((d["input"] for d in content if d.get("type") == "tool_use"), None)

    # using next allows us to have a default value
    thinking_block = next((item for item in content if isinstance(item, ThinkingBlock)), None)
    redacted_thinking_block = next((item for item in content if isinstance(item, RedactedThinkingBlock)), None)
    text = next((item.text for item in content if isinstance(item, TextBlock)), None)
    tool = [item for item in content if isinstance(item, ToolUseBlock)]

    return (thinking_block, redacted_thinking_block, text, tool)

class ToolCallHandler:
    def __init__(self, postfn, printer, attempt_id):
        self.postfn = postfn
        self.printer = printer
        self.attempt_id = attempt_id
        self.call_history = []

    def handle_tool_call(self, call):
        arguments = call.input
        call_id = call.id
        args_norm = normalize_args(arguments)

        fnoutput, fnerror = destructure(self.postfn("test-function", {"attempt-id": self.attempt_id,
                                                                      "args": args_norm}),
                                        "output",
                                        "error")

        # Handle case where the output key is missing
        if fnoutput is None:
            fnoutput = "Error calling tool"

        print_tool_call(self.printer, args_norm, fnoutput)

        if not fnerror:
            self.call_history.append((args_norm, fnoutput))

        function_call_result_message = {"type": "tool_result",
                                        "tool_use_id": call_id,
                                        "content": json.dumps(fnoutput)}

        return function_call_result_message

    def get_call_history(self):
        return self.call_history

    def format_call_history(self):
        lines = []
        for args, output in self.call_history:
            args_str = "(" + ", ".join(map(str, args)) + ")"
            lines.append(f"{args_str} → {output}")
        return "\n".join(lines)

def investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec, test_limit):
    mapped_args = list_to_map(arg_spec)
    tools = [
        {
            "name": "mystery_function",
            "description": "Use this tool to test the mystery function.",
            "input_schema": {
                "type": "object",
                "properties": mapped_args,
                "required": list(mapped_args.keys())
            }
        }
    ]

    tool_handler = ToolCallHandler(postfn, printer, attempt_id)

    # call the LLM repeatedly until it stops calling it's tool
    tool_call_counter = 0
    for _ in range(0, test_limit + 5):  # the primary limit is on tool calls. This is just a failsafe
        #pprint(messages)
        completion = completionfn(messages=messages, tools=tools)

        thinking, redacted_thinking, message, tool_calls = parse_completion(completion.content)

        printer.print("\n--- LLM ---")
        printer.indented_print(message)

        if tool_calls:
            printer.print("\n### SYSTEM: calling tool")
            # Add thinking block for models with +thinking suffix
            content_blocks = []

            if thinking:
                # Convert the ThinkingBlock object to a dict for the API
                content_blocks.append({"type": "thinking", "thinking": thinking.thinking, "signature": thinking.signature})

            if redacted_thinking:
                # Handle redacted thinking block
                content_blocks.append({"type": "redacted_thinking"})

            if message is not None:
                content_blocks.append({"type": "text", "text": message})

            content_blocks.extend(tool_calls)

            messages.append({"role": "assistant", "content": content_blocks})

            tool_call_user_message = {
                "role": "user",
                "content": []
            }

            for call in tool_calls:
                tool_call_user_message["content"].append(tool_handler.handle_tool_call(call))

                tool_call_counter += 1

            messages.append(tool_call_user_message)

        # if it didn't call the tool we can move on to verifications
        else:
            printer.print("\n### SYSTEM: The tool was used", tool_call_counter, "times.")

            content_blocks = []

            if thinking:
                # Convert the ThinkingBlock object to a dict for the API
                content_blocks.append({"type": "thinking", "thinking": thinking.thinking, "signature": thinking.signature})

            if redacted_thinking:
                # Handle redacted thinking block
                content_blocks.append({"type": "redacted_thinking"})

            if message is not None:
                content_blocks.append({"type": "text", "text": message})

            messages.append({"role": "assistant", "content": content_blocks})

            return (tool_handler.format_call_history(), tool_call_counter)

    raise MsgLimitException("Investigation loop overrun.")

def decision(completionfn, messages, printer):
    completion = completionfn(messages=messages)

    thinking, redacted_thinking, message, tool_calls = parse_completion(completion.content)

    printer.print("\n--- LLM ---")
    printer.indented_print(message)

    return messages

def investigate_decide_verify(postfn, completionfn, config, attempt, run_id, cursor):
    attempt_id, arg_spec, test_limit = destructure(attempt, "attempt-id", "arg-spec", "test-limit")

    start_time = datetime.now()
    start_api_calls = completionfn.total_call_count

    # setup the printer
    printer = AccumulatingPrinter()

    printer.print("\n### SYSTEM: interrogating function with args", arg_spec)

    messages = make_initial_message(test_limit)
    tool_calls, tool_call_count = investigate(config, postfn, completionfn, messages,
                                              printer, attempt_id, arg_spec, test_limit)

    printer.print("\n### SYSTEM: making decision based on tool calls", arg_spec)
    printer.print(tool_calls)

    messages = make_decision_messages(tool_calls)
    messages = decision(completionfn, messages, printer)

    printer.print("\n### SYSTEM: verifying function with args", arg_spec)
    verification_result = verify(config, postfn, completionfn, messages, printer, attempt_id)

    time_taken = (datetime.now() - start_time).total_seconds()
    q.add_attempt(cursor, run_id, verification_result, time_taken, tool_call_count, printer, completionfn, start_api_calls, attempt_id)

    return verification_result
