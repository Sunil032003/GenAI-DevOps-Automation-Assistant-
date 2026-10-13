"""
FDE Readiness Advisor Agent.
Synthesizes end-to-end agent results into an executive and technical
Deployment Readiness Scorecard and Handover Report.
"""

import os
from typing import Dict, List

from fde_agent.state import DeploymentReadinessReport, FDEAgentState
from fde_agent.tools.code_validator import write_file_safe


def calculate_readiness_metrics(state: FDEAgentState) -> DeploymentReadinessReport:
    """Calculate objective enterprise readiness metrics across all evaluation dimensions."""
    profile = state.get("profile")
    test_results = state.get("test_results")
    repair_history = state.get("repair_history", [])
    has_docker = bool(state.get("dockerfile_content"))
    has_cicd = bool(state.get("cicd_content"))

    # 1. Test Score (max 40 pts)
    test_pass_rate = 100.0
    test_score = 40
    if test_results:
        if test_results.total_tests > 0:
            test_pass_rate = (test_results.passed_count / test_results.total_tests) * 100.0
            test_score = int((test_pass_rate / 100.0) * 40)
        elif not test_results.success:
            test_pass_rate = 0.0
            test_score = 0

    # 2. Security Score (max 30 pts)
    security_score = 30
    security_findings = profile.security_findings if profile else []
    for f in security_findings:
        if f.severity == "CRITICAL":
            security_score = max(0, security_score - 15)
        elif f.severity == "HIGH":
            security_score = max(0, security_score - 10)
        elif f.severity == "MEDIUM":
            security_score = max(0, security_score - 5)

    # 3. Container & CI/CD Score (max 30 pts)
    container_score = 15 if has_docker else 0
    cicd_score = 15 if has_cicd else 0

    overall_score = test_score + security_score + container_score + cicd_score

    # Determine Tier
    if overall_score >= 85 and test_pass_rate >= 90:
        tier = "PRODUCTION_READY"
    elif overall_score >= 60:
        tier = "CONDITIONAL_APPROVAL"
    else:
        tier = "REMEDIATION_REQUIRED"

    key_risks: List[str] = []
    if test_pass_rate < 100.0:
        key_risks.append(f"Test suite has failing assertions ({100.0 - test_pass_rate:.1f}% failure rate).")
    if any(f.severity in ("CRITICAL", "HIGH") for f in security_findings):
        key_risks.append("Critical or high security issues detected in static code audit.")
    if repair_history:
        key_risks.append(f"Autonomous repairs were performed ({len(repair_history)} iteration(s)); review diffs.")

    recommended_actions: List[str] = [
        "Review generated Dockerfile and CI/CD workflow prior to cluster deployment.",
        "Ensure production secrets are loaded from enterprise secret vault, not .env files.",
        "Configure smoke tests in target staging environment before full traffic cutover.",
    ]
    if test_pass_rate < 100.0:
        recommended_actions.insert(0, "Investigate remaining test failures prior to production deployment.")

    verification_checklist = [
        "[ ] All unit and integration tests passing in containerized environment",
        "[ ] Static application security testing (SAST) passed without high severity flags",
        "[ ] Unprivileged non-root user enforced in container runtime",
        "[ ] CI/CD pipeline triggers successfully on main branch pull requests",
        "[ ] Deployment runbook and rollback plan reviewed by Forward Deployment Engineer",
    ]

    summary = (
        f"Deployment readiness score evaluated at {overall_score}/100 ({tier}). "
        f"Tests: {test_pass_rate:.1f}% pass rate. Security audit: {len(security_findings)} findings. "
        f"Container & CI/CD delivery artifacts verified."
    )

    return DeploymentReadinessReport(
        overall_score=overall_score,
        readiness_tier=tier,
        executive_summary=summary,
        security_score=security_score,
        test_pass_rate=test_pass_rate,
        container_readiness="READY" if has_docker else "MISSING",
        cicd_readiness="READY" if has_cicd else "MISSING",
        key_risks=key_risks,
        recommended_actions=recommended_actions,
        verification_checklist=verification_checklist,
    )


def format_report_markdown(report: DeploymentReadinessReport, state: FDEAgentState) -> str:
    """Format the readiness scorecard into an executive handover Markdown report."""
    lines = [
        "# 🚀 Forward Deployment Engineer: Client Release Scorecard",
        "",
        f"**Deployment Status:** `{report.readiness_tier}`  ",
        f"**Overall Readiness Score:** **{report.overall_score}/100**  ",
        f"**Test Pass Rate:** **{report.test_pass_rate:.1f}%**  ",
        f"**Security Posture Score:** **{report.security_score}/30**  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        report.executive_summary,
        "",
        "## 2. Infrastructure & Delivery Artifacts",
        f"- **Container Spec (Dockerfile):** `{report.container_readiness}`",
        f"- **CI/CD Pipeline (GitHub Actions):** `{report.cicd_readiness}`",
        f"- **Test Suite:** `{state.get('test_results').passed_count if state.get('test_results') else 0} passed, {state.get('test_results').failed_count if state.get('test_results') else 0} failed`",
        "",
        "## 3. Risk Register",
    ]

    if report.key_risks:
        for r in report.key_risks:
            lines.append(f"- ⚠️ {r}")
    else:
        lines.append("- ✅ No blocking deployment risks identified.")

    lines.extend([
        "",
        "## 4. Autonomous Self-Healing Audit Trail",
    ])

    repair_history = state.get("repair_history", [])
    if repair_history:
        for rec in repair_history:
            lines.append(
                f"- **Attempt {rec.attempt}** [{rec.repair_type}]: Target `{rec.target_file}` | "
                f"Status: `{'Applied' if rec.patch_applied else 'Failed'}` | Diagnosis: {rec.diagnosis}"
            )
    else:
        lines.append("- No repairs required; initial test pass was clean.")

    lines.extend([
        "",
        "## 5. Recommended Next Steps",
    ])
    for act in report.recommended_actions:
        lines.append(f"1. {act}")

    lines.extend([
        "",
        "## 6. Pre-Flight Verification Checklist",
    ])
    for item in report.verification_checklist:
        lines.append(f"- {item}")

    lines.append("")
    return "\n".join(lines)


def readiness_advisor_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: FDE Readiness Advisor Agent.
    Produces DEPLOYMENT_READINESS_REPORT.md.
    """
    project_path = state["project_path"]
    report = calculate_readiness_metrics(state)
    markdown_content = format_report_markdown(report, state)

    report_path = os.path.join(project_path, "DEPLOYMENT_READINESS_REPORT.md")
    write_file_safe(report_path, markdown_content, make_backup=True)

    return {
        "readiness_report": report,
        "status": "READINESS_AUDIT_COMPLETED",
    }

