"""
Documentation Engineer Agent for Forward Deployment Engineers.
Generates comprehensive technical README.md for enterprise handovers.
"""

import os
from typing import Dict

from fde_agent.llm import LLMFactory
from fde_agent.state import FDEAgentState
from fde_agent.tools.code_validator import clean_code_fences, write_file_safe


DOC_SYSTEM_PROMPT = """
You are a Lead Forward Deployment Engineer and Technical Architect.
Your task is to write a comprehensive, professional README.md for a deployed client application.

SECTIONS TO INCLUDE:
1. # Project Overview & Architecture (Include high-level overview).
2. ## System Architecture (ASCII diagram or clear component list).
3. ## Prerequisites & Environment Configuration (Document required .env variables).
4. ## Installation & Setup (Local virtualenv setup, pip install).
5. ## Automated Testing & Quality Assurance (Running pytest, test plan highlights).
6. ## Containerization & Docker Deployment (Build & run commands with port mappings).
7. ## CI/CD Pipeline (GitHub Actions overview).
8. ## Forward Deployment Handover & Maintenance Runbook.

Return ONLY clean GitHub-flavored Markdown. Do not wrap the whole document in ```markdown code fences.
"""


def documentation_engineer_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Documentation Engineer Agent.
    Updates or generates the project README.md.
    """
    project_path = state["project_path"]
    profile = state.get("profile")
    dependencies = state.get("dependencies")

    readme_path = os.path.join(project_path, "README.md")
    existing_readme = ""
    if os.path.isfile(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                existing_readme = f.read()
        except Exception:
            pass

    proj_type = profile.project_type if profile else "Python Enterprise Project"
    frameworks = ", ".join(profile.frameworks) if profile and profile.frameworks else "Standard Library"
    deps = ", ".join(dependencies.final_requirements[:10]) if dependencies else "Standard dependencies"

    prompt = f"""
Project Type: {proj_type}
Frameworks: {frameworks}
Key Dependencies: {deps}

Existing Documentation:
```markdown
{existing_readme[:2000] if existing_readme else "No existing documentation."}
```

Write or update the complete, production-ready README.md for client deployment handover.
"""

    raw_response = LLMFactory.invoke_with_fallback(
        prompt=prompt,
        system_instruction=DOC_SYSTEM_PROMPT,
        max_tokens=4096,
    )

    readme_content = clean_code_fences(raw_response, "markdown")
    if not readme_content or len(readme_content) < 50:
        readme_content = raw_response.strip()

    write_file_safe(readme_path, readme_content, make_backup=bool(existing_readme))

    return {
        "readme_path": readme_path,
        "readme_content": readme_content,
        "status": "DOCUMENTATION_UPDATED",
    }

