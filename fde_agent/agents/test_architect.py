"""
Test Architect Agent for Forward Deployment Engineers.
Generates structured test plans and robust, isolated pytest suites with full mocking.
"""

import os
from typing import Dict, List, Optional

from fde_agent.llm import LLMFactory
from fde_agent.state import FDEAgentState
from fde_agent.tools.code_validator import clean_code_fences, validate_python_syntax, write_file_safe


TEST_PLAN_SYSTEM_PROMPT = """
You are a Principal Test Architect and Forward Deployment Engineer.
Your objective is to design a robust, production-grade test strategy for client codebases.
Focus on:
1. Unit tests for core business logic and functions.
2. Handling boundary conditions, unexpected inputs, and None values.
3. Strict isolation: all external services, network calls, databases, hardware, OpenCV/camera, and GUI loops MUST be mocked.
4. Measurable assertions with clear failure messages.
Provide a clear, structured Markdown Test Plan.
"""

TEST_GENERATOR_SYSTEM_PROMPT = """
You are an expert Python QA Engineer and Forward Deployment Test Specialist.
Your task is to write complete, executable pytest code based on the source code and test plan.

CRITICAL REQUIREMENTS:
1. Return ONLY pure Python code. Do NOT wrap in markdown fences if possible, or use standard ```python fences.
2. Do NOT write explanations or prose outside the code.
3. Import the target module and classes/functions correctly.
4. MOCK all external I/O: network requests, file writes, database connections, and hardware/camera (e.g. cv2.waitKey).
5. All test functions must start with `test_`.
6. Code MUST be 100% syntactically valid Python.
"""


def generate_test_plan_for_file(filename: str, source_code: str) -> str:
    """Generate a test plan for a given source module."""
    prompt = f"""
Module Name: {filename}

Source Code:
```python
{source_code}
```

Please design a comprehensive Test Plan for this module covering happy paths, edge cases, and required mocks.
"""
    return LLMFactory.invoke_with_fallback(
        prompt=prompt,
        system_instruction=TEST_PLAN_SYSTEM_PROMPT,
        max_tokens=2048,
    )


def generate_pytest_code_for_file(filename: str, source_code: str, test_plan: str) -> str:
    """Generate executable pytest code for a module given its source code and test plan."""
    module_name = os.path.splitext(os.path.basename(filename))[0]
    prompt = f"""
Source File: {filename} (import as `{module_name}`)
Source Code:
```python
{source_code}
```

Test Plan:
{test_plan}

Write the complete, runnable pytest test file for this module.
Ensure all external dependencies and hardware/GUI interactions (like OpenCV waitKey/VideoCapture) are mocked with unittest.mock.
"""
    raw_response = LLMFactory.invoke_with_fallback(
        prompt=prompt,
        system_instruction=TEST_GENERATOR_SYSTEM_PROMPT,
        max_tokens=4096,
    )
    return clean_code_fences(raw_response, "python")


def test_architect_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Test Architect Agent.
    Creates test plans and generates executable pytest suites for eligible source files.
    """
    project_path = state["project_path"]
    profile = state.get("profile")
    source_files = profile.source_files if profile else []

    test_plan_sections: List[str] = []
    generated_tests: Dict[str, str] = {}

    for rel_path in source_files:
        if not rel_path.endswith(".py"):
            continue

        basename = os.path.basename(rel_path)
        # Avoid generating tests for test files or entry scripts that have no testable functions
        if basename.startswith("test_") or basename == "__init__.py":
            continue

        full_path = os.path.join(project_path, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
        except Exception:
            continue

        if not source_code.strip():
            continue

        # Generate Test Plan
        plan = generate_test_plan_for_file(rel_path, source_code)
        test_plan_sections.append(f"### Test Plan for {rel_path}\n{plan}")

        # Generate Pytest Code
        test_code = generate_pytest_code_for_file(rel_path, source_code, plan)

        # Validate syntax
        is_valid, err = validate_python_syntax(test_code)
        if not is_valid:
            # Attempt one repair of the test syntax if broken
            prompt_repair = f"The following test code has a syntax error: {err}\n\n{test_code}\n\nFix it and return valid Python code only."
            repaired = LLMFactory.invoke_with_fallback(
                prompt=prompt_repair,
                system_instruction=TEST_GENERATOR_SYSTEM_PROMPT,
            )
            test_code = clean_code_fences(repaired, "python")

        # Determine target test file path (e.g. test_<name>.py in root or same directory)
        dir_name = os.path.dirname(rel_path)
        test_filename = f"test_{basename}"
        test_rel_path = os.path.join(dir_name, test_filename).replace("\\", "/") if dir_name else test_filename
        test_full_path = os.path.join(project_path, test_rel_path)

        # Write test file to disk
        write_file_safe(test_full_path, test_code, make_backup=True)
        generated_tests[test_rel_path] = test_code

    combined_test_plan = "\n\n".join(test_plan_sections)

    return {
        "test_plan": combined_test_plan,
        "test_files": generated_tests,
        "status": "TESTS_ARCHITECTED",
    }

