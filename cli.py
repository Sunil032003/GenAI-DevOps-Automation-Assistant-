"""
Forward Deployment Engineer (FDE) Multi-Agent CLI.
Orchestrated via LangGraph & LangChain.
"""

import argparse
import os
import sys
import uuid

from fde_agent.config import config
from fde_agent.graph.workflow import build_fde_graph
from fde_agent.state import FDEAgentState
from fde_agent.ui.console import (
    console,
    print_banner,
    print_profile,
    print_readiness_scorecard,
    print_repairs,
    print_test_results,
)


def run_pipeline(project_path: str, max_repairs: int = 3, thread_id: str = "default") -> int:
    """Execute the full end-to-end FDE multi-agent LangGraph workflow."""
    print_banner()

    abs_path = os.path.abspath(project_path)
    if not os.path.isdir(abs_path):
        console.print(f"[bold red]Error:[/bold red] Project directory does not exist: {abs_path}")
        return 1

    console.print(f"[bold cyan]Target Repository:[/bold cyan] {abs_path}")
    console.print(f"[dim]Maximum Self-Healing Repair Cycles: {max_repairs}[/dim]\n")

    # Validate config (API keys)
    try:
        config.validate()
    except Exception as exc:
        console.print(f"[bold red]Configuration Error:[/bold red] {exc}")
        return 1

    # Compile LangGraph StateGraph
    graph = build_fde_graph(enable_checkpointing=True)

    initial_state: FDEAgentState = {
        "project_path": abs_path,
        "files": [],
        "repair_attempts": 0,
        "max_repair_attempts": max_repairs,
        "repair_history": [],
        "status": "INITIALIZED",
        "error_log": [],
        "messages": [],
    }

    thread_config = {"configurable": {"thread_id": thread_id}}

    console.print("[bold blue][LAUNCH] Launching FDE Multi-Agent Orchestration Graph...[/bold blue]\n")

    current_state = initial_state
    try:
        for event in graph.stream(initial_state, config=thread_config):
            for node_name, node_output in event.items():
                status = node_output.get("status", "RUNNING")
                console.print(f"  [cyan][OK] Node Completed:[/cyan] [bold]{node_name}[/bold] -> [dim]{status}[/dim]")
                current_state.update(node_output)

        console.print("\n[bold green][SUCCESS] Multi-Agent Workflow Execution Completed![/bold green]\n")

        # Display rich summary views
        if current_state.get("profile"):
            print_profile(current_state["profile"])

        print_test_results(current_state)

        if current_state.get("repair_history"):
            print_repairs(current_state["repair_history"])

        if current_state.get("readiness_report"):
            print_readiness_scorecard(current_state["readiness_report"])

        return 0

    except Exception as exc:
        console.print(f"\n[bold red]Pipeline Error:[/bold red] {exc}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> None:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        description="Forward Deployment Engineer (FDE) Autonomous Multi-Agent Platform."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run full end-to-end FDE deployment pipeline")
    run_parser.add_argument("project_path", type=str, help="Path to client project repository")
    run_parser.add_argument("--max-repairs", type=int, default=3, help="Max self-healing repair attempts (default: 3)")
    run_parser.add_argument("--model", type=str, default=None, help="Override primary LLM model")

    # 'audit' subcommand
    audit_parser = subparsers.add_parser("audit", help="Run static discovery and security audit only")
    audit_parser.add_argument("project_path", type=str, help="Path to client project repository")

    args = parser.parse_args()

    if not args.command:
        # Default behavior: if a single argument is passed, treat as 'run'
        if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
            sys.exit(run_pipeline(sys.argv[1]))
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        if args.model:
            config.primary_model = args.model
        sys.exit(run_pipeline(args.project_path, max_repairs=args.max_repairs))

    elif args.command == "audit":
        from fde_agent.agents.discovery import repo_auditor_node
        from fde_agent.tools.scanner import scan_project_files
        abs_path = os.path.abspath(args.project_path)
        print_banner()
        files = scan_project_files(abs_path)
        state: FDEAgentState = {"project_path": abs_path, "files": files}
        res = repo_auditor_node(state)
        print_profile(res["profile"])
        sys.exit(0)


if __name__ == "__main__":
    main()
