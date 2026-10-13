"""
Terminal Presentation and Rich Console Utilities for FDE Multi-Agent System.
Clean ASCII symbols for cross-platform and Windows compatibility.
"""

import sys
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fde_agent.state import DeploymentReadinessReport, FDEAgentState, ProjectProfile

# Ensure UTF-8 output when possible on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True, soft_wrap=True)


def print_banner() -> None:
    """Print executive Forward Deployment Engineer banner."""
    console.print(
        Panel.fit(
            "[bold cyan]FORWARD DEPLOYMENT ENGINEER (FDE) AGENTIC PLATFORM[/bold cyan]\n"
            "[dim]Production Multi-Agent System | LangGraph & LangChain Orchestration[/dim]",
            border_style="cyan",
        )
    )


def print_profile(profile: ProjectProfile) -> None:
    """Display project discovery summary."""
    table = Table(title="[DISCOVERY] Repository Architecture Profile", border_style="blue")
    table.add_column("Property", style="bold white", width=22)
    table.add_column("Details", style="cyan")

    table.add_row("Primary Language", profile.language)
    table.add_row("Project Type", profile.project_type)
    table.add_row("Frameworks", ", ".join(profile.frameworks) if profile.frameworks else "None detected")
    table.add_row("Detected Entrypoint", profile.entrypoint or "None specified")
    table.add_row("Source Files Count", str(len(profile.source_files)))
    table.add_row("Test Files Count", str(len(profile.test_files)))
    table.add_row(
        "Security Findings",
        f"[bold red]{len(profile.security_findings)}[/bold red]" if profile.security_findings else "[green]0 (Clean)[/green]",
    )

    console.print(table)


def print_test_results(state: FDEAgentState) -> None:
    """Display test execution telemetry."""
    results = state.get("test_results")
    if not results:
        console.print("[yellow]No test results available.[/yellow]")
        return

    status_badge = "[bold green]PASSED[/bold green]" if results.success else "[bold red]FAILED[/bold red]"
    panel_content = (
        f"Status: {status_badge} (Exit code: {results.return_code})\n"
        f"Total Tests Executed: [bold]{results.total_tests}[/bold]\n"
        f"Passed: [green]{results.passed_count}[/green] | Failed: [red]{results.failed_count}[/red]\n"
        f"Failure Category: [yellow]{results.failure_category}[/yellow]"
    )

    if results.failed_test_names:
        panel_content += "\n\n[bold red]Failed Test Cases:[/bold red]\n"
        for name in results.failed_test_names:
            panel_content += f"  - {name}\n"

    console.print(Panel(panel_content, title="[QA] Pytest Execution Telemetry", border_style="green" if results.success else "red"))


def print_repairs(repair_history: List) -> None:
    """Display self-healing reflection history."""
    if not repair_history:
        console.print("[dim]No repairs triggered (Clean test pass).[/dim]")
        return

    table = Table(title="[HEAL] Autonomous Self-Healing Audit Trail", border_style="magenta")
    table.add_column("Attempt", justify="center", width=8)
    table.add_column("Type", width=10)
    table.add_column("Target File", style="cyan")
    table.add_column("Applied", justify="center", width=10)
    table.add_column("Diagnosis / Root Cause", style="dim")

    for r in repair_history:
        applied_str = "[green]Yes[/green]" if r.patch_applied else "[red]No[/red]"
        table.add_row(
            str(r.attempt),
            r.repair_type,
            r.target_file,
            applied_str,
            r.diagnosis[:60] + ("..." if len(r.diagnosis) > 60 else ""),
        )

    console.print(table)


def print_readiness_scorecard(report: DeploymentReadinessReport) -> None:
    """Display the executive handover scorecard."""
    color = "green" if report.readiness_tier == "PRODUCTION_READY" else "yellow" if report.readiness_tier == "CONDITIONAL_APPROVAL" else "red"

    score_panel = (
        f"[bold {color}]READINESS TIER: {report.readiness_tier}[/bold {color}]\n"
        f"Overall Readiness Score: [bold {color}]{report.overall_score}/100[/bold {color}]\n"
        f"Test Pass Rate: {report.test_pass_rate:.1f}%\n"
        f"Security Posture Score: {report.security_score}/30\n"
        f"Containerization Status: {report.container_readiness}\n"
        f"CI/CD Pipeline Status: {report.cicd_readiness}\n\n"
        f"[bold]Executive Summary:[/bold]\n{report.executive_summary}"
    )

    console.print(Panel(score_panel, title="[SCORECARD] Forward Deployment Handover Report", border_style=color))

