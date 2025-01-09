import json
from pydantic import BaseModel

def list_to_map(input_list):
    "openai doesn't like arrays much so just assign arbritray keys"
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: {"type": item} for key, item in zip(keys, input_list)}

def normalize_args(input_dict):
    """Converts a dict into a list of values, sorted by the alphabetical order of the keys."""
    return [input_dict[key] for key in sorted(input_dict.keys())]

def print_tool_call(printer, args, result):
    printer.indented_print(", ".join(map(str, args)), "→", result)

def handle_tool_call(postfn, printer, attempt_id, call):
    arguments = json.loads(call.function.arguments)
    args_norm = normalize_args(arguments)

    fnoutput = postfn("test-function", {"attempt-id": attempt_id,
                                        "args": args_norm})["output"]

    print_tool_call(printer, args_norm, fnoutput)

    function_call_result_message = {
        "role": "tool",
        "content": json.dumps(fnoutput),
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
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "mystery_function",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": list_to_map(arg_spec),
                    "required": list(list_to_map(arg_spec).keys()),
                    "additionalProperties": False
                },
            },
        }
    ]

    # call the LLM repeatedly until it stops calling it's tool
    for count in range(0, msg_limit):
        completion = completionfn(messages=messages, tools=tools)

        response = completion.choices[0]
        message = response.message.content
        tool_calls = response.message.tool_calls

        tool_call_counter = 0

        printer.print("\n--- LLM ---")
        printer.indented_print(message)

        if tool_calls:
            printer.print("\n### SYSTEM: calling tool")
            messages.append({"role": "assistant",
                             "content": message,
                             "tool_calls": tool_calls})

            for call in tool_calls:
                messages.append(handle_tool_call(postfn, printer, attempt_id, call))

                tool_call_counter += 1

        # if it didn't call the tool we can move on to verifications
        else:
            printer.print("\n### SYSTEM: The tool was used", tool_call_counter, "times.")
            messages.append({"role": "assistant",
                             "content": message})

            return (messages, tool_call_counter)
        
    # LLM ran out of messages
    raise MsgLimitException("LLM ran out of messages.")

