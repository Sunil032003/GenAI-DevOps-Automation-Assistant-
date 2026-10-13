import os
import re
import yaml


WORKFLOW_FILENAME = "ci-cd.yml"


def _build_workflow(include_docker):
    """
    Build the CI/CD workflow YAML deterministically.

    Never asks an LLM for CI commands. CI failures must stay
    failures, and CD must never run after a failed CI.
    """

    lines = []
    lines.append("name: CI/CD Workflow")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("  pull_request:")
    lines.append("")
    lines.append("jobs:")
    lines.append("  ci:")
    lines.append("    runs-on: ubuntu-latest")
    lines.append("    steps:")
    lines.append("      - name: Checkout repository")
    lines.append("        uses: actions/checkout@v4")
    lines.append("")
    lines.append("      - name: Setup Python 3.12")
    lines.append("        uses: actions/setup-python@v5")
    lines.append("        with:")
    lines.append("          python-version: '3.12'")
    lines.append("")
    lines.append("      - name: Upgrade pip")
    lines.append("        run: python -m pip install --upgrade pip")
    lines.append("")
    lines.append("      - name: Install dependencies")
    lines.append("        run: python -m pip install -r requirements.txt")
    lines.append("")
    lines.append("      - name: Run tests")
    lines.append("        run: python -m pytest -v")
    lines.append("")
    lines.append("  cd:")
    lines.append("    runs-on: ubuntu-latest")
    lines.append("    needs: ci")
    lines.append("    steps:")
    lines.append("      - name: Checkout repository")
    lines.append("        uses: actions/checkout@v4")
    lines.append("")

    if include_docker:

        lines.append("      - name: Check Docker")
        lines.append("        run: docker --version")
        lines.append("")
        lines.append("      - name: Build Docker image")
        lines.append("        run: docker build -t my-image .")
        lines.append("")

    else:

        lines.append("      - name: Verify project")
        lines.append("        run: echo \"No Dockerfile configured.\"")
        lines.append("")

    return "\n".join(lines)


def _has_dockerfile(project_path):
    """Check if Dockerfile exists in project."""
    return os.path.isfile(os.path.join(project_path, "Dockerfile"))


def _get_workflow_path(project_path, filename=None):
    """Get the full path to the workflow file."""
    if not filename:
        filename = WORKFLOW_FILENAME
    workflow_directory = os.path.join(project_path, ".github", "workflows")
    os.makedirs(workflow_directory, exist_ok=True)
    return os.path.join(workflow_directory, filename)


def _load_existing_workflow(workflow_path):
    """Load existing workflow content if it exists."""
    if not os.path.isfile(workflow_path):
        return None
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _parse_workflow(content):
    """Parse workflow YAML content."""
    try:
        return yaml.safe_load(content)
    except Exception:
        return None


def _workflow_has_docker_job(workflow_dict):
    """Check if workflow has a CD job with Docker steps."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    cd_job = workflow_dict["jobs"].get("cd")
    if not cd_job or "steps" not in cd_job:
        return False
    for step in cd_job["steps"]:
        run_cmd = step.get("run", "")
        if "docker" in run_cmd.lower():
            return True
    return False


def _workflow_has_apt_get_docker_install(workflow_dict):
    """Check if workflow contains sudo apt-get install docker.io or similar."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    cd_job = workflow_dict["jobs"].get("cd")
    if not cd_job or "steps" not in cd_job:
        return False
    for step in cd_job["steps"]:
        run_cmd = step.get("run", "")
        if "apt-get" in run_cmd and "docker" in run_cmd:
            return True
        if "apt-get update" in run_cmd:
            return True
    return False


def _workflow_has_docker_version_check(workflow_dict):
    """Check if workflow has 'docker --version' check."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    cd_job = workflow_dict["jobs"].get("cd")
    if not cd_job or "steps" not in cd_job:
        return False
    for step in cd_job["steps"]:
        run_cmd = step.get("run", "")
        if "docker --version" in run_cmd:
            return True
    return False


def _workflow_has_docker_build(workflow_dict):
    """Check if workflow has 'docker build' command."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    cd_job = workflow_dict["jobs"].get("cd")
    if not cd_job or "steps" not in cd_job:
        return False
    for step in cd_job["steps"]:
        run_cmd = step.get("run", "")
        if "docker build" in run_cmd:
            return True
    return False


