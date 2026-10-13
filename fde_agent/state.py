"""
Type-safe LangGraph State and Pydantic Schemas for the FDE Multi-Agent System.
"""

from typing import Annotated, Dict, List, Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


# ============================================================
# PYDANTIC STRUCTURED DOMAIN SCHEMAS
# ============================================================

class SecurityFinding(BaseModel):
    """Identified security risk or vulnerability in client repository."""
    file_path: str
    line_number: Optional[int] = None
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    description: str
    recommendation: str


class ProjectProfile(BaseModel):
    """Comprehensive technical profile of the client repository."""
    language: str = "Unknown"
    project_type: str = "Unknown"
    frameworks: List[str] = Field(default_factory=list)
    entrypoint: Optional[str] = None
    source_files: List[str] = Field(default_factory=list)
    test_files: List[str] = Field(default_factory=list)
    config_files: List[str] = Field(default_factory=list)
    security_findings: List[SecurityFinding] = Field(default_factory=list)
    summary: str = ""


class DependencyAudit(BaseModel):
    """Analysis and resolution of project dependencies."""
    detected_imports: List[str] = Field(default_factory=list)
    resolved_packages: Dict[str, str] = Field(default_factory=dict)
    missing_packages: List[str] = Field(default_factory=list)
    requirements_file_exists: bool = False
    requirements_path: Optional[str] = None
    final_requirements: List[str] = Field(default_factory=list)


class TestExecutionResult(BaseModel):
    """Result of sandboxed pytest execution."""
    __test__ = False
    success: bool
    return_code: int
    total_tests: int = 0
    passed_count: int = 0
    failed_count: int = 0
    failed_test_names: List[str] = Field(default_factory=list)
    output: str = ""
    failure_category: Optional[Literal["SOURCE_BUG", "TEST_BUG", "ENVIRONMENT_BUG", "TIMEOUT", "NONE"]] = None


class RepairRecord(BaseModel):
    """Log entry of an autonomous self-healing repair action."""
    attempt: int
    target_file: str
    repair_type: Literal["SOURCE", "TEST", "DEPENDENCY", "UNKNOWN"]
    diagnosis: str
    patch_applied: bool
    syntax_valid: bool
    root_cause: str = ""


class DeploymentReadinessReport(BaseModel):
    """Forward Deployment Engineer Executive & Technical Handover Scorecard."""
    overall_score: int = Field(ge=0, le=100)
    readiness_tier: Literal["PRODUCTION_READY", "CONDITIONAL_APPROVAL", "REMEDIATION_REQUIRED"]
    executive_summary: str
    security_score: int = Field(ge=0, le=100)
    test_pass_rate: float = Field(ge=0.0, le=100.0)
    container_readiness: str
    cicd_readiness: str
    key_risks: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    verification_checklist: List[str] = Field(default_factory=list)


# ============================================================
# LANGGRAPH SHARED STATE
# ============================================================

class FDEAgentState(TypedDict, total=False):
    """
    State shared across all nodes in the Forward Deployment Engineer graph.
    """
    project_path: str
    files: List[str]

    # Domain models
    profile: Optional[ProjectProfile]
    dependencies: Optional[DependencyAudit]
    test_plan: Optional[str]
    test_files: Dict[str, str]  # relative_path -> source_code
    test_results: Optional[TestExecutionResult]

    # Reflection / Self-Healing loops
    repair_attempts: int
    max_repair_attempts: int
    repair_history: List[RepairRecord]

    # Delivery Artifacts
    dockerfile_path: Optional[str]
    dockerfile_content: Optional[str]
    cicd_path: Optional[str]
    cicd_content: Optional[str]
    readme_path: Optional[str]
    readme_content: Optional[str]
    readiness_report: Optional[DeploymentReadinessReport]

    # Deployment / Git status
    published_url: Optional[str]
    status: str
    error_log: List[str]

    # LangChain Chat History
    messages: Annotated[List[BaseMessage], add_messages]
