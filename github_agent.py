import os
import shutil
import subprocess


# ============================================================
# FIND GITHUB CLI
# ============================================================

def find_gh():
    """
    Find GitHub CLI executable on Windows/Linux.
    """

    # First check PATH
    gh_path = shutil.which("gh")

    if gh_path:
        return gh_path

    # Windows locations
    windows_paths = [
        r"C:\Program Files\GitHub CLI\gh.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe"
        ),
    ]

    for path in windows_paths:
        if os.path.isfile(path):
            return path

    # Linux common location
    linux_paths = [
        "/usr/bin/gh",
        "/usr/local/bin/gh",
    ]

    for path in linux_paths:
        if os.path.isfile(path):
            return path

    return None


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(command, cwd=None):
    """
    Run a shell command safely.
    """

    try:

        command = list(command)

        # If using GitHub CLI, find actual executable
        if command and command[0] == "gh":

            gh_path = find_gh()

            if gh_path is None:

                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": (
                        "GitHub CLI (gh) could not "
                        "be found."
                    )
                }

            command[0] = gh_path

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except FileNotFoundError as error:

        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(error)
        }

    except Exception as error:

        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(error)
        }


# ============================================================
# CHECK GITHUB CLI
# ============================================================

def check_github_cli():

    gh_path = find_gh()

    if gh_path is None:

        return {
            "success": False,
            "path": None,
            "message": (
                "GitHub CLI is not installed "
                "or could not be found."
            )
        }

    result = run_command(
        [
            "gh",
            "--version"
        ]
    )

    return {
        "success": result["success"],
        "path": gh_path,
        "message": (
            result["stdout"]
            if result["success"]
            else result["stderr"]
        )
    }


# ============================================================
# CHECK GITHUB AUTHENTICATION
# ============================================================

def check_github_authentication():

    return run_command(
        [
            "gh",
            "auth",
            "status"
        ]
    )


# ============================================================
# SETUP GIT AUTHENTICATION
# ============================================================

def setup_git_authentication():

    return run_command(
        [
            "gh",
            "auth",
            "setup-git"
        ]
    )


# ============================================================
# CHECK WHETHER PROJECT IS A GIT REPOSITORY
# ============================================================

def is_git_repository(project_path):

    git_directory = os.path.join(
        project_path,
        ".git"
    )

    return os.path.isdir(
        git_directory
    )


# ============================================================
# INITIALIZE GIT
# ============================================================

def initialize_git_repository(project_path):

    print(
        "\nInitializing local Git repository..."
    )

    result = run_command(
        [
            "git",
            "init"
        ],
        cwd=project_path
    )

    if result["success"]:

        print(
            "Git repository initialized."
        )

    return result


# ============================================================
# CHECK GIT USER
# ============================================================

def check_git_user(project_path):

    name_result = run_command(
        [
            "git",
            "config",
            "user.name"
        ],
        cwd=project_path
    )

    email_result = run_command(
        [
            "git",
            "config",
            "user.email"
        ],
        cwd=project_path
    )

    name_exists = (
        name_result["success"]
        and
        bool(name_result["stdout"])
    )

    email_exists = (
        email_result["success"]
        and
        bool(email_result["stdout"])
    )

    return (
        name_exists
        and
        email_exists
    )


# ============================================================
# CONFIGURE GIT USER
# ============================================================

def setup_git_user(project_path):

    print(
        "\nGit user configuration is missing."
    )

    name = input(
        "Enter Git user name: "
    ).strip()

    email = input(
        "Enter Git user email: "
    ).strip()

    if not name or not email:

        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": (
                "Git user name and email "
                "are required."
            )
        }

    name_result = run_command(
        [
            "git",
            "config",
            "user.name",
            name
        ],
        cwd=project_path
    )

    if not name_result["success"]:
        return name_result

    email_result = run_command(
        [
            "git",
            "config",
            "user.email",
            email
        ],
        cwd=project_path
    )

    return email_result


# ============================================================
# GIT ADD
# ============================================================

def git_add_files(project_path):

    print(
        "\nAdding project files to Git..."
    )

    return run_command(
        [
            "git",
            "add",
            "."
        ],
        cwd=project_path
    )


