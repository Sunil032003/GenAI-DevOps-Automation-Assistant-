from openrouter_agent import ask_ai
import os


def generate_failure_report(
    project_path,
    source_code,
    test_code,
    pytest_output
):
    """
    Analyze pytest failures and generate a detailed
    failure report.
    """

    prompt = f"""
You are an expert software testing failure-analysis agent.

Analyze the source code, generated test code, and actual
pytest output.

Your job is ONLY to explain why the tests failed.

Do NOT modify the source code.

Do NOT generate replacement test code.

Do NOT claim that a test is correct simply because pytest
executed it.

==================================================
SOURCE CODE
==================================================

{source_code}

==================================================
GENERATED TEST CODE
==================================================

{test_code}

==================================================
PYTEST OUTPUT
==================================================

{pytest_output}

==================================================
ANALYSIS
==================================================

For every failed test:

1. Identify the test name.

2. Identify the source function/class/method being tested.

3. Identify the exact failure.

4. Explain the expected behavior according to the source code.

5. Explain what the generated test expected.

6. Compare the two.

7. Identify the root cause.

8. Determine whether the problem is:
   - incorrect test expectation
   - incorrect test input
   - incorrect mock
   - incorrect mock return type
   - incorrect execution condition
   - incorrect assertion
   - state contamination
   - missing dependency
   - environment/resource problem
   - actual source-code failure
   - other

9. Explain the evidence from the source code.

10. Provide a recommended action.

Do not invent behavior.

If the available information is insufficient to determine
the exact cause, explicitly say:

"Root cause cannot be determined from the available evidence."

==================================================
OUTPUT FORMAT
==================================================

Return ONLY Markdown.

Use:

# Test Failure Report

## Summary

- Total tests:
- Passed:
- Failed:
- Errors:
- Skipped:

## Failed Tests

For every failure:

### <Test Name>

**Status:** FAILED

**Source Function/Class:**

**Failure:**

**Expected According to Source:**

**What the Test Expected:**

**Root Cause:**

**Failure Category:**

**Evidence:**

**Recommended Action:**

## Overall Analysis

Explain the major patterns found across the failures.

## Final Assessment

State whether the failures appear to be caused mainly by:

- generated test problems
- source-code problems
- environment/dependency problems
- or a combination

Do not generate Python code.
Do not use Markdown code fences.
"""

    report = ask_ai(prompt)

    report = report.replace(
        "```markdown",
        ""
    )

    report = report.replace(
        "```md",
        ""
    )

    report = report.replace(
        "```",
        ""
    )

    report = report.strip()

    report_path = os.path.join(
        project_path,
        "TEST_FAILURE_REPORT.md"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    return report_path