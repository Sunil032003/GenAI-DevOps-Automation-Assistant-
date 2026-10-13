"""
LangGraph Multi-Agent Workflow for Forward Deployment Engineers.
Coordinates Repo Discovery, Dependency Engineering, Test Architecture,
Autonomous Self-Healing, Hardened Containerization, CI/CD, and Handover Reporting.
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from fde_agent.agents.cicd import cicd_architect_node
from fde_agent.agents.container import container_architect_node
from fde_agent.agents.dependencies import dependency_engineer_node
from fde_agent.agents.discovery import repo_auditor_node
from fde_agent.agents.documentation import documentation_engineer_node
from fde_agent.agents.readiness_advisor import readiness_advisor_node
from fde_agent.agents.self_healing import self_healing_node
from fde_agent.agents.test_architect import test_architect_node
from fde_agent.agents.test_execution import test_execution_node
from fde_agent.graph.checkpointer import get_checkpointer
from fde_agent.state import FDEAgentState

logger = logging.getLogger("fde_agent.graph")


def route_after_test_execution(
    state: FDEAgentState,
) -> Literal["container_architect", "self_healing_engineer", "readiness_advisor"]:
    """
    Conditional edge router:
    - If tests passed -> proceed to containerization.
    - If tests failed and attempts remain -> loop into self-healing reflection.
    - If tests failed and max attempts exceeded -> escalate directly to readiness report.
    """
    test_results = state.get("test_results")
    repair_attempts = state.get("repair_attempts", 0)
    max_repairs = state.get("max_repair_attempts", 3)

    if test_results and test_results.success:
        logger.info("Test execution passed cleanly. Routing to container architect.")
        return "container_architect"

    if repair_attempts < max_repairs:
        logger.info(
            "Tests failed. Initiating self-healing repair cycle (%d/%d).",
            repair_attempts + 1,
            max_repairs,
        )
        return "self_healing_engineer"

    logger.warning("Max repair cycles (%d) exceeded. Escalating to readiness report.", max_repairs)
    return "readiness_advisor"


def build_fde_graph(enable_checkpointing: bool = True):
    """
    Construct and compile the production LangGraph state graph.
    """
    workflow = StateGraph(FDEAgentState)

    # 1. Register Nodes
    workflow.add_node("repo_auditor", repo_auditor_node)
    workflow.add_node("dependency_engineer", dependency_engineer_node)
    workflow.add_node("test_architect", test_architect_node)
    workflow.add_node("test_executor", test_execution_node)
    workflow.add_node("self_healing_engineer", self_healing_node)
    workflow.add_node("container_architect", container_architect_node)
    workflow.add_node("cicd_architect", cicd_architect_node)
    workflow.add_node("documentation_engineer", documentation_engineer_node)
    workflow.add_node("readiness_advisor", readiness_advisor_node)

    # 2. Add Linear Edges
    workflow.add_edge(START, "repo_auditor")
    workflow.add_edge("repo_auditor", "dependency_engineer")
    workflow.add_edge("dependency_engineer", "test_architect")
    workflow.add_edge("test_architect", "test_executor")

    # 3. Add Conditional Edge for Test Verification & Self-Healing
    workflow.add_conditional_edges(
        "test_executor",
        route_after_test_execution,
        {
            "container_architect": "container_architect",
            "self_healing_engineer": "self_healing_engineer",
            "readiness_advisor": "readiness_advisor",
        },
    )

    # 4. Add Cyclical Edge from Self-Healing back to Test Execution
    workflow.add_edge("self_healing_engineer", "test_executor")

    # 5. Add Packaging & Handover Edges
    workflow.add_edge("container_architect", "cicd_architect")
    workflow.add_edge("cicd_architect", "documentation_engineer")
    workflow.add_edge("documentation_engineer", "readiness_advisor")
    workflow.add_edge("readiness_advisor", END)

    # 6. Compile Graph
    checkpointer = get_checkpointer() if enable_checkpointing else None
    return workflow.compile(checkpointer=checkpointer)

