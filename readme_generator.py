from openrouter_agent import ask_ai
import os


def generate_readme(project_path, project_info, files=None):
    """
    Create or UPDATE the project README.md.

    If README.md already exists, the AI updates it and preserves
    useful existing documentation. It never writes a duplicate
    file such as README_v2.md.
    """

    readme_path = os.path.join(
        project_path,
        "README.md"
    )

    existing_readme = ""

    if os.path.isfile(readme_path):

        try:

            with open(
                readme_path,
                "r",
                encoding="utf-8"
            ) as file:

                existing_readme = file.read()

        except Exception:

            existing_readme = ""

    file_list = (
        "\n".join(files)
        if files
        else "Not provided"
    )

    if existing_readme.strip():

        prompt = f"""
You are an expert technical writer updating an EXISTING README.md.

The project source files may have changed. Update the README so it
accurately reflects the current state of the project.

Preserve useful existing documentation.

Update outdated information.

Add newly implemented functionality.

Do NOT remove valuable content.

Do NOT create a new file. The result must be written back to the
existing README.md file.

==================================================
PROJECT INFORMATION
==================================================

{project_info}

==================================================
PROJECT FILES
==================================================

{file_list}

==================================================
EXISTING README.md
==================================================

{existing_readme}

==================================================
REQUIREMENTS
==================================================

1. Keep the project title and description accurate.

2. Update installation instructions if they are outdated.

3. Update the run instructions if they are outdated.

4. Update the project structure section if files changed.

5. Add a section for any new functionality if missing.

6. Keep formatting clean and consistent.

7. Keep useful existing sections.

8. Return ONLY the complete updated README content.

9. Do NOT return Markdown code fences.

10. Do NOT return explanations.
"""

    else:

        prompt = f"""
You are an expert technical writer creating a README.md for a project.

==================================================
PROJECT INFORMATION
==================================================

{project_info}

==================================================
PROJECT FILES
==================================================

{file_list}

==================================================
REQUIREMENTS
==================================================

Create a complete README.md that includes:

1. Project title

2. Description

3. Technologies used

4. Installation

5. How to run

6. Project structure

7. Testing instructions (how to run the tests)

8. Docker instructions (if a Dockerfile is used)

Base the documentation only on the provided project files and
project information. Do not invent functionality.

Return ONLY the complete README content.

Do NOT return Markdown code fences.

Do NOT return explanations.
"""

    readme = ask_ai(prompt)

    readme = readme.replace(
        "```markdown",
        ""
    )

    readme = readme.replace(
        "```md",
        ""
    )

    readme = readme.replace(
        "```",
        ""
    )

    readme = readme.strip()

    with open(
        readme_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(readme)

    return readme_path
