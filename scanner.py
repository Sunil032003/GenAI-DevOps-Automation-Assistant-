import os


def scan_project(project_path):

    files = []

    # Folders that Git Pilot should ignore
    ignored_folders = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "venv",
        ".venv",
        "node_modules"
    }

    # Files that Git Pilot should ignore
    ignored_files = {
        "README.md",
        "Dockerfile",
        ".gitignore"
    }

    # File types that are not useful for code analysis/testing
    ignored_extensions = (
        ".pt",
        ".pth",
        ".h5",
        ".keras",
        ".pkl",
        ".joblib",
        ".zip",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".mp4",
        ".avi",
        ".mov"
    )

    for root, dirs, filenames in os.walk(project_path):

        # Don't enter ignored folders
        dirs[:] = [
            d for d in dirs
            if d not in ignored_folders
        ]

        for filename in filenames:

            # Ignore specific files
            if filename in ignored_files:
                continue

            # Ignore existing test files
            if filename.startswith("test_"):
                continue

            # Ignore model, image, video and binary files
            if filename.lower().endswith(ignored_extensions):
                continue

            # Get complete file path
            file_path = os.path.join(root, filename)

            # Convert to path relative to project
            relative_path = os.path.relpath(
                file_path,
                project_path
            )

            files.append(relative_path)

    return files