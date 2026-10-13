from openrouter_agent import ask_ai
import os


def generate_tests(
    project_path,
    filename,
    source_code,
    test_types,
    test_plan
):
    """
    Generate pytest tests based on the actual source code
    and the generated test plan.
    """

    module_name = os.path.splitext(
        os.path.basename(filename)
    )[0]

    prompt = f"""
You are an expert Python test implementation agent.

Your task is to convert the provided TEST PLAN into actual
pytest test code.

You MUST read both the source code and the test plan carefully.

==================================================
SOURCE FILE
==================================================

Filename:
{filename}

Module:
{module_name}

Source Code:
{source_code}

==================================================
USER REQUESTED TEST TYPES
==================================================

{test_types}

==================================================
TEST PLAN
==================================================

{test_plan}

==================================================
YOUR TASK
==================================================

Implement the test cases from the TEST PLAN as executable
pytest tests.

The TEST PLAN defines WHAT must be tested.

The SOURCE CODE defines HOW the application actually works.

Use both sources together.

==================================================
IMPORTANT RULES
==================================================

1. Implement the test cases that belong to the current source file.

2. Use the exact test case IDs from the TEST PLAN in comments.

3. Test only behavior that exists in the source code.

4. Do not invent functions, classes, methods, parameters,
   variables, return values, or behavior.

5. Use the actual function signatures from the source code.

6. Use realistic input values based on the source code
   and TEST PLAN.

7. Expected results must match the actual source code.

8. Do not change the original source code.

9. Use pytest.

10. Use unittest.mock when mocking is necessary.

11. If the source uses an external dependency, determine
    from the source code how that dependency is used and
    mock it appropriately when required.

12. If a mocked function returns an object that is later
    processed by another operation, the mocked return value
    must be compatible with that operation.

13. Do not use generic MagicMock values when the source code
    requires a specific type or structure.

14. Follow the actual execution path of the source code.

15. For conditional branches, create test inputs that
    actually reach the requested branch.

16. For loops, make sure test conditions eventually terminate.

17. Do not create infinite loops.

18. Tests must be independent.

19. Tests must not leave unwanted changes to global state.

20. If temporary state is changed during a test, isolate or
    restore it appropriately.

21. Do not access real hardware or external services
    unnecessarily during unit tests.

22. Do not remove assertions simply to make a test pass.

23. Do not create fake behavior that is not supported by
    the source code.

24. Do not duplicate the same test unnecessarily.

25. Only generate the test types requested by the user.

26. MOCKING OPENCV (cv2) & HARDWARE/GUI:
    - Under no circumstances should tests access real hardware (like a camera) or display a GUI window (like cv2.imshow).
    - If the source code uses OpenCV (cv2), you MUST mock all OpenCV functions.
    - Specifically, mock cv2.VideoCapture so that VideoCapture.read() returns (True, a dummy numpy array of the appropriate shape, e.g., np.zeros((480, 640, 3), dtype=np.uint8)) or (False, None) depending on the test case, rather than opening a real camera.
    - Mock cv2.waitKey to return a value that causes loops depending on it to terminate immediately (for example, if the loop terminates when 'q' is pressed, let waitKey return ord('q')).
    - Mock cv2.imshow, cv2.destroyAllWindows, and other GUI/drawing calls (like cv2.circle, cv2.putText, cv2.rectangle, cv2.line) to be no-ops.

==================================================
IMPORT RULES
==================================================

Import only names that actually exist.

Use the real module name:

from {module_name} import ...

Never use:

from your_module import ...

Do not invent imports.

==================================================
TEST CASE TRACEABILITY
==================================================

Every generated test must correspond to a test case in
the TEST PLAN.

Use comments like:

# TC001 - Register shopper

before the corresponding test.

Do not generate tests that cannot be mapped to a TEST PLAN
test case.

==================================================
FINAL VALIDATION
==================================================

Before returning the code, verify internally:

- Every imported name exists.
- Every function call uses the correct parameters.
- Every test corresponds to the TEST PLAN.
- Expected results are supported by the source code.
- Mocked values have the correct structure.
- Conditional tests actually reach their target branches.
- Loops terminate.
- Tests are independent.
- No real hardware is unnecessarily accessed.
- No source code is modified.

==================================================
OUTPUT
==================================================

Return ONLY valid Python test code.

Do NOT return explanations.

Do NOT return Markdown.

Do NOT use ```python.

Do NOT use ```.

Do NOT include anything outside the Python code.
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

    return response.strip()