# ============================================================
# GIT STATUS
# ============================================================

def git_status(project_path):

    return run_command(
        [
            "git",
            "status",
            "--porcelain"
        ],
        cwd=project_path
    )


# ============================================================
# CHECK WHETHER COMMITS EXIST
# ============================================================

def has_git_commits(project_path):

    result = run_command(
        [
            "git",
            "rev-parse",
            "--verify",
            "HEAD"
        ],
        cwd=project_path
    )

    return result["success"]


# ============================================================
# CREATE COMMIT
# ============================================================

def create_commit(
    project_path,
    message
):

    print(
        f"\nCreating Git commit: {message}"
    )

    return run_command(
        [
            "git",
            "commit",
            "-m",
            message
        ],
        cwd=project_path
    )


# ============================================================
# GET EXISTING REMOTE
# ============================================================

def get_git_remote(
    project_path,
    remote_name="origin"
):

    return run_command(
        [
            "git",
            "remote",
            "get-url",
            remote_name
        ],
        cwd=project_path
    )


# ============================================================
# GET REMOTE URL (STRING OR NONE)
# ============================================================

def get_remote_url(project_path):

    result = get_git_remote(
        project_path,
        "origin"
    )

    if result["success"]:
        return result["stdout"]

    return None


# ============================================================
# ENSURE GITIGNORE PROTECTS SECRETS
# ============================================================

def ensure_gitignore(project_path):
    """
    Make sure common secret/environment files cannot be committed.
    Appends entries to .gitignore without removing existing rules.
    """

    gitignore_path = os.path.join(
        project_path,
        ".gitignore"
    )

    existing_rules = ""

    if os.path.isfile(gitignore_path):

        try:

            with open(
                gitignore_path,
                "r",
                encoding="utf-8"
            ) as file:

                existing_rules = file.read()

        except Exception:

            existing_rules = ""

    required_rules = [
        ".env",
        "*.env",
        ".env.*",
        "!.env.example",
        "__pycache__/",
        ".pytest_cache/",
        ".venv/",
        "venv/",
        "node_modules/"
    ]

    missing_rules = [
        rule
        for rule in required_rules
        if rule not in existing_rules
    ]

    if not missing_rules:
        return gitignore_path

    new_rules = "\n".join(missing_rules)

    with open(
        gitignore_path,
        "a",
        encoding="utf-8"
    ) as file:

        if existing_rules.strip():
            file.write("\n")

        file.write("\n# Added by Git Pilot\n")
        file.write(new_rules)
        file.write("\n")

    return gitignore_path


# ============================================================
# ADD REMOTE
# ============================================================

def add_git_remote(
    project_path,
    remote_name,
    repository_url
):

    return run_command(
        [
            "git",
            "remote",
            "add",
            remote_name,
            repository_url
        ],
        cwd=project_path
    )


# ============================================================
# UPDATE REMOTE
# ============================================================

def update_git_remote(
    project_path,
    remote_name,
    repository_url
):

    return run_command(
        [
            "git",
            "remote",
            "set-url",
            remote_name,
            repository_url
        ],
        cwd=project_path
    )


# ============================================================
# CONFIGURE ORIGIN
# ============================================================

def configure_origin(
    project_path,
    repository_url
):

    print(
        "\nConfiguring GitHub remote..."
    )

    existing_remote = get_git_remote(
        project_path,
        "origin"
    )

    # --------------------------------------------------------
    # Origin already exists
    # --------------------------------------------------------

    if existing_remote["success"]:

        old_url = existing_remote["stdout"]

        print(
            "\nExisting origin found:"
        )

        print(
            old_url
        )

        # If already points to the new repository
        if old_url.rstrip("/") == repository_url.rstrip("/"):

            print(
                "\nOrigin already points "
                "to the correct repository."
            )

            return {
                "success": True,
                "repository_url": repository_url
            }

        print(
            "\nUpdating origin..."
        )

        result = update_git_remote(
            project_path,
            "origin",
            repository_url
        )

    # --------------------------------------------------------
    # Origin does not exist
    # --------------------------------------------------------

    else:

        print(
            "\nNo origin found."
        )

        print(
            "Adding origin..."
        )

        result = add_git_remote(
            project_path,
            "origin",
            repository_url
        )

    if not result["success"]:

        return {
            "success": False,
            "repository_url": repository_url,
            "message": (
                result["stderr"]
                or result["stdout"]
            )
        }

    print(
        "\nOrigin configured:"
    )

    print(
        repository_url
    )

    return {
        "success": True,
        "repository_url": repository_url
    }


