"""
Autonomous Self-Healing Agent for Forward Deployment Engineers.
Performs root-cause diagnosis, AST verification, and reflection repair loops.
"""

import os
import re
from typing import Dict, Optional, Tuple

from fde_agent.llm import LLMFactory
from fde_agent.state import FDEAgentState, RepairRecord
from fde_agent.tools.code_validator import clean_code_fences, validate_python_syntax, write_file_safe


SELF_HEALING_SYSTEM_PROMPT = """
You are a Principal Software Reliability and Self-Healing Agent in a Forward Deployment team.
A pytest test failed during client deployment verification.
Your mission is to perform root-cause analysis and apply the correct fix to either the SOURCE code, the TEST code, or both.

DIAGNOSTIC PRINCIPLES:
1. SOURCE CODE BUG:
   The source function or class has an implementation defect (wrong calculation, IndexError, unhandled None, faulty logic).
   In this case, fix the SOURCE CODE.
2. TEST CODE BUG:
   The test made invalid assumptions, expected wrong values, failed to mock external I/O/GUI, or tested functionality never intended.
   In this case, fix the TEST CODE.
3. NEVER simply delete or weaken assertions to make a test trivially pass.
4. Preserve intended software contracts and project architecture.

OUTPUT INSTRUCTIONS:
You must provide your response in the following exact format:

DIAGNOSIS: <brief explanation of the root cause>
TARGET: <SOURCE | TEST | BOTH>
FILE_TO_FIX: <relative path to file>
REPAIRED_CODE:
```python
<complete corrected code for the specified file>
```
"""


def parse_self_healing_response(response: str) -> Tuple[str, str, str, str]:
    """Parse the structured repair output from the LLM."""
    diagnosis = "Unspecified diagnosis"
    diag_match = re.search(r"DIAGNOSIS:\s*(.+?)(?=\nTARGET:|\nFILE_TO_FIX:|\nREPAIRED_CODE:|$)", response, re.DOTALL)
    if diag_match:
        diagnosis = diag_match.group(1).strip()

    target = "SOURCE"
    target_match = re.search(r"TARGET:\s*(\w+)", response)
    if target_match:
        target = target_match.group(1).strip().upper()

    file_to_fix = ""
    file_match = re.search(r"FILE_TO_FIX:\s*(.+?)\n", response)
    if file_match:
        file_to_fix = file_match.group(1).strip()

    repaired_code = clean_code_fences(response, "python")
    return diagnosis, target, file_to_fix, repaired_code


def self_healing_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Self-Healing Engineer Agent (Reflection & Repair Loop).
    """
    project_path = state["project_path"]
    test_results = state.get("test_results")
    repair_attempts = state.get("repair_attempts", 0) + 1
    repair_history = list(state.get("repair_history", []))

    if not test_results or test_results.success:
        return {"status": "TESTS_ALREADY_PASSING"}

    failed_tests = test_results.failed_test_names
    test_output = test_results.output

    # Identify candidate failing test file
    target_test_file = ""
    target_source_file = ""

    if failed_tests:
        # e.g., "test_Analyzer.py::test_foo" or "tests/test_x.py"
        first_failure = failed_tests[0].split("::")[0].replace("\\", "/")
        target_test_file = first_failure

        # Corresponding source file heuristic: test_foo.py -> foo.py
        base = os.path.basename(target_test_file)
        if base.startswith("test_"):
            source_base = base[5:]
            dir_name = os.path.dirname(target_test_file)
            target_source_file = os.path.join(dir_name, source_base).replace("\\", "/")

    # Read current content of test and source files
    test_code = ""
    source_code = ""

    test_full_path = os.path.join(project_path, target_test_file) if target_test_file else ""
    if test_full_path and os.path.isfile(test_full_path):
        try:
            with open(test_full_path, "r", encoding="utf-8") as f:
                test_code = f.read()
        except Exception:
            pass

    source_full_path = os.path.join(project_path, target_source_file) if target_source_file else ""
    if source_full_path and os.path.isfile(source_full_path):
        try:
            with open(source_full_path, "r", encoding="utf-8") as f:
                source_code = f.read()
        except Exception:
            pass

    # Build repair prompt
    prompt = f"""
Pytest Output:
```
{test_output[-3000:]}
```

Target Test File: {target_test_file}
Test Code:
```python
{test_code}
```

Target Source File: {target_source_file}
Source Code:
```python
{source_code}
```

Diagnose the real failure and provide the corrected code for the broken file.
"""

    response = LLMFactory.invoke_with_fallback(
        prompt=prompt,
        system_instruction=SELF_HEALING_SYSTEM_PROMPT,
        max_tokens=4096,
    )

    diagnosis, target_type, file_to_fix, repaired_code = parse_self_healing_response(response)

    # Determine which file path to write
    if not file_to_fix or file_to_fix not in [target_test_file, target_source_file]:
        file_to_fix = target_test_file if target_type == "TEST" else target_source_file

    full_target_path = os.path.join(project_path, file_to_fix) if file_to_fix else ""
    patch_applied = False
    syntax_valid = False

    if full_target_path and repaired_code:
        syntax_valid, syntax_err = validate_python_syntax(repaired_code)
        if syntax_valid:
            patch_applied, write_err = write_file_safe(full_target_path, repaired_code, make_backup=True)

    record = RepairRecord(
        attempt=repair_attempts,
        target_file=file_to_fix or "Unknown",
        repair_type="TEST" if target_type == "TEST" else "SOURCE",
        diagnosis=diagnosis,
        patch_applied=patch_applied,
        syntax_valid=syntax_valid,
        root_cause=diagnosis,
    )
    repair_history.append(record)

    return {
        "repair_attempts": repair_attempts,
        "repair_history": repair_history,
        "status": f"REPAIR_ATTEMPT_{repair_attempts}_COMPLETED",
    }

