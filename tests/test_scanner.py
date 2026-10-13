"""Unit tests for scanner and file classification tools."""

import os
import pytest
from fde_agent.tools.scanner import classify_files, scan_project_files


def test_classify_files():
    files = [
        "main.py",
        "test_main.py",
        "requirements.txt",
        "README.md",
        ".env",
        "server.js",
    ]
    categories = classify_files(files)

    assert "main.py" in categories["source"]
    assert "test_main.py" in categories["tests"]
    assert "requirements.txt" in categories["configs"]
    assert "README.md" in categories["documentation"]
    assert ".env" in categories["sensitive"]


def test_scan_project_files_current_dir():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = scan_project_files(current_dir)
    assert len(files) > 0
    # Ignored directories like .git should not appear in relative paths
    assert not any(f.startswith(".git/") or f.startswith(".git\\") for f in files)

