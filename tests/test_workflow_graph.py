"""Unit tests for LangGraph workflow and conditional routing."""

from fde_agent.graph.workflow import build_fde_graph, route_after_test_execution
from fde_agent.state import FDEAgentState, TestExecutionResult


def test_build_fde_graph():
    graph = build_fde_graph(enable_checkpointing=False)
    assert graph is not None
    # Verify graph contains key nodes
    nodes = graph.nodes
    assert "repo_auditor" in nodes
    assert "dependency_engineer" in nodes
    assert "test_architect" in nodes
    assert "test_executor" in nodes
    assert "self_healing_engineer" in nodes
    assert "container_architect" in nodes
    assert "cicd_architect" in nodes
    assert "documentation_engineer" in nodes
    assert "readiness_advisor" in nodes


def test_routing_when_tests_pass():
    state: FDEAgentState = {
        "test_results": TestExecutionResult(
            success=True,
            return_code=0,
            output="Passed",
        ),
        "repair_attempts": 0,
        "max_repair_attempts": 3,
    }
    route = route_after_test_execution(state)
    assert route == "container_architect"


def test_routing_when_tests_fail_and_attempts_remain():
    state: FDEAgentState = {
        "test_results": TestExecutionResult(
            success=False,
            return_code=1,
            output="Failed",
        ),
        "repair_attempts": 1,
        "max_repair_attempts": 3,
    }
    route = route_after_test_execution(state)
    assert route == "self_healing_engineer"


def test_routing_when_max_repairs_exceeded():
    state: FDEAgentState = {
        "test_results": TestExecutionResult(
            success=False,
            return_code=1,
            output="Failed",
        ),
        "repair_attempts": 3,
        "max_repair_attempts": 3,
    }
    route = route_after_test_execution(state)
    assert route == "readiness_advisor"