# ============================================================
# CREATE GITHUB REPOSITORY
# ============================================================

def create_github_repository(
    project_path,
    repository_name,
    visibility="private"
):

    print(
        "\nCreating GitHub repository..."
    )

    if visibility == "public":

        visibility_flag = "--public"

    else:

        visibility_flag = "--private"

    # IMPORTANT:
    #
    # We do NOT use:
    #
    # --source
    # --remote origin
    # --push
    #
    # because we want to control the remote ourselves.

    result = run_command(
        [
            "gh",
            "repo",
            "create",
            repository_name,
            visibility_flag
        ],
        cwd=project_path
    )

    return result


# ============================================================
# GET GITHUB REPOSITORY URL
# ============================================================

def get_repository_url(
    repository_name
):

    result = run_command(
        [
            "gh",
            "repo",
            "view",
            repository_name,
            "--json",
            "url",
            "--jq",
            ".url"
        ]
    )

    return result


# ============================================================
# PUSH PROJECT
# ============================================================

def push_project(
    project_path
):

    print(
        "\nPushing project to GitHub..."
    )

    result = run_command(
        [
            "git",
            "push",
            "-u",
            "origin",
            "HEAD"
        ],
        cwd=project_path
    )

    return result


# ============================================================
# MAIN PUBLISH FUNCTION
# ============================================================

