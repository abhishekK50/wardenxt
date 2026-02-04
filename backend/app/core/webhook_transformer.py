"""
Webhook Transformer
Transforms external webhook payloads into WardenXT incident format
"""

from typing import Dict, List, Optional
from datetime import datetime
import re

from app.models.incident import (
    IncidentSummary, Severity, IncidentStatus,
    RootCause, StatusUpdate, LogEntry, MetricPoint, TimelineEvent
)


def map_urgency_to_severity(urgency: str) -> Severity:
    """Map external urgency/priority levels to WardenXT severity

    Args:
        urgency: External urgency string (high, critical, low, etc.)

    Returns:
        Severity enum value
    """
    urgency_lower = urgency.lower() if urgency else ""

    if urgency_lower in ["critical", "p0", "sev0", "emergency"]:
        return Severity.P0
    elif urgency_lower in ["high", "p1", "sev1", "urgent"]:
        return Severity.P1
    elif urgency_lower in ["medium", "p2", "sev2", "warning"]:
        return Severity.P2
    else:
        return Severity.P2  # Default to P2


def estimate_cost_and_impact(severity: Severity, services_count: int = 1) -> tuple:
    """Estimate cost and user impact based on severity and services affected

    Based on industry averages:
    - P0: ~$5,000-$10,000 per minute, affects 10,000+ users
    - P1: ~$1,000-$5,000 per minute, affects 1,000-10,000 users
    - P2: ~$100-$1,000 per minute, affects 100-1,000 users
    - P3: ~$10-$100 per minute, affects <100 users

    Args:
        severity: Incident severity level
        services_count: Number of services affected

    Returns:
        Tuple of (estimated_cost_str, users_impacted_str)
    """
    # Base estimates per severity
    severity_estimates = {
        Severity.P0: {"base_cost": 50000, "base_users": 10000, "cost_label": "$50,000+"},
        Severity.P1: {"base_cost": 15000, "base_users": 5000, "cost_label": "$15,000+"},
        Severity.P2: {"base_cost": 5000, "base_users": 1000, "cost_label": "$5,000+"},
        Severity.P3: {"base_cost": 1000, "base_users": 100, "cost_label": "$1,000+"},
    }

    estimate = severity_estimates.get(severity, severity_estimates[Severity.P2])

    # Adjust for number of services (each additional service increases impact)
    service_multiplier = 1 + (services_count - 1) * 0.25  # 25% increase per additional service

    adjusted_users = int(estimate["base_users"] * service_multiplier)

    # Format users impacted string
    if adjusted_users >= 10000:
        users_str = f"{adjusted_users // 1000}k+ users"
    elif adjusted_users >= 1000:
        users_str = f"{adjusted_users // 100 * 100}+ users"
    else:
        users_str = f"{adjusted_users}+ users"

    return estimate["cost_label"], users_str


def generate_incident_id() -> str:
    """Generate unique incident ID in format INC-YYYY-MM-XXXX

    Returns:
        Incident ID string
    """
    now = datetime.utcnow()
    # Use timestamp for uniqueness
    unique_part = f"{now.hour:02d}{now.minute:02d}"
    return f"INC-{now.year}-{now.month:02d}{now.day:02d}-{unique_part}"


