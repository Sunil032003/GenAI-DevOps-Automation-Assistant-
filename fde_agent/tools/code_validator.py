"""
AST Syntax Validation and Safe File Modification Utilities.
"""

import ast
import difflib
import os
import re
import shutil
from typing import Optional, Tuple


def clean_code_fences(raw_content: str, language_hint: str = "python") -> str:
    """
    Robustly extract code from markdown fences.
    Handles ```python, ```dockerfile, ```yaml, etc., as well as bare fences.
    """
    if not raw_content:
        return ""

    content = raw_content.strip()

    # Match fenced code blocks
    pattern = rf"```(?:{language_hint}|{language_hint.lower()}|{language_hint.upper()})?\s*\n(.*?)\n```"
    matches = re.findall(pattern, content, flags=re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()

    # Fallback to any code fence if specific hint didn't match
    generic_matches = re.findall(r"```(?:\w+)?\s*\n(.*?)\n```", content, flags=re.DOTALL)
    if generic_matches:
        return generic_matches[0].strip()

    # Strip fences if at the extreme boundaries
    lines = content.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Check if Python code parses cleanly into an AST without SyntaxError.
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as exc:
        return False, f"Syntax error at line {exc.lineno}: {exc.msg}"
    except Exception as exc:
        return False, str(exc)


def write_file_safe(
    file_path: str,
    content: str,
    make_backup: bool = True,
    validate_syntax: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Safely write content to disk.
    Optionally creates a .bak backup and validates Python syntax before commit.
    """
    if validate_syntax and file_path.endswith(".py"):
        valid, err = validate_python_syntax(content)
        if not valid:
            return False, f"Refusing to write invalid Python syntax to {file_path}: {err}"

    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    if make_backup and os.path.isfile(file_path):
        backup_path = f"{file_path}.bak"
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as exc:
            return False, f"Failed to create backup at {backup_path}: {exc}"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, None
    except Exception as exc:
        return False, f"Failed writing to {file_path}: {exc}"


def restore_backup(file_path: str) -> bool:
    """
    Restore file from .bak backup if present.
    """
    backup_path = f"{file_path}.bak"
    if os.path.isfile(backup_path):
        shutil.copy2(backup_path, file_path)
        return True
    return False


def compute_unified_diff(original: str, modified: str, filename: str = "file") -> str:
    """
    Generate a concise unified diff between original and modified text.
    """
    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=3,
        )
    )
    return "".join(diff_lines)

