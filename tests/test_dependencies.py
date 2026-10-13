"""Unit tests for Dependency Engineer Agent."""

from fde_agent.agents.dependencies import extract_imports_from_source, PACKAGE_MAP


def test_extract_imports_from_source():
    source = """
import os
import sys
import numpy as np
from fastapi import FastAPI, Depends
from mymodule.sub import helper
"""
    imports = extract_imports_from_source(source)
    assert "os" in imports
    assert "sys" in imports
    assert "numpy" in imports
    assert "fastapi" in imports
    assert "mymodule" in imports


def test_package_map_resolution():
    assert PACKAGE_MAP.get("dotenv") == "python-dotenv"
    assert PACKAGE_MAP.get("cv2") == "opencv-python"
    assert PACKAGE_MAP.get("sklearn") == "scikit-learn"
    assert PACKAGE_MAP.get("yaml") == "PyYAML"
    assert PACKAGE_MAP.get("langgraph") == "langgraph"

