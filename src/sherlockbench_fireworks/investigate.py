import json
from openai import BadRequestError
from pydantic import BaseModel
import re

def remove_think_blocks(text: str) -> str:
    """
    Removes all occurrences of <think>...</think> (including the tags and content in between)
    from the input multi-line string.

    For Qwen as-per their recommendations: https://huggingface.co/Qwen/Qwen3-235B-A22B
    """
    # re.DOTALL makes '.' match newlines as well
    pattern = r"<think>.*?</think>"
    return re.sub(pattern, "", text, flags=re.DOTALL)

def list_to_map(input_list):
    """openai doesn't like arrays much so just assign arbritray keys"""
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: {"type": item} for key, item in zip(keys, input_list)}

def normalize_args(input_dict):
    """Converts a dict into a list of values, sorted by the alphabetical order of the keys."""
    return [input_dict[key] for key in sorted(input_dict.keys())]

def print_tool_call(printer, args, result):
    printer.indented_print(", ".join(map(str, args)), "→", result)

def handle_tool_call(postfn, printer, attempt_id, call):
    try:
        arguments = json.loads(call.function.arguments)

    except json.JSONDecodeError as e:
        function_call_result_message = {
            "role": "tool",
            "content": "invalid json when calling tool",
            "tool_call_id": call.id
        }

        return function_call_result_message

    args_norm = normalize_args(arguments)

    try:
        fnoutput = postfn("test-function", {"attempt-id": attempt_id,
                                            "args": args_norm})["output"]

        print_tool_call(printer, args_norm, fnoutput)

        function_call_result_message = {
            "role": "tool",
            "content": json.dumps(fnoutput),
            "tool_call_id": call.id
        }

    except KeyError as e:
        function_call_result_message = {
            "role": "tool",
            "content": "invalid schema when calling tool",
            "tool_call_id": call.id
        }

    return function_call_result_message

class NoToolException(Exception):
    """When the LLM doesn't use it's tool when it was expected to."""
    pass

class MsgLimitException(Exception):
    """When the LLM uses too many messages."""
    pass

def investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec):
    msg_limit = config["msg-limit"]

    mapped_args = list_to_map(arg_spec)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "mystery_function",
                "parameters": {
                    "type": "object",
                    "properties": mapped_args,
                    "required": list(mapped_args.keys()),
                    "additionalProperties": False
                },
            },
        }
    ]

    # call the LLM repeatedly until it stops calling it's tool
    tool_call_counter = 0
    for count in range(0, msg_limit):
        # # this retry logic is specifically for Qwen 3
        # for _ in range(3):
        #     try:
        #         completion = completionfn(messages=messages, tools=tools)
        #         break

        #     except BadRequestError as e:
        #         print(e)
        #         print("retrying")

        completion = completionfn(messages=messages, tools=tools)
                
        response = completion.choices[0]
        message = response.message.content
        tool_calls = response.message.tool_calls

        printer.print("\n--- LLM ---")
        printer.indented_print(message)

        if tool_calls:
            printer.print("\n### SYSTEM: calling tool")
            messages.append({"role": "assistant",
                             "content": remove_think_blocks(message),
                             "tool_calls": tool_calls})

            for call in tool_calls:
                messages.append(handle_tool_call(postfn, printer, attempt_id, call))

                tool_call_counter += 1

        # if it didn't call the tool we can move on to verifications
        else:
            printer.print("\n### SYSTEM: The tool was used", tool_call_counter, "times.")
            messages.append({"role": "assistant",
                             "content": remove_think_blocks(message)})

            return (messages, tool_call_counter)

    # LLM ran out of messages
    raise MsgLimitException("LLM ran out of messages.")
