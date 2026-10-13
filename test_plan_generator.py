from openrouter_agent import ask_ai
import os


def generate_test_plan(
    project_path,
    source_files,
    test_types
):
    """
    Generate a TEST_PLAN.md for the selected project files.
    """

    # ------------------------------------------
    # Read all selected source files
    # ------------------------------------------

    source_content = ""

    for file_path in source_files:

        filename = os.path.basename(file_path)

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                source_code = file.read()

        except Exception as error:

            source_code = (
                f"Unable to read this file: {error}"
            )

        source_content += f"""

==================================================
SOURCE FILE: {filename}
==================================================

{source_code}

"""


    # ------------------------------------------
    # AI prompt
    # ------------------------------------------

    prompt = f"""
You are an expert software test planning agent.

Your task is to analyze the ACTUAL source code provided below
and create a detailed test plan.

Do NOT generate Python test code.

The test plan will later be given to another AI agent that
will generate the actual pytest tests.

==================================================
SELECTED TEST TYPES
==================================================

{test_types}

==================================================
SOURCE CODE
==================================================

{source_content}

==================================================
ANALYSIS REQUIREMENTS
==================================================

First understand the source code completely.

Identify:

- functions
- classes
- methods
- parameters
- return values
- important conditions
- branches
- loops
- exceptions
- state changes
- dependencies
- external resources
- important inputs
- important outputs
- edge cases
- failure conditions

Do NOT assume functionality that does not exist.

Do NOT invent functions or behavior.

The test plan must be based ONLY on the provided source code.

==================================================
TEST CASE REQUIREMENTS
==================================================

Generate test cases ONLY for the test types requested by the user.

Each test case must contain:

1. Test Case ID

2. Test Case Name

3. Source File

4. Function/Class/Method

5. Test Type

6. Objective

7. Preconditions

8. Input / Test Data

9. Expected Result

10. Reason for Testing

11. Priority

Use IDs such as:

TC001
TC002
TC003

Each test case must describe a behavior that actually exists
in the source code.

For conditional branches, specify the input required to reach
the branch.

For edge cases, identify realistic boundary or unusual inputs
based on the source code.

For exception tests, only include exceptions that the source
code can actually produce or explicitly handles.

For state-changing operations, describe the expected state
after execution.

For external dependencies, identify what behavior needs to
be simulated or isolated during testing.

==================================================
TEST CASE QUALITY
==================================================

Avoid duplicate test cases.

Do not create tests simply to increase the number of tests.

Prefer meaningful tests that verify actual behavior.

Make the test plan specific enough that another AI agent can
implement the test cases without guessing.

Every expected result must be supported by the source code.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid Markdown content.

Use this structure:

# Test Plan

## Project Overview

Briefly describe what can be determined about the project
from the provided source code.

## Selected Test Types

List the test types requested by the user.

## Test Cases

For every test case use:

### TC001 - Test Case Name

- **Source File:** filename
- **Function/Class/Method:** actual name
- **Test Type:** actual test type
- **Objective:** ...
- **Preconditions:** ...
- **Input / Test Data:** ...
- **Expected Result:** ...
- **Reason for Testing:** ...
- **Priority:** High/Medium/Low

Continue with TC002, TC003, etc.

## Test Coverage Areas

List the source-code behaviors covered by the planned tests.

## Test Environment / Dependencies

List any dependencies or external resources that the tests
may need to mock, isolate, or configure.

Do NOT generate Python code.

Do NOT use Markdown code fences.

Do NOT add explanations outside the Markdown document.
"""

    # ------------------------------------------
    # Ask AI
    # ------------------------------------------

    test_plan = ask_ai(prompt)

    # ------------------------------------------
    # Clean accidental code fences
    # ------------------------------------------

    test_plan = test_plan.replace(
        "```markdown",
        ""
    )

    test_plan = test_plan.replace(
        "```md",
        ""
    )

    test_plan = test_plan.replace(
        "```",
        ""
    )

    test_plan = test_plan.strip()


    # ------------------------------------------
    # Save TEST_PLAN.md
    # ------------------------------------------

    test_plan_path = os.path.join(
        project_path,
        "TEST_PLAN.md"
    )

    with open(
        test_plan_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(test_plan)


    return test_plan_path