"""
Incident Data Models - Enhanced with Status Tracking
Pydantic models for incident data structures with lifecycle management
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    """Incident severity levels"""
    P0 = "P0"  # Critical - Complete outage
    P1 = "P1"  # High - Major functionality impaired
    P2 = "P2"  # Medium - Partial functionality impaired
    P3 = "P3"  # Low - Minor issues


class IncidentStatus(str, Enum):
    """Incident lifecycle status"""
    DETECTED = "DETECTED"          # Initial detection
    INVESTIGATING = "INVESTIGATING" # Team investigating
    IDENTIFIED = "IDENTIFIED"       # Root cause identified
    MITIGATING = "MITIGATING"      # Mitigation in progress
    MONITORING = "MONITORING"       # Issue resolved, monitoring
    RESOLVED = "RESOLVED"           # Fully resolved
    CLOSED = "CLOSED"               # Incident closed


class StatusUpdate(BaseModel):
    """Status update record"""
    timestamp: str
    from_status: IncidentStatus
    to_status: IncidentStatus
    updated_by: str = "System"
    notes: Optional[str] = None


class LogEntry(BaseModel):
    """Single log entry"""
    timestamp: str
    level: str
    service: str
    host: str
    message: str
    thread_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict] = None


class MetricPoint(BaseModel):
    """Single metric data point"""
    timestamp: str
    service: str
    host: str
    metrics: Dict[str, float]


class TimelineEvent(BaseModel):
    """Incident timeline event"""
    time: str
    event: str
    impact: str
    type: str = "incident_event"


class RootCause(BaseModel):
    """Root cause analysis"""
    primary: str
    secondary: Optional[str] = None
    contributing_factors: Optional[List[str]] = None


class IncidentSummary(BaseModel):
    """Incident summary from generated data"""
    incident_id: str
    title: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.DETECTED
    incident_type: str = "unknown"
    start_time: str = ""
    end_time: Optional[str] = None
    duration_minutes: int
    services_affected: List[str]
    root_cause: RootCause
    estimated_cost: str
    users_impacted: str
    business_impact: str = "Unknown"
    mttr_actual: str = "Unknown"
    mttr_target: str = "Unknown"
    detection_time: Optional[str] = None
    resolution_time: Optional[str] = None
    mitigation_steps: List[str]
    lessons_learned: List[str]
    status_history: List[StatusUpdate] = []


class Incident(BaseModel):
    """Complete incident data"""
    summary: IncidentSummary
    logs: List[LogEntry]
    metrics: List[MetricPoint]
    timeline: List[TimelineEvent]
    status: IncidentStatus = IncidentStatus.DETECTED
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IncidentListItem(BaseModel):
    """Incident list item for dashboard"""
    incident_id: str
    title: str
    severity: Severity
    status: IncidentStatus
    incident_type: str = "unknown"
    start_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    services_affected: List[str]
    estimated_cost: Optional[str] = None
    users_impacted: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    """Request to update incident status"""
    new_status: IncidentStatus
    notes: Optional[str] = None
    updated_by: str = "User"


# Webhook Models

class PagerDutyWebhook(BaseModel):
    """PagerDuty incident webhook payload"""
    event_type: str
    incident: Dict


class SlackWebhook(BaseModel):
    """Slack alert webhook payload"""
    text: str
    channel: Optional[str] = None
    timestamp: Optional[str] = None
    user: Optional[str] = None


class GenericWebhook(BaseModel):
    """Generic webhook that accepts any JSON"""
    data: Dict = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow any additional fields


class WebhookSource(str, Enum):
    """Webhook source type"""
    PAGERDUTY = "pagerduty"
    SLACK = "slack"
    GENERIC = "generic"


class ExternalIncident(BaseModel):
    """Incident created from external webhook"""
    incident_id: str
    source: WebhookSource
    raw_payload: Dict
    created_at: str
    incident_data: IncidentSummary
    auto_analyzed: bool = False
    analysis_id: Optional[str] = None