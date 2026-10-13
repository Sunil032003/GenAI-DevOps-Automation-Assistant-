"""
Sandboxed Pytest Execution Tool with Structured Telemetry Parsing.
"""

import os
import re
import subprocess
import sys
from typing import List, Optional

from fde_agent.config import config
from fde_agent.state import TestExecutionResult


def execute_tests(project_path: str, timeout_seconds: Optional[int] = None) -> TestExecutionResult:
    """
    Run pytest within target repository and return parsed structured telemetry.
    """
    timeout = timeout_seconds or config.test_timeout_seconds

    # Prepare isolated environment
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = project_path + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = project_path

    try:
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-v",
                "--tb=short",
            ],
            cwd=project_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""
        combined_output = stdout + "\n" + stderr

        # Parse metrics using regex
        passed_match = re.search(r"(\d+)\s+passed", combined_output)
        failed_match = re.search(r"(\d+)\s+failed", combined_output)
        error_match = re.search(r"(\d+)\s+error", combined_output)

        passed_count = int(passed_match.group(1)) if passed_match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0
        error_count = int(error_match.group(1)) if error_match else 0
        total_failures = failed_count + error_count
        total_tests = passed_count + total_failures

        # Extract failed test identifiers
        failed_test_names: List[str] = []
        for line in combined_output.splitlines():
            line_clean = line.strip()
            if line_clean.startswith("FAILED ") or line_clean.startswith("ERROR "):
                parts = line_clean.split()
                if len(parts) > 1:
                    failed_test_names.append(parts[1])

        # Categorize failure
        failure_category = "NONE"
        if process.returncode != 0:
            if "ModuleNotFoundError" in combined_output or "ImportError" in combined_output:
                failure_category = "ENVIRONMENT_BUG"
            elif "AssertionError" in combined_output:
                failure_category = "SOURCE_BUG"
            elif "SyntaxError" in combined_output:
                failure_category = "TEST_BUG"
            else:
                failure_category = "SOURCE_BUG"

        return TestExecutionResult(
            success=process.returncode == 0,
            return_code=process.returncode,
            total_tests=total_tests,
            passed_count=passed_count,
            failed_count=total_failures,
            failed_test_names=failed_test_names,
            output=combined_output,
            failure_category=failure_category if process.returncode != 0 else "NONE",
        )

    except subprocess.TimeoutExpired as exc:
        msg = (
            f"Test execution timed out after {timeout} seconds. "
            "Likely caused by an infinite loop or unmocked blocking I/O (GUI/Camera/Network).\n"
            f"{exc}"
        )
        return TestExecutionResult(
            success=False,
            return_code=-2,
            output=msg,
            failure_category="TIMEOUT",
        )

    except Exception as exc:
        return TestExecutionResult(
            success=False,
            return_code=-1,
            output=f"Pytest invocation failed: {exc}",
            failure_category="ENVIRONMENT_BUG",
        )

