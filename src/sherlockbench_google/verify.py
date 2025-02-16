import sys

from google.genai import types
from sherlockbench_client import destructure
import json
import re

from .prompts import make_verification_message, sys_instruct
from pprint import pprint

def trim_to_json(content: str) -> str:
    """
    Removes anything before the first `{` and after the last `}` in the given string.
    """
    match = re.search(r'\{.*\}', content, re.DOTALL)
    return match.group(0) if match else ""

def verify(config, postfn, chatfn, printer, attempt_id):
    # for each verification
    while (v_data := postfn("next-verification", {"attempt-id": attempt_id})):
        verification = v_data["next-verification"]
        output_type = v_data["output-type"]

        printer.print("\n### SYSTEM: inputs:")
        printer.indented_print(verification)

        config = types.GenerateContentConfigDict(
            system_instruction=sys_instruct
        )

        chat_response = chatfn.stateless_call(message=make_verification_message(verification), config=config)

        try:
            thoughts, expected_output = destructure(json.loads(trim_to_json(chat_response.text)), "thoughts", "expected_output")
        except json.JSONDecodeError as e:
            printer.print("\n### SYSTEM: bad json:")
            printer.print(chat_response.text)
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
