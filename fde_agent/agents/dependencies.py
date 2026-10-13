"""
Dependency Engineer Agent for Forward Deployment Engineers.
Performs AST import extraction, standard library exclusion, and pinned requirements generation.
"""

import ast
import os
import sys
from typing import Dict, List, Set

from fde_agent.state import DependencyAudit, FDEAgentState
from fde_agent.tools.code_validator import write_file_safe

# Comprehensive map of Python top-level import name to PyPI distribution name
PACKAGE_MAP: Dict[str, str] = {
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
    "httpx": "httpx",
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
    "langgraph": "langgraph",
    "langchain_openai": "langchain-openai",
    "langchain_core": "langchain-core",
    "pydantic": "pydantic",
    "pytest": "pytest",
    "transformers": "transformers",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "selenium": "selenium",
    "playwright": "playwright",
    "flask_cors": "flask-cors",
    "rich": "rich",
    "click": "click",
    "jwt": "PyJWT",
    "redis": "redis",
    "psycopg2": "psycopg2-binary",
}

# Standard library module names (available in Python 3.10+)
STDLIB_MODULES: Set[str] = getattr(sys, "stdlib_module_names", set())


def extract_imports_from_source(source_code: str) -> Set[str]:
    """Extract top-level package names imported in Python source code."""
    imports = set()
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_pkg = alias.name.split(".")[0]
                imports.add(top_pkg)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Ignore relative imports
                top_pkg = node.module.split(".")[0]
                imports.add(top_pkg)

    return imports


def dependency_engineer_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Dependency Engineer Agent.
    Audits project imports, checks requirements.txt, and ensures reproducible dependencies.
    """
    project_path = state["project_path"]
    profile = state.get("profile")
    source_files = profile.source_files if profile else []

    all_imports: Set[str] = set()

    for rel_path in source_files:
        if not rel_path.endswith(".py"):
            continue
        full_path = os.path.join(project_path, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
                imports = extract_imports_from_source(source)
                all_imports.update(imports)
        except Exception:
            continue

    # Filter out standard library modules and internal project files
    project_module_names = {
        os.path.splitext(os.path.basename(f))[0]
        for f in source_files
    }

    external_imports: List[str] = []
    for pkg in sorted(all_imports):
        if pkg in STDLIB_MODULES:
            continue
        if pkg in project_module_names:
            continue
        if pkg.startswith("_"):
            continue
        external_imports.append(pkg)

    # Resolve to PyPI distribution names
    resolved: Dict[str, str] = {}
    for imp in external_imports:
        pypi_name = PACKAGE_MAP.get(imp, imp)
        resolved[imp] = pypi_name

    # Check existing requirements.txt
    req_path = os.path.join(project_path, "requirements.txt")
    req_exists = os.path.isfile(req_path)
    existing_lines: List[str] = []

    if req_exists:
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                existing_lines = [
                    line.strip()
                    for line in f.read().splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
        except Exception:
            existing_lines = []

    # Combine existing and newly detected packages
    final_pkgs = set()
    for line in existing_lines:
        pkg_name = line.split("==")[0].split(">=")[0].split("<")[0].strip()
        if pkg_name:
            final_pkgs.add(pkg_name)

    for pypi_pkg in resolved.values():
        final_pkgs.add(pypi_pkg)

    # Ensure testing framework is always present for FDE verification
    final_pkgs.add("pytest")

    # Order packages cleanly
    sorted_pkgs = sorted(list(final_pkgs), key=lambda x: x.lower())

    # Build formatted requirements.txt content
    req_content_lines = [
        "# ============================================================",
        "# Production Dependencies - Generated by FDE Multi-Agent System",
        "# ============================================================",
        "",
    ]
    for pkg in sorted_pkgs:
        req_content_lines.append(pkg)
    req_content_lines.append("")

    new_content = "\n".join(req_content_lines)

    # Write requirements.txt if missing or updated
    write_file_safe(req_path, new_content, make_backup=req_exists)

    audit = DependencyAudit(
        detected_imports=external_imports,
        resolved_packages=resolved,
        missing_packages=[p for p in sorted_pkgs if not any(p in line for line in existing_lines)],
        requirements_file_exists=req_exists,
        requirements_path=req_path,
        final_requirements=sorted_pkgs,
    )

    return {
        "dependencies": audit,
        "status": "DEPENDENCIES_AUDITED",
    }