def _workflow_has_needs_ci(workflow_dict):
    """Check if CD job has 'needs: ci'."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    cd_job = workflow_dict["jobs"].get("cd")
    if not cd_job:
        return False
    return cd_job.get("needs") == "ci" or cd_job.get("needs") == ["ci"]


def _workflow_has_ci_steps(workflow_dict):
    """Check if CI job has all required steps."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False
    ci_job = workflow_dict["jobs"].get("ci")
    if not ci_job or "steps" not in ci_job:
        return False

    steps = ci_job["steps"]
    has_checkout = False
    has_setup_python = False
    has_pip_upgrade = False
    has_install_reqs = False
    has_pytest = False

    for step in steps:
        uses = step.get("uses", "")
        run_cmd = step.get("run", "")

        if "actions/checkout" in uses:
            has_checkout = True
        if "actions/setup-python" in uses:
            has_setup_python = True
        if "python -m pip install --upgrade pip" in run_cmd:
            has_pip_upgrade = True
        if "python -m pip install -r requirements.txt" in run_cmd:
            has_install_reqs = True
        if "python -m pytest -v" in run_cmd:
            has_pytest = True

    return all([has_checkout, has_setup_python, has_pip_upgrade, has_install_reqs, has_pytest])


def _workflow_has_failure_masking(workflow_dict):
    """Check if workflow masks test failures."""
    if not workflow_dict or "jobs" not in workflow_dict:
        return False

    def check_job(job):
        if not job or "steps" not in job:
            return False
        for step in job["steps"]:
            run_cmd = step.get("run", "")
            if "|| true" in run_cmd:
                return True
            if step.get("continue-on-error") is True:
                return True
            if step.get("if") == "always()":
                return True
        return False

    return check_job(workflow_dict["jobs"].get("ci")) or check_job(workflow_dict["jobs"].get("cd"))


def _update_workflow_in_place(workflow_path, project_path, has_dockerfile):
    """
    Read existing workflow, compare with required config, and update in place.
    Returns (updated, changes_made_list)
    """
    existing_content = _load_existing_workflow(workflow_path)
    if not existing_content:
        return False, ["No existing workflow to update"]

    workflow_dict = _parse_workflow(existing_content)
    if not workflow_dict:
        return False, ["Failed to parse existing workflow"]

    changes = []

    # Check CI steps
    if not _workflow_has_ci_steps(workflow_dict):
        changes.append("CI steps incomplete or missing")

    # Check failure masking
    if _workflow_has_failure_masking(workflow_dict):
        changes.append("Workflow masks test failures (|| true, continue-on-error, if: always())")

    # Check CD needs: ci
    if not _workflow_has_needs_ci(workflow_dict):
        changes.append("CD job missing 'needs: ci'")

    # Check Docker handling
    if has_dockerfile:
        if _workflow_has_apt_get_docker_install(workflow_dict):
            changes.append("CD contains deprecated 'sudo apt-get install docker.io'")
        if not _workflow_has_docker_version_check(workflow_dict):
            changes.append("CD missing 'docker --version' check")
        if not _workflow_has_docker_build(workflow_dict):
            changes.append("CD missing 'docker build -t my-image .'")
    else:
        # No Dockerfile - CD should have verification step
        cd_job = workflow_dict.get("jobs", {}).get("cd")
        if cd_job and "steps" in cd_job:
            has_verify = any("No Dockerfile" in step.get("run", "") for step in cd_job["steps"])
            if not has_verify:
                changes.append("CD missing verification step for non-Docker project")

    # If no changes needed, workflow is already correct
    if not changes:
        return False, ["Workflow already valid, no changes needed"]

    # Generate new correct workflow
    new_workflow = _build_workflow(has_dockerfile)

    # Write updated workflow
    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(new_workflow)

    return True, changes


def _create_new_workflow(workflow_path, project_path, has_dockerfile):
    """Create a new workflow file."""
    workflow = _build_workflow(has_dockerfile)
    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(workflow)
    return ["Created new workflow"]


def generate_cicd(
    project_path,
    project_info=None,
    has_dockerfile=False,
    filename=None
):
    """
    Generate or update the CI/CD workflow.
    
    Logic:
    - If workflow exists: inspect, compare, update if needed
    - If workflow doesn't exist: create new
    - Always validate after modification
    """
    workflow_path = _get_workflow_path(project_path, filename)
    has_dockerfile = has_dockerfile or _has_dockerfile(project_path)

    existing_content = _load_existing_workflow(workflow_path)

    if existing_content:
        # Workflow exists - inspect and update if needed
        updated, changes = _update_workflow_in_place(workflow_path, project_path, has_dockerfile)
        if updated:
            print(f"Workflow updated: {', '.join(changes)}")
        else:
            print(f"Workflow unchanged: {', '.join(changes)}")
    else:
        # No workflow - create new
        changes = _create_new_workflow(workflow_path, project_path, has_dockerfile)
        print(f"Workflow created: {', '.join(changes)}")

    return workflow_path