def transform_pagerduty_webhook(payload: Dict) -> IncidentSummary:
    """Transform PagerDuty webhook payload to WardenXT incident

    Args:
        payload: PagerDuty webhook payload

    Returns:
        IncidentSummary object
    """
    incident_data = payload.get("incident", {})

    # Extract basic info
    title = incident_data.get("title", "PagerDuty Incident")
    urgency = incident_data.get("urgency", "medium")
    severity = map_urgency_to_severity(urgency)

    # Service info
    service = incident_data.get("service", {})
    service_name = service.get("name", "Unknown Service") if isinstance(service, dict) else str(service)
    services_affected = [service_name]

    # Timestamps
    created_at = incident_data.get("created_at", datetime.utcnow().isoformat() + "Z")

    # Estimate cost and impact based on severity and services
    estimated_cost, users_impacted = estimate_cost_and_impact(severity, len(services_affected))

    # Build incident summary
    return IncidentSummary(
        incident_id=generate_incident_id(),
        title=title,
        severity=severity,
        status=IncidentStatus.DETECTED,
        incident_type="webhook_pagerduty",
        start_time=created_at,
        end_time=None,
        duration_minutes=0,
        services_affected=services_affected,
        root_cause=RootCause(
            primary="Incident detected via PagerDuty webhook",
            secondary=None,
            contributing_factors=[]
        ),
        estimated_cost=estimated_cost,
        users_impacted=users_impacted,
        business_impact="Auto-ingested from PagerDuty - analysis pending",
        mttr_actual="In Progress",
        mttr_target="TBD",
        detection_time=created_at,
        resolution_time=None,
        mitigation_steps=["Incident auto-ingested", "AI analysis queued"],
        lessons_learned=[],
        status_history=[
            StatusUpdate(
                timestamp=datetime.utcnow().isoformat() + "Z",
                from_status=IncidentStatus.DETECTED,
                to_status=IncidentStatus.DETECTED,
                updated_by="PagerDuty Webhook",
                notes=f"Incident auto-created from PagerDuty (urgency: {urgency})"
            )
        ]
    )


def transform_slack_webhook(payload: Dict) -> IncidentSummary:
    """Transform Slack webhook payload to WardenXT incident

    Args:
        payload: Slack webhook payload

    Returns:
        IncidentSummary object
    """
    # Extract message text
    text = payload.get("text", "Slack Alert")
    channel = payload.get("channel", "unknown")
    timestamp = payload.get("timestamp", str(datetime.utcnow().timestamp()))

    # Try to infer severity from text
    severity = Severity.P2  # Default
    text_lower = text.lower()
    if any(word in text_lower for word in ["critical", "p0", "outage", "down"]):
        severity = Severity.P0
    elif any(word in text_lower for word in ["urgent", "p1", "high", "alert"]):
        severity = Severity.P1

    # Extract service name from text if possible
    services_affected = ["Slack Alert"]
    service_match = re.search(r"(?:on|from|in|service)\s+([a-zA-Z0-9-_]+)", text)
    if service_match:
        services_affected = [service_match.group(1)]

    created_at = datetime.utcnow().isoformat() + "Z"

    # Estimate cost and impact based on severity and services
    estimated_cost, users_impacted = estimate_cost_and_impact(severity, len(services_affected))

    return IncidentSummary(
        incident_id=generate_incident_id(),
        title=text[:100],  # Truncate to 100 chars
        severity=severity,
        status=IncidentStatus.DETECTED,
        incident_type="webhook_slack",
        start_time=created_at,
        end_time=None,
        duration_minutes=0,
        services_affected=services_affected,
        root_cause=RootCause(
            primary="Incident detected via Slack webhook",
            secondary=None,
            contributing_factors=[]
        ),
        estimated_cost=estimated_cost,
        users_impacted=users_impacted,
        business_impact="Auto-ingested from Slack - analysis pending",
        mttr_actual="In Progress",
        mttr_target="TBD",
        detection_time=created_at,
        resolution_time=None,
        mitigation_steps=["Incident auto-ingested from Slack", "AI analysis queued"],
        lessons_learned=[],
        status_history=[
            StatusUpdate(
                timestamp=created_at,
                from_status=IncidentStatus.DETECTED,
                to_status=IncidentStatus.DETECTED,
                updated_by="Slack Webhook",
                notes=f"Alert from channel: {channel}"
            )
        ]
    )