def publish_project(
    project_path,
    repository_name=None,
    visibility="private",
    repository_url=None
):

    print(
        "\n=========================================="
    )

    print(
        "          GITHUB PUBLISHING"
    )

    print(
        "=========================================="
    )

    # ========================================================
    # 1. CHECK GITHUB CLI
    # ========================================================

    print(
        "\nChecking GitHub CLI..."
    )

    cli_result = check_github_cli()

    if not cli_result["success"]:

        return {
            "success": False,
            "stage": "github_cli",
            "message": cli_result["message"]
        }

    print(
        "GitHub CLI found:"
    )

    print(
        cli_result["path"]
    )


    # ========================================================
    # 2. CHECK AUTHENTICATION
    # ========================================================

    print(
        "\nChecking GitHub authentication..."
    )

    auth_result = (
        check_github_authentication()
    )

    if not auth_result["success"]:

        return {
            "success": False,
            "stage": "authentication",
            "message": (
                "GitHub CLI is not authenticated. "
                "Run 'gh auth login' first."
            )
        }

    print(
        "GitHub authentication successful."
    )


    # ========================================================
    # 3. CONFIGURE GIT AUTHENTICATION
    # ========================================================

    print(
        "\nConfiguring Git authentication..."
    )

    git_auth_result = (
        setup_git_authentication()
    )

    if not git_auth_result["success"]:

        return {
            "success": False,
            "stage": "git_authentication",
            "message": (
                git_auth_result["stderr"]
                or git_auth_result["stdout"]
            )
        }

    print(
        "Git authentication configured."
    )


    # ========================================================
    # 4. CHECK / INITIALIZE GIT
    # ========================================================

    if not is_git_repository(
        project_path
    ):

        init_result = (
            initialize_git_repository(
                project_path
            )
        )

        if not init_result["success"]:

            return {
                "success": False,
                "stage": "git_init",
                "message": (
                    init_result["stderr"]
                    or init_result["stdout"]
                )
            }

    else:

        print(
            "\nLocal Git repository already exists."
        )


    # ========================================================
    # 5. DETECT EXISTING REMOTE
    # ========================================================
    # Only use existing remote if user didn't explicitly choose
    # to create a new repository (repository_name provided).
    # If repository_name is provided, we create a new repo instead.

    if repository_url is None and repository_name is None:
        existing_remote = get_remote_url(project_path)

        if existing_remote:
            print(
                "\nExisting GitHub remote detected:"
            )

            print(
                existing_remote
            )

            print(
                "Pushing to the existing repository."
            )

            repository_url = existing_remote


    # ========================================================
    # 6. CHECK GIT USER
    # ========================================================

    if not check_git_user(
        project_path
    ):

        config_result = (
            setup_git_user(
                project_path
            )
        )

        if not config_result["success"]:

            return {
                "success": False,
                "stage": "git_configuration",
                "message": (
                    config_result["stderr"]
                    or config_result["stdout"]
                )
            }

    else:

        print(
            "\nGit user configuration found."
        )


    # ========================================================
    # 7. ENSURE SECRETS ARE IGNORED
    # ========================================================

    ensure_gitignore(
        project_path
    )


    # ========================================================
    # 8. ADD ALL PROJECT FILES
    # ========================================================

    add_result = git_add_files(
        project_path
    )

    if not add_result["success"]:

        return {
            "success": False,
            "stage": "git_add",
            "message": (
                add_result["stderr"]
                or add_result["stdout"]
            )
        }

    print(
        "Project files added."
    )


    # ========================================================
    # 9. CREATE COMMIT
    # ========================================================

    status_result = git_status(
        project_path
    )

    if not status_result["success"]:

        return {
            "success": False,
            "stage": "git_status",
            "message": (
                status_result["stderr"]
                or status_result["stdout"]
            )
        }


    if status_result["stdout"]:

        # Determine whether this is the first commit
        if has_git_commits(project_path):

            commit_message = (
                "Update project generated by Git Pilot"
            )

        else:

            commit_message = (
                "Initial commit generated by Git Pilot"
            )


        commit_result = create_commit(
            project_path,
            commit_message
        )


        if not commit_result["success"]:

            return {
                "success": False,
                "stage": "git_commit",
                "message": (
                    commit_result["stderr"]
                    or commit_result["stdout"]
                )
            }

        print(
            "Git commit created."
        )

    else:

        print(
            "\nNo changes to commit."
        )


    # ========================================================
    # 10. CREATE GITHUB REPOSITORY ONLY WHEN NEEDED
    # ========================================================

    if repository_url is None:

        if not repository_name:

            return {
                "success": False,
                "stage": "repository_target",
                "message": (
                    "No repository name or existing "
                    "repository URL provided."
                )
            }

        repo_result = (
            create_github_repository(
                project_path,
                repository_name,
                visibility
            )
        )


        if not repo_result["success"]:

            error_message = (
                repo_result["stderr"]
                or repo_result["stdout"]
            )

            # If repository already exists,
            # we can continue.
            if (
                "already exists" in
                error_message.lower()
            ):

                print(
                    "\nRepository already exists."
                )

            else:

                return {
                    "success": False,
                    "stage": "repository_creation",
                    "message": error_message
                }

        else:

            print(
                "\nGitHub repository created."
            )


        # ========================================================
        # 11. GET REPOSITORY URL
        # ========================================================

        url_result = get_repository_url(
            repository_name
        )


        if not url_result["success"]:

            return {
                "success": False,
                "stage": "repository_url",
                "message": (
                    url_result["stderr"]
                    or url_result["stdout"]
                )
            }


        repository_url = (
            url_result["stdout"]
        )

    else:

        print(
            "\nUsing existing repository:"
        )

        print(
            repository_url
        )

        print(
            "No new repository will be created."
        )


    # ========================================================
    # 12. CONFIGURE ORIGIN
    # ========================================================

    remote_result = configure_origin(
        project_path,
        repository_url
    )


    if not remote_result["success"]:

        return {
            "success": False,
            "stage": "remote_configuration",
            "message": remote_result["message"]
        }


    # ========================================================
    # 13. PUSH
    # ========================================================

    push_result = push_project(
        project_path
    )


    if not push_result["success"]:

        return {
            "success": False,
            "stage": "git_push",
            "message": (
                push_result["stderr"]
                or push_result["stdout"]
            )
        }


    print(
        "\nProject pushed successfully."
    )


    # ========================================================
    # 14. FINAL RESULT
    # ========================================================

    return {
        "success": True,
        "stage": "completed",
        "message": (
            "Project successfully "
            "published to GitHub."
        ),
        "repository_url": repository_url
    }