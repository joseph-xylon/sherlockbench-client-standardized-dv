from anthropic.types import TextBlock, ToolUseBlock
import json
from .prompts import make_verification_message
from sherlockbench_client import destructure
from pprint import pprint

def verify(config, postfn, completionfn, messages, printer, attempt_id):
    # for each verification
    while (v_data := postfn("next-verification", {"attempt-id": attempt_id})):
        verification = v_data["next-verification"]
        output_type = v_data["output-type"]

        printer.print("\n### SYSTEM: inputs:")
        printer.indented_print(verification)

        # Anthropic 'Requests which include `tool_use` or `tool_result` blocks must define tools.'
        vmessages = [messages[-1]] + [make_verification_message(verification)]

        # try:
        completion = completionfn(messages=vmessages)
        # except _ as e:

        response = next((item.text for item in completion.content if isinstance(item, TextBlock)), None)

        try:
            thoughts, expected_output = destructure(json.loads(response), "thoughts", "expected_output")
        except json.JSONDecodeError as e:
            printer.print("\n### SYSTEM: bad json:")
            printer.print(response)
            return False

        printer.print("\n--- LLM ---")
        printer.indented_print(thoughts, "\n")
        printer.print()
        printer.indented_print("`" + str(expected_output) + "`\n")

        vstatus = postfn("attempt-verification", {"attempt-id": attempt_id,
                                                  "prediction": expected_output})["status"]

        if vstatus in ("wrong"):
            printer.print("\n### SYSTEM: WRONG")
            return False
        else:
            printer.print("\n### SYSTEM: CORRECT")

        if vstatus in ("done"):
            break

    # if we got here all the verifications passed
    return True
