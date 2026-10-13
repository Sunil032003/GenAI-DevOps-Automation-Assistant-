"""Unit tests for code validation and AST syntax tools."""

import os
import tempfile
from fde_agent.tools.code_validator import (
    clean_code_fences,
    compute_unified_diff,
    validate_python_syntax,
    write_file_safe,
)


def test_clean_code_fences():
    fenced = "```python\ndef hello():\n    return 'world'\n```"
    cleaned = clean_code_fences(fenced, "python")
    assert cleaned == "def hello():\n    return 'world'"

    bare = "def hello():\n    return 'world'"
    assert clean_code_fences(bare) == bare


def test_validate_python_syntax():
    valid_code = "def add(a, b):\n    return a + b\n"
    is_valid, err = validate_python_syntax(valid_code)
    assert is_valid is True
    assert err is None

    invalid_code = "def broken(:\n    pass"
    is_valid, err = validate_python_syntax(invalid_code)
    assert is_valid is False
    assert "Syntax error" in err


def test_write_file_safe_with_backup():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "sample.py")
        # Initial write
        ok, err = write_file_safe(test_file, "x = 1\n", make_backup=False)
        assert ok is True

        # Second write with backup
        ok, err = write_file_safe(test_file, "x = 2\n", make_backup=True)
        assert ok is True
        assert os.path.isfile(f"{test_file}.bak")

        with open(f"{test_file}.bak", "r") as f:
            assert f.read() == "x = 1\n"
        with open(test_file, "r") as f:
            assert f.read() == "x = 2\n"


def test_compute_unified_diff():
    orig = "line 1\nline 2\n"
    mod = "line 1\nline 2 modified\n"
    diff = compute_unified_diff(orig, mod, "test.txt")
    assert "--- a/test.txt" in diff
    assert "+++ b/test.txt" in diff

