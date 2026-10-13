import re

from openrouter_agent import ask_ai


def repair_source_and_tests(
    source_code,
    test_code,
    pytest_error
):
    """
    Ask the AI to diagnose a failing test and return corrected
    SOURCE code and/or corrected TEST code.

    Returns a dict:
    {
        "source_code": str or None,
        "test_code": str or None
    }

    A key is None when the AI did not provide a corrected
    version of that part.
    """

    prompt = f"""
You are an expert software repair agent.

A pytest test was generated for the source code below,
but the test FAILED when executed.

Your job is to diagnose the exact root cause and fix
whatever is actually broken.

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
DIAGNOSIS RULES
==================================================

1. Carefully analyze the source code.

2. Carefully analyze the generated test.

3. Carefully analyze the complete pytest error.

4. Identify the REAL reason the test failed.

Two kinds of problems are possible:

A) SOURCE-CODE BUG:
   The source code does not do what its own structure
   clearly implies it should do. It may return a wrong
   value, crash on valid input, or behave inconsistently.
   In that case, fix the SOURCE CODE.

B) TEST-CODE BUG:
   The test is wrong. It may use the wrong import, wrong
   arguments, wrong expected result, wrong mock, or it may
   expect behavior that the source code never implemented.
   In that case, fix the TEST CODE.

You MUST decide which of the two is broken.

If the source is broken, fix the source.

If the test is broken, fix the test.

If both are broken, fix both.

==================================================
REPAIR RULES
==================================================

1. Do NOT change the intended behavior of the source.

2. Do NOT invent functions, classes, methods, parameters,
   return values, or behavior that the project does not have.

3. Do NOT make the source return a hard-coded value just to
   satisfy a test.

4. Do NOT remove an assertion from the test to make it pass.

5. Do NOT weaken the test expectations.

6. The test must verify the behavior the source actually
   implements.

7. If the source requires a specific data type or structure,
   provide a compatible test value.

8. If the test uses mocks, make the mocks compatible with
   how the source code actually uses them.

9. If the test needs to reach a specific conditional branch,
   construct inputs that actually reach that branch.

10. If a loop exists, ensure the test terminates.

11. Keep tests independent and isolated.

12. Use the actual module name and real function signatures.

13. If a file does NOT need to be changed, return it exactly
    as it was provided.

17. MOCKING OPENCV (cv2) & HARDWARE/GUI:
    - Under no circumstances should tests access real hardware (like a camera) or display a GUI window (like cv2.imshow).
    - If the source or test code uses OpenCV (cv2), you MUST mock all OpenCV functions.
    - Specifically, mock cv2.VideoCapture so that VideoCapture.read() returns (True, a dummy numpy array of the appropriate shape, e.g., np.zeros((480, 640, 3), dtype=np.uint8)) or (False, None) depending on the test case, rather than opening a real camera.
    - Mock cv2.waitKey to return a value that causes loops depending on it to terminate immediately (for example, if the loop terminates when 'q' is pressed, let waitKey return ord('q')).
    - Mock cv2.imshow, cv2.destroyAllWindows, and other GUI/drawing calls (like cv2.circle, cv2.putText, cv2.rectangle, cv2.line) to be no-ops.

14. Do NOT return explanations.

15. Do NOT return Markdown.

16. Do NOT use code fences.

==================================================
OUTPUT FORMAT
==================================================

Return the COMPLETE corrected source code between the tags
below, followed by the COMPLETE corrected test code between
the tags below. Both blocks must be present and must contain
ONLY valid Python code.

<SOURCE>
<complete corrected python source code>
</SOURCE>

<TEST>
<complete corrected python test code>
</TEST>
"""

    response = ask_ai(prompt)

    # Robustly extract python code block(s)
    import re
    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", response, re.DOTALL)
    if code_blocks:
        response = "\n\n".join(code_blocks)
    else:
        # Fallback: remove accidental code fences if no block matched
        response = response.replace("```python", "").replace("```", "")

    source_block = _extract_block(
        response,
        "SOURCE"
    )

    test_block = _extract_block(
        response,
        "TEST"
    )

    result = {
        "source_code": (
            source_block.strip()
            if source_block
            else None
        ),
        "test_code": (
            test_block.strip()
            if test_block
            else None
        )
    }

    return result


def _extract_block(text, tag):
    """
    Extract the content between <TAG> and </TAG>.
    Returns None when the tag block is not found.
    """

    start_pattern = re.compile(
        r"<\s*"
        + tag
        + r"\s*>",
        re.IGNORECASE
    )

    end_pattern = re.compile(
        r"<\s*/\s*"
        + tag
        + r"\s*>",
        re.IGNORECASE
    )

    start_match = start_pattern.search(text)
    end_match = end_pattern.search(text)

    if not start_match or not end_match:
        return None

    if end_match.start() < start_match.end():
        return None

    return text[
        start_match.end():end_match.start()
    ]
