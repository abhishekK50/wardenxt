"""
Analysis Data Models
Pydantic models for AI-generated analysis
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ConfidenceLevel(str, Enum):
    """Confidence in analysis"""
    LOW = "LOW"          # < 50%
    MEDIUM = "MEDIUM"    # 50-75%
    HIGH = "HIGH"        # 75-90%
    VERY_HIGH = "VERY_HIGH"  # > 90%


class RootCauseAnalysis(BaseModel):
    """AI-generated root cause analysis"""
    primary_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    evidence: List[str]
    contributing_factors: Optional[List[str]] = None
    similar_incidents: Optional[List[str]] = None


class MitigationAction(BaseModel):
    """Single mitigation action"""
    priority: str  # HIGH, MEDIUM, LOW
    action: str
    estimated_time: str
    risk_level: str
    command: Optional[str] = None  # For executable actions


class ImpactAssessment(BaseModel):
    """Business and technical impact"""
    users_affected: str
    estimated_cost: str
    services_impacted: List[str]
    severity_justification: str


class IncidentBrief(BaseModel):
    """AI-generated incident brief"""
    incident_id: str
    executive_summary: str
    root_cause: RootCauseAnalysis
    impact: ImpactAssessment
    recommended_actions: List[MitigationAction]
    timeline_summary: str
    generated_at: str
    analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "INC-2026-0001",
                "executive_summary": "Database connection pool exhaustion...",
                "root_cause": {
                    "primary_cause": "Memory leak in payment-api v2.3.1",
                    "confidence": 0.89,
                    "confidence_level": "HIGH",
                    "evidence": ["Memory usage increased 78%", "Connection pool at 98/100"]
                }
            }
        }


class AgentStatus(BaseModel):
    """Current status of AI agent"""
    status: str  # IDLE, ANALYZING, EXECUTING
    current_task: Optional[str] = None
    progress: float = Field(ge=0.0, le=1.0, default=0.0)
    logs_analyzed: int = 0
    metrics_analyzed: int = 0
    insights_generated: int = 0


class AnalysisRequest(BaseModel):
    """Request for incident analysis"""
    incident_id: str
    include_logs: bool = True
    include_metrics: bool = True
    include_timeline: bool = True
    max_logs: Optional[int] = 1000  # Limit for performance


class AnalysisResponse(BaseModel):
    """Response from analysis"""
    incident_id: str
    brief: IncidentBrief
    agent_status: AgentStatus