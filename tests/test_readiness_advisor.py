"""Unit tests for FDE Readiness Advisor and scoring logic."""

from fde_agent.agents.readiness_advisor import calculate_readiness_metrics
from fde_agent.state import FDEAgentState, ProjectProfile, SecurityFinding, TestExecutionResult


def test_calculate_readiness_perfect_score():
    state: FDEAgentState = {
        "project_path": ".",
        "profile": ProjectProfile(
            language="Python",
            project_type="Web Service",
            security_findings=[],
        ),
        "test_results": TestExecutionResult(
            success=True,
            return_code=0,
            total_tests=10,
            passed_count=10,
            failed_count=0,
            output="10 passed",
        ),
        "dockerfile_content": "FROM python:3.11-slim\n",
        "cicd_content": "name: CI/CD\n",
        "repair_history": [],
    }

    report = calculate_readiness_metrics(state)
    assert report.overall_score == 100
    assert report.readiness_tier == "PRODUCTION_READY"
    assert report.test_pass_rate == 100.0
    assert report.container_readiness == "READY"
    assert report.cicd_readiness == "READY"


def test_calculate_readiness_with_security_and_failing_tests():
    state: FDEAgentState = {
        "project_path": ".",
        "profile": ProjectProfile(
            language="Python",
            project_type="Web Service",
            security_findings=[
                SecurityFinding(
                    file_path="app.py",
                    severity="CRITICAL",
                    description="Exposed token",
                    recommendation="Remove token",
                )
            ],
        ),
        "test_results": TestExecutionResult(
            success=False,
            return_code=1,
            total_tests=10,
            passed_count=5,
            failed_count=5,
            output="5 failed",
        ),
        "dockerfile_content": None,
        "cicd_content": None,
        "repair_history": [],
    }

    report = calculate_readiness_metrics(state)
    # Test score: 50% of 40 = 20. Security: 30 - 15 = 15. Docker: 0. CI/CD: 0. Total = 35.
    assert report.overall_score == 35
    assert report.readiness_tier == "REMEDIATION_REQUIRED"
    assert report.test_pass_rate == 50.0