def transform_generic_webhook(payload: Dict) -> IncidentSummary:
    """Transform generic webhook payload to WardenXT incident

    Uses intelligent field extraction to find relevant data

    Args:
        payload: Generic webhook payload (any JSON)

    Returns:
        IncidentSummary object
    """
    # Try to extract common fields with fallbacks
    possible_title_keys = ["title", "alert_name", "name", "message", "summary", "description"]
    title = "Generic Webhook Alert"
    for key in possible_title_keys:
        if key in payload and payload[key]:
            title = str(payload[key])[:100]
            break

    # Try to extract severity
    possible_severity_keys = ["severity", "priority", "urgency", "level"]
    severity = Severity.P2  # Default
    for key in possible_severity_keys:
        if key in payload:
            severity = map_urgency_to_severity(str(payload[key]))
            break

    # Try to extract service/host info
    services_affected = ["Unknown"]
    possible_service_keys = ["service", "host", "server", "application", "app", "component"]
    for key in possible_service_keys:
        if key in payload and payload[key]:
            services_affected = [str(payload[key])]
            break

    # Try to extract message
    possible_message_keys = ["message", "description", "details", "text", "body"]
    message = "Generic alert received"
    for key in possible_message_keys:
        if key in payload and payload[key]:
            message = str(payload[key])
            break

    created_at = datetime.utcnow().isoformat() + "Z"

    # Estimate cost and impact based on severity and services
    estimated_cost, users_impacted = estimate_cost_and_impact(severity, len(services_affected))

    return IncidentSummary(
        incident_id=generate_incident_id(),
        title=title,
        severity=severity,
        status=IncidentStatus.DETECTED,
        incident_type="webhook_generic",
        start_time=created_at,
        end_time=None,
        duration_minutes=0,
        services_affected=services_affected,
        root_cause=RootCause(
            primary="Incident detected via generic webhook",
            secondary=None,
            contributing_factors=[message]
        ),
        estimated_cost=estimated_cost,
        users_impacted=users_impacted,
        business_impact="Auto-ingested from external monitoring - analysis pending",
        mttr_actual="In Progress",
        mttr_target="TBD",
        detection_time=created_at,
        resolution_time=None,
        mitigation_steps=["Incident auto-ingested", "Extracting details", "AI analysis queued"],
        lessons_learned=[],
        status_history=[
            StatusUpdate(
                timestamp=created_at,
                from_status=IncidentStatus.DETECTED,
                to_status=IncidentStatus.DETECTED,
                updated_by="Generic Webhook",
                notes=f"Alert ingested from external system"
            )
        ]
    )


def create_minimal_incident_logs(summary: IncidentSummary, raw_payload: Dict) -> List[LogEntry]:
    """Create minimal log entries for webhook-sourced incident

    Args:
        summary: Incident summary
        raw_payload: Original webhook payload

    Returns:
        List of log entries
    """
    created_at = summary.start_time

    return [
        LogEntry(
            timestamp=created_at,
            level="INFO",
            service=summary.services_affected[0] if summary.services_affected else "webhook",
            host="webhook-ingestion",
            message=f"Incident auto-created from webhook: {summary.title}",
            metadata={"webhook_payload": raw_payload}
        )
    ]


def create_minimal_incident_metrics(summary: IncidentSummary) -> List[MetricPoint]:
    """Create minimal metric points for webhook-sourced incident

    Args:
        summary: Incident summary

    Returns:
        List of metric points (empty for now, can be populated later)
    """
    # Return empty list - metrics will be populated if monitoring is connected
    return []


def create_minimal_incident_timeline(summary: IncidentSummary) -> List[TimelineEvent]:
    """Create minimal timeline for webhook-sourced incident

    Args:
        summary: Incident summary

    Returns:
        List of timeline events
    """
    return [
        TimelineEvent(
            time=summary.start_time,
            event="Incident Detected",
            impact="Webhook received from external monitoring",
            type="detection"
        ),
        TimelineEvent(
            time=datetime.utcnow().isoformat() + "Z",
            event="Auto-Ingestion Complete",
            impact="Incident created in WardenXT",
            type="system"
        )
    ]
