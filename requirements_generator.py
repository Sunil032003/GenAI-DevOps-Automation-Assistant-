import ast
import os
import re
import sys


# ============================================================
# IMPORT NAME -> PIP PACKAGE MAP
# ============================================================

PACKAGE_MAP = {
    "dotenv": "python-dotenv",
    "yaml": "PyYAML",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "bs4": "beautifulsoup4",
    "PIL": "Pillow",
    "pymongo": "pymongo",
    "flask": "Flask",
    "django": "Django",
    "requests": "requests",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "sqlalchemy": "SQLAlchemy",
    "openai": "openai",
    "langchain": "langchain",
    "transformers": "transformers",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "selenium": "selenium",
    "playwright": "playwright",
    "pytest": "pytest",
    "flask_cors": "flask-cors",
}


# ============================================================
# EXTRACT IMPORTS FROM A SOURCE FILE
# ============================================================

def _imports_from_code(source):

    imports = set()

    try:

        tree = ast.parse(source)

    except SyntaxError:

        return imports

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.Import
        ):

            for alias in node.names:

                top_level = (
                    alias.name.split(".")[0]
                )

                imports.add(
                    top_level
                )

        elif isinstance(
            node,
            ast.ImportFrom
        ):

            if node.module:

                top_level = (
                    node.module.split(".")[0]
                )

                imports.add(
                    top_level
                )

    return imports


# ============================================================
# DETECT THIRD-PARTY DEPENDENCIES
# ============================================================

def _is_local_module(project_path, name):
    """
    Return True if the import name refers to a module or package
    inside the project itself.
    """

    py_file = os.path.join(
        project_path,
        name + ".py"
    )

    pkg_dir = os.path.join(
        project_path,
        name
    )

    if os.path.isfile(py_file):
        return True

    if os.path.isdir(pkg_dir):

        init_file = os.path.join(
            pkg_dir,
            "__init__.py"
        )

        if os.path.isfile(init_file):
            return True

    return False


def detect_dependencies(project_path, files):
    """
    Return the set of third-party package names imported by the
    project source code (standard-library and local modules
    excluded).
    """

    stdlib = getattr(
        sys,
        "stdlib_module_names",
        set()
    )

    dependencies = set()

    for file in files:

        if not file.endswith(".py"):
            continue

        if os.path.basename(file).startswith("test_"):
            continue

        file_path = os.path.join(
            project_path,
            file
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as source_file:

                source = source_file.read()

        except Exception:
            continue

        for name in _imports_from_code(source):

            if name in stdlib:
                continue

            if _is_local_module(
                project_path,
                name
            ):
                continue

            dependencies.add(name)

    return dependencies


# ============================================================
# CREATE OR UPDATE requirements.txt
# ============================================================

def _package_base(entry):
    """
    Extract the plain package name from a requirements entry,
    ignoring version specifiers and extras.
    """

    match = re.match(
        r"[A-Za-z0-9._-]+",
        entry.strip()
    )

    if match:
        return match.group(0).lower()

    return entry.strip().lower()


def _split_entry(entry):
    """
    Split a requirements entry into (package_name, version_suffix).
    """

    stripped = entry.strip()

    match = re.match(
        r"[A-Za-z0-9._-]+",
        stripped
    )

    if not match:
        return stripped, ""

    return (
        match.group(0),
        stripped[match.end():]
    )


def generate_requirements(project_path, files):
    """
    Create or update requirements.txt.

    Preserves existing version pins and adds missing
    third-party dependencies plus pytest.

    Returns (requirements_path, dependencies, updated).
    """

    requirements_path = os.path.join(
        project_path,
        "requirements.txt"
    )

    existing_entries = []

    if os.path.isfile(requirements_path):

        try:

            with open(
                requirements_path,
                "r",
                encoding="utf-8"
            ) as file:

                existing_entries = [
                    line.strip()
                    for line in file
                    if line.strip()
                    and not line.strip().startswith("#")
                ]

        except Exception:

            existing_entries = []

    detected = detect_dependencies(
        project_path,
        files
    )

    required_packages = set()

    for dependency in detected:

        required_packages.add(
            PACKAGE_MAP.get(
                dependency,
                dependency
            )
        )

    # pytest is always required by the CI pipeline
    required_packages.add("pytest")

    required_by_base = {
        package.lower(): package
        for package in required_packages
    }

    final_entries = []
    seen = set()

    # Preserve existing version pins for packages that are still
    # required, using the canonical package name. Entries that no
    # longer map to a real dependency are dropped so that
    # 'pip install -r' can never fail.
    for entry in existing_entries:

        base = _package_base(entry)

        canonical = required_by_base.get(base)

        if canonical and base not in seen:

            seen.add(base)

            _, version_suffix = _split_entry(entry)

            final_entries.append(
                canonical + version_suffix
            )

    # Add missing required packages
    for package in sorted(required_packages):

        base = package.lower()

        if base not in seen:

            seen.add(base)

            final_entries.append(package)

    content = "\n".join(final_entries)

    if final_entries:
        content += "\n"

    with open(
        requirements_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    updated = (
        sorted(existing_entries)
        != sorted(final_entries)
    )

    return (
        requirements_path,
        sorted(required_packages),
        updated
    )
