"""Unit tests for FDE state and Pydantic schemas."""

import pytest
from fde_agent.state import (
    DeploymentReadinessReport,
    DependencyAudit,
    ProjectProfile,
    RepairRecord,
    SecurityFinding,
    TestExecutionResult,
)


def test_security_finding_model():
    finding = SecurityFinding(
        file_path="config.py",
        line_number=12,
        severity="CRITICAL",
        description="Leaked token",
        recommendation="Use env vars",
    )
    assert finding.severity == "CRITICAL"
    assert finding.line_number == 12


def test_project_profile_defaults():
    profile = ProjectProfile(
        language="Python",
        project_type="Web API",
        frameworks=["FastAPI"],
    )
    assert profile.language == "Python"
    assert profile.frameworks == ["FastAPI"]
    assert profile.security_findings == []


def test_test_execution_result_model():
    result = TestExecutionResult(
        success=True,
        return_code=0,
        total_tests=5,
        passed_count=5,
        failed_count=0,
        failed_test_names=[],
        output="5 passed in 0.2s",
        failure_category="NONE",
    )
    assert result.success is True
    assert result.total_tests == 5


def test_repair_record_model():
    rec = RepairRecord(
        attempt=1,
        target_file="app.py",
        repair_type="SOURCE",
        diagnosis="Fixed index out of bounds",
        patch_applied=True,
        syntax_valid=True,
    )
    assert rec.attempt == 1
    assert rec.patch_applied is True


def test_deployment_readiness_report_validation():
    report = DeploymentReadinessReport(
        overall_score=95,
        readiness_tier="PRODUCTION_READY",
        executive_summary="All checks green.",
        security_score=30,
        test_pass_rate=100.0,
        container_readiness="READY",
        cicd_readiness="READY",
    )
    assert report.overall_score == 95
    assert report.readiness_tier == "PRODUCTION_READY"

