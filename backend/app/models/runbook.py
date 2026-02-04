"""
Runbook Models
Data models for automated runbook generation and execution
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RunbookCommand(BaseModel):
    """Individual executable command within a runbook step"""
    command: str = Field(..., description="Actual command to execute (bash, kubectl, etc.)")
    description: str = Field(..., description="Human-readable description of what this command does")
    risk_level: str = Field(..., description="Risk level: safe, medium, high")
    expected_output: Optional[str] = Field(None, description="What success looks like")
    timeout_seconds: int = Field(default=30, description="Maximum execution time")
    requires_approval: bool = Field(default=True, description="Requires user confirmation before execution")


class RunbookStep(BaseModel):
    """Single step in the runbook (contains one or more commands)"""
    step_number: int = Field(..., description="Sequential step number")
    category: str = Field(..., description="Step category: diagnostic, remediation, verification, rollback")
    title: str = Field(..., description="Step title")
    commands: List[RunbookCommand] = Field(..., description="Commands to execute in this step")
    prerequisite_steps: List[int] = Field(default_factory=list, description="Steps that must complete first")
    estimated_duration: str = Field(..., description="Estimated time to complete (e.g., '2 minutes')")


class Runbook(BaseModel):
    """Complete runbook for incident remediation"""
    incident_id: str = Field(..., description="Associated incident ID")
    generated_at: str = Field(..., description="ISO timestamp when runbook was generated")
    incident_type: str = Field(..., description="Type of incident (e.g., database_outage)")
    severity: str = Field(..., description="Incident severity (P0, P1, P2, P3)")
    steps: List[RunbookStep] = Field(..., description="Ordered list of runbook steps")
    total_steps: int = Field(..., description="Total number of steps")
    estimated_total_time: str = Field(..., description="Total estimated execution time")
    warnings: List[str] = Field(default_factory=list, description="Important warnings about execution")
    prerequisites: List[str] = Field(default_factory=list, description="Required access/tools/permissions")


class ExecutionResult(BaseModel):
    """Result of executing a single command"""
    step_number: int = Field(..., description="Step number executed")
    command_index: int = Field(default=0, description="Index of command within step")
    command: str = Field(..., description="Command that was executed")
    success: bool = Field(..., description="Whether execution succeeded")
    output: str = Field(default="", description="Standard output from command")
    error: Optional[str] = Field(None, description="Error message if failed")
    executed_at: str = Field(..., description="ISO timestamp when executed")
    executed_by: str = Field(default="system", description="User or system that executed")
    dry_run: bool = Field(default=True, description="Whether this was a dry-run (no actual execution)")
    duration_seconds: float = Field(default=0.0, description="How long execution took")


class RunbookExecuteRequest(BaseModel):
    """Request to execute a runbook step"""
    step_number: int = Field(..., description="Step to execute")
    command_index: int = Field(default=0, description="Command index within step")
    dry_run: bool = Field(default=True, description="Dry-run mode (simulate execution)")
    confirmation_text: Optional[str] = Field(None, description="Confirmation text for high-risk commands")
    executed_by: str = Field(default="user", description="Who is executing this command")


class RunbookValidationResult(BaseModel):
    """Result of validating a runbook before execution"""
    is_valid: bool = Field(..., description="Whether runbook is safe to execute")
    issues: List[str] = Field(default_factory=list, description="List of validation issues found")
    warnings: List[str] = Field(default_factory=list, description="Warnings that don't block execution")
    dangerous_commands: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Commands flagged as dangerous with details"
    )


class RunbookGenerateRequest(BaseModel):
    """Request to generate a new runbook"""
    incident_id: str = Field(..., description="Incident to generate runbook for")
    include_rollback: bool = Field(default=True, description="Include rollback steps")
    max_steps: int = Field(default=10, description="Maximum number of steps to generate")
    focus_area: Optional[str] = Field(
        None,
        description="Focus area: diagnostic, remediation, emergency_rollback"
    )
