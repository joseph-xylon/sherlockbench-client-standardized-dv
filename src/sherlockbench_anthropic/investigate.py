from anthropic.types import TextBlock, ToolUseBlock
from pprint import pprint

import json

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
    printer.indented_print(", ".join(map(str, args)), "→", result)

def parse_completion(content):
    #text = next((d["text"] for d in content if d.get("type") == "text"), None)
    #tool = next((d["input"] for d in content if d.get("type") == "tool_use"), None)

    text = next((item.text for item in content if isinstance(item, TextBlock)), None)
    tool = [item for item in content if isinstance(item, ToolUseBlock)]

    return (text, tool)

def handle_tool_call(postfn, printer, attempt_id, call):
    arguments = call.input
    call_id = call.id
    args_norm = normalize_args(arguments)

    fnoutput = postfn("test-function", {"attempt-id": attempt_id,
                                        "args": args_norm})["output"]

    print_tool_call(printer, args_norm, fnoutput)

    function_call_result_message = {"type": "tool_result",
                                    "tool_use_id": call_id,
                                    "content": json.dumps(fnoutput)}

    return function_call_result_message

def investigate(config, postfn, completionfn, messages, printer, attempt_id, arg_spec):
    msg_limit = config["msg-limit"]

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

    # call the LLM repeatedly until it stops calling it's tool
    tool_call_counter = 0
    for count in range(0, msg_limit):
        #pprint(messages)
        completion = completionfn(messages=messages, tools=tools)

        message, tool_calls = parse_completion(completion.content)

        printer.print("\n--- LLM ---")
        printer.indented_print(message)
        
        if tool_calls:
            printer.print("\n### SYSTEM: calling tool")
            messages.append({"role": "assistant",
                             "content":
                             ([] if message is None else  # Anthropic d
                             [{"type": "text", "text": message}]) + tool_calls})

            tool_call_user_message = {
                "role": "user",
                "content": []
            }

            for call in tool_calls:
                tool_call_user_message["content"].append(handle_tool_call(postfn, printer, attempt_id, call))

                tool_call_counter += 1

            messages.append(tool_call_user_message)

        # if it didn't call the tool we can move on to verifications
        else:
            printer.print("\n### SYSTEM: The tool was used", tool_call_counter, "times.")
            messages.append({"role": "assistant",
                             "content": [{"type": "text",
                               "text": message}]})

            return (messages, tool_call_counter)
        
    # LLM ran out of messages
    raise MsgLimitException("LLM ran out of messages.")
