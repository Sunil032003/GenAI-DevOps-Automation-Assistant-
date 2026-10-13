from openrouter_agent import ask_ai


def repair_tests(
    source_code,
    test_code,
    pytest_error
):
    """
    Ask the AI to repair a generated pytest test
    based on the actual pytest failure.
    """

    prompt = f"""
You are an expert Python test repair agent.

A pytest test was generated for the source code below,
but the test failed when executed.

Your task is to repair ONLY the test code.

==================================================
SOURCE CODE
==================================================

{source_code}

==================================================
GENERATED TEST CODE
==================================================

{test_code}

==================================================
PYTEST FAILURE
==================================================

{pytest_error}

==================================================
REPAIR REQUIREMENTS
==================================================

1. Carefully analyze the source code.

2. Carefully analyze the generated test.

3. Carefully analyze the complete pytest error.

4. Identify the actual reason the test failed.

5. Fix the test so that it correctly tests the behavior
   implemented by the source code.

6. Do NOT modify the source code.

7. Do NOT invent behavior that does not exist.

8. Do NOT simply remove a failing assertion to make the test pass.

9. Preserve the original purpose of the test.

10. If the test uses mocks, make the mocks compatible with
    how the source code actually uses them.

11. If the source requires a specific data type or structure,
    provide a compatible test value.

12. If the test needs to reach a specific conditional branch,
    construct inputs that actually reach that branch.

13. If the test modifies state, keep tests isolated.

14. Do not leave unwanted changes to global or shared state.

15. If the test involves external resources, mock them appropriately.

16. If a loop exists, ensure the test terminates.

17. Use the actual functions, classes and parameters from
    the source code.

18. Keep the test focused on the original requested behavior.

19. Return ONLY the complete corrected Python test code.

20. Do NOT return explanations.

21. Do NOT return Markdown.

22. Do NOT use code fences.

Return ONLY valid Python code.
"""

    repaired_test = ask_ai(prompt)

    repaired_test = repaired_test.replace(
        "```python",
        ""
    )

    repaired_test = repaired_test.replace(
        "```",
        ""
    )

    return repaired_test.strip()