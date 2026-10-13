"""
Safe Git and GitHub CLI Operations for Forward Deployment Engineers.
"""

import os
import shutil
import subprocess
from typing import List, Optional, Tuple


def find_gh_cli() -> Optional[str]:
    """Find the GitHub CLI executable on Windows or Linux."""
    gh_path = shutil.which("gh")
    if gh_path:
        return gh_path

    # Common Windows installation locations
    windows_paths = [
        r"C:\Program Files\GitHub CLI\gh.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe"),
    ]
    for p in windows_paths:
        if os.path.isfile(p):
            return p

    # Common Linux locations
    for p in ["/usr/bin/gh", "/usr/local/bin/gh"]:
        if os.path.isfile(p):
            return p

    return None


def run_git_command(args: List[str], cwd: str, timeout: int = 30) -> Tuple[bool, str]:
    """Execute a git command safely."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output.strip()
    except Exception as exc:
        return False, str(exc)


def get_git_remote_url(project_path: str) -> Optional[str]:
    """Retrieve the remote origin URL if configured."""
    success, output = run_git_command(["config", "--get", "remote.origin.url"], cwd=project_path)
    if success and output:
        return output.splitlines()[0].strip()
    return None


def stage_and_commit(project_path: str, commit_message: str) -> Tuple[bool, str]:
    """Stage all tracked changes and create a commit."""
    # Check if inside git repository
    if not os.path.isdir(os.path.join(project_path, ".git")):
        success, out = run_git_command(["init"], cwd=project_path)
        if not success:
            return False, f"Failed to initialize git repository: {out}"

    # Stage files
    success, out = run_git_command(["add", "."], cwd=project_path)
    if not success:
        return False, f"Git add failed: {out}"

    # Check if there is anything to commit
    success, out = run_git_command(["status", "--porcelain"], cwd=project_path)
    if not out.strip():
        return True, "No changes to commit (clean working directory)."

    # Commit
    success, out = run_git_command(["commit", "-m", commit_message], cwd=project_path)
    return success, out

