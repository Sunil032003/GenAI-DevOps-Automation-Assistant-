"""
Repo Auditor & Discovery Agent for Forward Deployment Engineers.
Performs AST parsing, framework detection, and static security audits.
"""

import ast
import os
import re
from typing import Dict, List, Optional, Tuple

from fde_agent.llm import LLMFactory
from fde_agent.state import FDEAgentState, ProjectProfile, SecurityFinding
from fde_agent.tools.scanner import classify_files, scan_project_files


SECRET_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret|token|password|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-\.]{16,}['\"]", "Hardcoded API Key / Secret detected in source code"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI / OpenRouter API Key format detected"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token detected"),
]


def audit_file_security(file_path: str, content: str) -> List[SecurityFinding]:
    """Scan file content for credentials, shell execution, and unsafe constructs."""
    findings: List[SecurityFinding] = []

    for idx, line in enumerate(content.splitlines(), start=1):
        # Check secret patterns
        for pattern, desc in SECRET_PATTERNS:
            if re.search(pattern, line):
                findings.append(
                    SecurityFinding(
                        file_path=file_path,
                        line_number=idx,
                        severity="CRITICAL",
                        description=desc,
                        recommendation="Move sensitive credentials into environment variables (.env) or a secret manager.",
                    )
                )

        # Check unsafe shell execution
        if "shell=True" in line:
            findings.append(
                SecurityFinding(
                    file_path=file_path,
                    line_number=idx,
                    severity="HIGH",
                    description="Unsafe subprocess execution with shell=True",
                    recommendation="Pass command arguments as an array and set shell=False to prevent command injection.",
                )
            )

        if "eval(" in line or "exec(" in line:
            findings.append(
                SecurityFinding(
                    file_path=file_path,
                    line_number=idx,
                    severity="HIGH",
                    description="Dynamic code execution via eval/exec detected",
                    recommendation="Avoid eval/exec; use safe parsing libraries like ast.literal_eval.",
                )
            )

    return findings


def analyze_python_ast(content: str) -> Tuple[List[str], List[str], Optional[str]]:
    """Extract functions, classes, and detect if an entrypoint exists."""
    functions: List[str] = []
    classes: List[str] = []
    entrypoint: Optional[str] = None

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.If):
                # Detect if __name__ == '__main__':
                try:
                    test_str = ast.unparse(node.test)
                    if "__name__" in test_str and "__main__" in test_str:
                        entrypoint = "__main__ block"
                except Exception:
                    pass
    except SyntaxError:
        pass

    return functions, classes, entrypoint


def detect_frameworks(files: List[str], project_path: str) -> List[str]:
    """Identify project frameworks by inspecting imports and file names."""
    frameworks = set()
    for rel_path in files:
        if not rel_path.endswith(".py"):
            continue
        full_path = os.path.join(project_path, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "fastapi" in content:
                    frameworks.add("FastAPI")
                if "flask" in content:
                    frameworks.add("Flask")
                if "django" in content:
                    frameworks.add("Django")
                if "pytest" in content:
                    frameworks.add("pytest")
                if "torch" in content:
                    frameworks.add("PyTorch")
                if "tensorflow" in content or "keras" in content:
                    frameworks.add("TensorFlow/Keras")
                if "cv2" in content or "opencv" in content:
                    frameworks.add("OpenCV")
                if "click" in content or "argparse" in content:
                    frameworks.add("CLI Application")
                if "streamlit" in content:
                    frameworks.add("Streamlit")
                if "langchain" in content or "langgraph" in content:
                    frameworks.add("LangChain/LangGraph")
        except Exception:
            continue
    return sorted(list(frameworks))


def repo_auditor_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Repo Auditor & Discovery Agent.
    """
    project_path = state["project_path"]
    files = state.get("files") or scan_project_files(project_path)

    classified = classify_files(files)
    source_files = classified["source"]
    test_files = classified["tests"]
    config_files = classified["configs"]

    security_findings: List[SecurityFinding] = []
    detected_entrypoint: Optional[str] = None

    # Inspect source files
    for rel_path in source_files:
        full_path = os.path.join(project_path, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                findings = audit_file_security(rel_path, content)
                security_findings.extend(findings)

                _, _, ep = analyze_python_ast(content)
                if ep and not detected_entrypoint:
                    detected_entrypoint = rel_path
        except Exception:
            continue

    # Identify primary language
    ext_counts = {}
    for f in files:
        _, ext = os.path.splitext(f.lower())
        if ext:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    primary_lang = "Python" if ext_counts.get(".py", 0) > 0 else "Unknown"
    frameworks = detect_frameworks(files, project_path)

    # Determine project type
    if "FastAPI" in frameworks or "Flask" in frameworks or "Django" in frameworks:
        proj_type = "Web API / Microservice"
    elif "CLI Application" in frameworks:
        proj_type = "Command-Line Tool"
    elif "PyTorch" in frameworks or "TensorFlow/Keras" in frameworks or "OpenCV" in frameworks:
        proj_type = "Machine Learning / Computer Vision System"
    else:
        proj_type = f"{primary_lang} Application"

    summary = (
        f"Audited {len(files)} files. Identified primary language: {primary_lang}. "
        f"Project type: {proj_type}. Frameworks: {', '.join(frameworks) if frameworks else 'Standard Library'}. "
        f"Entrypoint: {detected_entrypoint or 'None specified'}. "
        f"Found {len(security_findings)} security issues."
    )

    profile = ProjectProfile(
        language=primary_lang,
        project_type=proj_type,
        frameworks=frameworks,
        entrypoint=detected_entrypoint,
        source_files=source_files,
        test_files=test_files,
        config_files=config_files,
        security_findings=security_findings,
        summary=summary,
    )

    return {
        "files": files,
        "profile": profile,
        "status": "DISCOVERY_COMPLETED",
    }

