import os
import subprocess
import sys


def run_tests(project_path):
    """
    Run pytest inside the target project and return the result.
    """

    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = project_path + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = project_path

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-v"
            ],
            cwd=project_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )


        output = result.stdout + "\n" + result.stderr

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "output": output
        }

    except subprocess.TimeoutExpired as error:
        return {
            "success": False,
            "return_code": -2,
            "output": f"Test execution timed out after 30 seconds. This might be due to an infinite loop, or an unmocked blocking call (e.g. cv2.waitKey or opening a camera/GUI). Please ensure all hardware, camera, and GUI interactions are mocked.\n{error}"
        }

    except Exception as error:

        return {
            "success": False,
            "return_code": -1,
            "output": str(error)
        }