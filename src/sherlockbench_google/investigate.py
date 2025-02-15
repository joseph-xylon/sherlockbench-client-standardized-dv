import sys
from .prompts import sys_instruct, investigation_message

from google.genai import types
from pprint import pprint

def list_to_map(input_list):
    """assign arbritray keys to each argument and format it how Google likes"""
    keys = [chr(97 + i) for i in range(len(input_list))]  # Generate keys: 'a', 'b', 'c', etc.
    return {key: types.Schema(type=item.upper()) for key, item in zip(keys, input_list)}

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
        completion = chatfn(message=next_message, config=config)

        pprint(completion)

        sys.exit()
