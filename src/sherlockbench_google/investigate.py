import sys
from .prompts import sys_instruct, investigation_message

from google.genai import types
from pprint import pprint
import json

class NoToolException(Exception):
    """When the LLM doesn't use it's tool when it was expected to."""
    pass

class MsgLimitException(Exception):
    """When the LLM uses too many messages."""
    pass

def print_tool_call(printer, args, result):
    printer.indented_print(", ".join(map(str, args)), "→", result)

def list_to_map(input_list):
    """assign arbritray keys to each argument and format it how Google likes"""
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: types.Schema(type=item.upper()) for key, item in zip(keys, input_list)}

def normalize_args(input_dict):
    """Converts a dict into a list of values, sorted by the alphabetical order of the keys."""
    return [input_dict[key] for key in sorted(input_dict.keys())]

def handle_tool_call(postfn, printer, attempt_id, call):
    arguments = call.args
    fnname = call.name
    args_norm = normalize_args(arguments)

    fnoutput = postfn("test-function", {"attempt-id": attempt_id,
                                        "args": args_norm})["output"]

    print_tool_call(printer, args_norm, fnoutput)

    function_call_result_message = {"function_response":
                                    {"name": fnname,
                                     "response": {"output": json.dumps(fnoutput)}}}

    return function_call_result_message

def investigate(config, postfn, chatfn, printer, attempt_id, arg_spec):
    msg_limit = config["msg-limit"]

    mapped_args = list_to_map(arg_spec)
    tool = types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="mystery_function",
            description="Use this tool to test the mystery function.",
            parameters=types.Schema(
                properties=mapped_args,
                type='OBJECT',
            ),
        )
    ])
    
    # we override the config for each request. this allows us to specify the tool
    config = types.GenerateContentConfigDict(
        system_instruction=sys_instruct,
        tools=[tool]
    )

    # call the LLM repeatedly until it stops calling it's tool
    tool_call_counter = 0
    next_message = investigation_message
    for count in range(0, msg_limit):
        print("next_message:", next_message)
        completion = chatfn(message=next_message, config=config)

        llm_response = completion.candidates[0].content
        #pprint(llm_response)

        message = next((obj.text for obj in llm_response.parts if obj.text is not None), None)
        tool_calls = [obj.function_call for obj in llm_response.parts if obj.function_call is not None]

        printer.print("\n--- LLM ---")
        printer.indented_print(message)
        #print("tool calls: ")
        #pprint(tool_calls)
        
        if tool_calls:
            printer.print("\n### SYSTEM: calling tool")

            next_message = []
            for call in tool_calls:
                next_message.append(handle_tool_call(postfn, printer, attempt_id, call))

                tool_call_counter += 1

        # if it didn't call the tool we can move on to verifications
        else:
            printer.print("\n### SYSTEM: The tool was used", tool_call_counter, "times.")

            return (tool_call_counter)
