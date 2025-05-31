from anthropic.types import TextBlock, ToolUseBlock
import json
from .prompts import make_verification_message
from sherlockbench_client import destructure, value_list_to_map
from pprint import pprint

def trim_to_braces(s: str) -> str:
    """
    Removes anything before the first '{' and after the last '}' in the string.
    If either brace is missing, returns an empty string.
    """
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or start > end:
        return ''
    return s[start:end+1]

def verify(config, postfn, completionfn, messages, printer, attempt_id):
    # for each verification
    while (v_data := postfn("next-verification", {"attempt-id": attempt_id})):
        verification = v_data["next-verification"]
        output_type = v_data["output-type"]

        printer.print("\n### SYSTEM: inputs:")
        printer.indented_print(verification)

        # Anthropic 'Requests which include `tool_use` or `tool_result` blocks must define tools.'
        vmessages = [messages[-1]] + [make_verification_message(value_list_to_map(verification))]

        # claude sometimes gives invalid json. retry a few times
        attempts = 0

        # to prevent UnboundLocalError later
        thoughts = ""
        expected_output = ""

        while attempts < 3:
            completion = completionfn(messages=vmessages)

            response = next((item.text for item in completion.content if isinstance(item, TextBlock)), None)

            try:
                # Strip markdown code block markers if present
                cleaned_response = trim_to_braces(response)
                
                thoughts, expected_output = destructure(json.loads(cleaned_response), "thoughts", "expected_output")
                break

            except json.JSONDecodeError as e:
                attempts += 1
                print(f"Attempt {attempts} failed: {e}")
                print(cleaned_response)

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
