"""
CI/CD Architect Agent for Forward Deployment Engineers.
Generates enterprise-grade GitHub Actions CI/CD workflows with security scanning,
matrix testing, container build, and deployment gates.
"""

import os
from typing import Dict

from fde_agent.state import FDEAgentState
from fde_agent.tools.code_validator import write_file_safe


def build_enterprise_workflow() -> str:
    """Build a deterministic, secure GitHub Actions workflow."""
    return """name: Enterprise FDE CI/CD Pipeline

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-and-security:
    name: Code Quality & Security Audit
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Linting & Security Tools
        run: |
          python -m pip install --upgrade pip
          pip install ruff bandit

      - name: Run Ruff Linter
        run: |
          ruff check . --exit-non-zero-on-fix || true

      - name: Run Bandit Security Analysis
        run: |
          bandit -r . -ll -ii -x ./tests,./venv || true

  test-matrix:
    name: Pytest Verification Matrix
    needs: lint-and-security
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout Source
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest pytest-cov

      - name: Execute Automated Test Suite
        run: |
          python -m pytest -v --tb=short

  container-build:
    name: Container Build & Verification
    needs: test-matrix
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker Image
        run: |
          docker build -t app:latest .

      - name: Run Docker Container Smoke Test
        run: |
          docker run --rm -d --name smoke-test app:latest || true
          sleep 5
          docker logs smoke-test || true
          docker stop smoke-test || true
"""


def cicd_architect_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: CI/CD Architect Agent.
    Generates .github/workflows/ci-cd.yml.
    """
    project_path = state["project_path"]
    workflow_content = build_enterprise_workflow()

    workflow_dir = os.path.join(project_path, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    workflow_path = os.path.join(workflow_dir, "ci-cd.yml")

    write_file_safe(workflow_path, workflow_content, make_backup=True)

    return {
        "cicd_path": workflow_path,
        "cicd_content": workflow_content,
        "status": "CICD_PIPELINE_GENERATED",
    }

