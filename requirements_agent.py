import os


def detect_requirements(project_path):
    """
    Detect whether requirements.txt exists in the project.

    Returns a dict:
        - "exists": True if requirements.txt is found
        - "path": full path to requirements.txt or None
        - "content": list of dependency lines or None
    """

    requirements_path = os.path.join(
        project_path,
        "requirements.txt"
    )

    if not os.path.isfile(requirements_path):

        return {
            "exists": False,
            "path": None,
            "content": None
        }

    with open(
        requirements_path,
        "r",
        encoding="utf-8"
    ) as file:

        lines = [
            line.strip()
            for line in file.read().splitlines()
            if line.strip()
            and not line.strip().startswith("#")
        ]

    return {
        "exists": True,
        "path": requirements_path,
        "content": lines
    }