def _ensure_requirements_txt(project_path, files):
    """
    Ensure requirements.txt exists with required dependencies.
    Returns (requirements_path, updated, dependencies)
    """
    from requirements_generator import generate_requirements
    return generate_requirements(project_path, files)


def validate_cicd(workflow_path):
    """
    Read the REAL workflow file and check it for correctness.

    Returns a list of issue strings. An empty list means the
    workflow is valid.
    """

    issues = []

    try:

        with open(
            workflow_path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

    except Exception as error:

        return [
            f"Workflow file could not be read: {error}"
        ]

    required_checks = [
        ("name: CI/CD Workflow", "workflow name"),
        ("jobs:", "jobs section"),
        ("actions/checkout@v4", "checkout v4"),
        ("actions/setup-python@v5", "setup-python v5"),
        ("python-version: '3.12'", "Python 3.12"),
        ("python -m pip install --upgrade pip", "pip upgrade"),
        ("python -m pip install -r requirements.txt", "install requirements.txt"),
        ("python -m pytest -v", "pytest via python -m"),
        ("needs: ci", "CD depends on CI"),
    ]

    for needle, label in required_checks:

        if needle not in content:

            issues.append(
                f"Missing {label} in workflow"
            )

    # --------------------------------------------------------
    # Bare "pytest" runs are rejected.
    # --------------------------------------------------------

    if re.search(
        r"run:\s*pytest\s*$",
        content,
        re.MULTILINE
    ):

        issues.append(
            "Workflow runs bare 'pytest' instead of 'python -m pytest -v'"
        )

    # --------------------------------------------------------
    # Failures must not be hidden.
    # --------------------------------------------------------

    if "|| true" in content:

        issues.append(
            "Workflow contains '|| true' which hides test failures"
        )

    if "continue-on-error: true" in content:

        issues.append(
            "Workflow contains 'continue-on-error: true' on a test step"
        )

    if "if: always()" in content:

        issues.append(
            "Workflow contains 'if: always()' which can make CI appear successful"
        )

    if (
        "pip install -r requirements.txt" in content
        and
        "python -m pip install -r requirements.txt" not in content
    ):

        issues.append(
            "requirements.txt installation does not use 'python -m pip'"
        )

    # --------------------------------------------------------
    # CD must not run on failure.
    # --------------------------------------------------------

    if "needs: ci" not in content:

        issues.append(
            "CD job is missing 'needs: ci'"
        )

    # --------------------------------------------------------
    # CD Docker validation
    # --------------------------------------------------------
    # Only validate Docker steps if the workflow appears to have a Docker job
    has_docker_job = "docker" in content.lower() and ("docker --version" in content or "docker build" in content or "apt-get" in content and "docker" in content)
    
    if "sudo apt-get update" in content and "docker" in content:
        issues.append("Workflow contains 'sudo apt-get update' for Docker installation (not needed on ubuntu-latest)")
    
    if "sudo apt-get install docker.io" in content:
        issues.append("Workflow contains 'sudo apt-get install docker.io' (not needed on ubuntu-latest)")
    
    # Only check for Docker version/build if workflow has Docker steps
    if has_docker_job:
        if "docker --version" not in content:
            issues.append("Workflow missing 'docker --version' check in CD")
        
        if "docker build -t my-image ." not in content:
            issues.append("Workflow missing 'docker build -t my-image .' in CD")

    return issues


def validate_and_repair_workflow(workflow_path, project_path, has_dockerfile, max_attempts=3):
    """
    Validate workflow and repair if needed.
    Returns True if valid, False otherwise.
    """
    for attempt in range(max_attempts):
        issues = validate_cicd(workflow_path)
        if not issues:
            return True

        print(f"\nWorkflow validation failed (attempt {attempt + 1}):")
        for issue in issues:
            print(f"  - {issue}")

        print("\nRepairing workflow...")
        generate_cicd(project_path, None, has_dockerfile, os.path.basename(workflow_path))

    return False