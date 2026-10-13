"""
Production Project Scanner and File Classifier for Forward Deployment Engineers.
"""

import os
from typing import Dict, List, Set, Tuple

IGNORED_FOLDERS: Set[str] = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

IGNORED_FILES: Set[str] = {
    ".DS_Store",
    "Thumbs.db",
}

IGNORED_EXTENSIONS: Tuple[str, ...] = (
    ".pt",
    ".pth",
    ".h5",
    ".keras",
    ".pkl",
    ".joblib",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".ico",
    ".svg",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".mp3",
    ".wav",
    ".pdf",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
)


def scan_project_files(project_path: str) -> List[str]:
    """
    Scan repository and return all relevant code and configuration files.
    """
    if not os.path.isdir(project_path):
        raise ValueError(f"Project directory does not exist: {project_path}")

    files: List[str] = []

    for root, dirs, filenames in os.walk(project_path):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS]

        for filename in filenames:
            if filename in IGNORED_FILES:
                continue

            if filename.lower().endswith(IGNORED_EXTENSIONS):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, project_path).replace("\\", "/")
            files.append(rel_path)

    return sorted(files)


def classify_files(files: List[str]) -> Dict[str, List[str]]:
    """
    Categorize files into source, tests, configs, documentation, and sensitive items.
    """
    categories: Dict[str, List[str]] = {
        "source": [],
        "tests": [],
        "configs": [],
        "documentation": [],
        "sensitive": [],
    }

    config_names = {
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "pom.xml",
        "dockerfile",
        "docker-compose.yml",
        "pytest.ini",
    }

    for file in files:
        basename = os.path.basename(file).lower()

        if basename.startswith(".env") or basename.endswith(".key") or basename.endswith(".pem"):
            categories["sensitive"].append(file)

        if basename.startswith("test_") or basename.endswith("_test.py") or "/tests/" in file:
            categories["tests"].append(file)
        elif basename in config_names or basename.endswith((".yaml", ".yml", ".json", ".toml", ".ini", ".cfg")):
            categories["configs"].append(file)
        elif basename.endswith((".md", ".rst", ".txt")):
            categories["documentation"].append(file)
        elif basename.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".cs", ".rb")):
            categories["source"].append(file)
        else:
            categories["source"].append(file)

    return categories

