"""
Test Execution Node for the FDE LangGraph Workflow.
Executes pytest in a sandboxed runner and captures structured telemetry.
"""

from typing import Dict

from fde_agent.state import FDEAgentState
from fde_agent.tools.test_runner import execute_tests


def test_execution_node(state: FDEAgentState) -> Dict:
    """
    LangGraph Node: Sandboxed Test Runner.
    Runs pytest and returns structured results.
    """
    project_path = state["project_path"]
    results = execute_tests(project_path)

    return {
        "test_results": results,
        "status": "TESTS_EXECUTED",
    }

