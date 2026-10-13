from openrouter_agent import ask_ai
import os


INSTRUCTION_WORDS = (
    "FROM",
    "RUN",
    "CMD",
    "COPY",
    "WORKDIR",
    "ENV",
    "EXPOSE",
    "ARG",
    "ENTRYPOINT",
    "LABEL",
    "VOLUME",
    "USER",
    "ADD"
)


def _strip_inline_comments(dockerfile):
    """
    Remove trailing "# comments" from Docker instruction lines.
    Docker only allows comments on their own line; an inline
    comment after an instruction makes the file invalid.
    """

    sanitized = []

    for line in dockerfile.splitlines():

        stripped = line.strip()

        if (
            stripped
            and not stripped.startswith("#")
            and stripped.startswith(INSTRUCTION_WORDS)
        ):

            comment_index = line.find("#")

            if comment_index != -1:

                line = line[:comment_index].rstrip()

        sanitized.append(line)

    return "\n".join(sanitized)


def generate_dockerfile(project_path, project_info):

    prompt = f"""
Create a simple Dockerfile for this project.

Project information:
{project_info}

Requirements:
- Use Python 3.12
- Install dependencies from requirements.txt
- Copy the project files
- Keep the Dockerfile simple
- Do NOT add comments to the same line as a Docker instruction
- Do NOT wrap the content in code fences

Return only the Dockerfile content.
"""

    dockerfile = ask_ai(prompt)

    dockerfile = dockerfile.replace(
        "```Dockerfile",
        ""
    )

    dockerfile = dockerfile.replace(
        "```dockerfile",
        ""
    )

    dockerfile = dockerfile.replace(
        "```",
        ""
    )

    dockerfile = _strip_inline_comments(
        dockerfile
    )

    dockerfile = dockerfile.strip()

    dockerfile_path = os.path.join(project_path, "Dockerfile")

    with open(dockerfile_path, "w", encoding="utf-8") as file:
        file.write(dockerfile)

    return dockerfile_path