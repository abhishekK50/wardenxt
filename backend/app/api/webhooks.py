"""
Webhooks API Routes
Endpoints for receiving incidents from external monitoring tools
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, status
from typing import Dict
from datetime import datetime
from pathlib import Path
import json

from app.models.incident import (
    PagerDutyWebhook, SlackWebhook, GenericWebhook,
    ExternalIncident, WebhookSource, Incident, LogEntry, MetricPoint, TimelineEvent,
    IncidentSummary, RootCause, Severity, IncidentStatus
)
from app.core.webhook_transformer import (
    transform_pagerduty_webhook,
    transform_slack_webhook,
    transform_generic_webhook,
    create_minimal_incident_logs,
    create_minimal_incident_metrics,
    create_minimal_incident_timeline
)
from app.core.logging import get_logger
from app.core.agent.analyzer import IncidentAnalyzer

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger(__name__)

# File path for persistent storage
WEBHOOK_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "webhook_incidents"
WEBHOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for webhook-created incidents
# Format: {incident_id: ExternalIncident}
webhook_incidents: Dict[str, ExternalIncident] = {}

# In-memory storage for complete incident data (for analysis)
# Format: {incident_id: Incident}
webhook_incident_data: Dict[str, Incident] = {}


def save_webhook_incident(incident_id: str, external_incident: ExternalIncident, incident: Incident):
    """Save webhook incident to file for persistence"""
    try:
        incident_file = WEBHOOK_DATA_DIR / f"{incident_id}.json"
        data = {
            "external_incident": {
                "incident_id": external_incident.incident_id,
                "source": external_incident.source,
                "raw_payload": external_incident.raw_payload,
                "created_at": external_incident.created_at,
                "auto_analyzed": external_incident.auto_analyzed,
                "analysis_id": external_incident.analysis_id,
                "incident_data": {
                    "incident_id": external_incident.incident_data.incident_id,
                    "title": external_incident.incident_data.title,
                    "severity": str(external_incident.incident_data.severity.value) if hasattr(external_incident.incident_data.severity, 'value') else str(external_incident.incident_data.severity),
                    "status": str(external_incident.incident_data.status.value) if hasattr(external_incident.incident_data.status, 'value') else str(external_incident.incident_data.status),
                    "services_affected": external_incident.incident_data.services_affected,
                    "root_cause": {
                        "primary": external_incident.incident_data.root_cause.primary if external_incident.incident_data.root_cause else "Unknown",
                        "secondary": external_incident.incident_data.root_cause.secondary if external_incident.incident_data.root_cause else None,
                    },
                    "duration_minutes": external_incident.incident_data.duration_minutes,
                    "estimated_cost": external_incident.incident_data.estimated_cost,
                    "users_impacted": external_incident.incident_data.users_impacted,
                    "mitigation_steps": external_incident.incident_data.mitigation_steps or [],
                    "lessons_learned": external_incident.incident_data.lessons_learned or [],
                    "incident_type": getattr(external_incident.incident_data, 'incident_type', 'unknown'),
                    "start_time": getattr(external_incident.incident_data, 'start_time', ''),
                }
            }
        }
        with open(incident_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("webhook_incident_saved", extra_fields={"incident_id": incident_id, "file": str(incident_file)})
    except Exception as e:
        logger.error("webhook_incident_save_failed", extra_fields={"incident_id": incident_id, "error": str(e)})


def load_webhook_incidents():
    """Load all webhook incidents from files on startup"""
    global webhook_incidents, webhook_incident_data

    try:
        if not WEBHOOK_DATA_DIR.exists():
            return

        for incident_file in WEBHOOK_DATA_DIR.glob("*.json"):
            try:
                with open(incident_file, 'r') as f:
                    data = json.load(f)

                ext_data = data.get("external_incident", {})
                inc_data = ext_data.get("incident_data", {})

                # Reconstruct IncidentSummary
                severity_str = inc_data.get("severity", "P2")
                try:
                    severity = Severity(severity_str)
                except:
                    severity = Severity.P2

                status_str = inc_data.get("status", "DETECTED")
                try:
                    status = IncidentStatus(status_str)
                except:
                    status = IncidentStatus.DETECTED

                # Check if there's a more recent status in the status store
                from app.db.status_store import get_status_store
                status_store = get_status_store()
                stored_status = status_store.get_current_status(ext_data.get("incident_id"))
                if stored_status is not None:
                    status = stored_status

                root_cause_data = inc_data.get("root_cause", {})
                root_cause = RootCause(
                    primary=root_cause_data.get("primary", "Unknown"),
                    secondary=root_cause_data.get("secondary")
                )

                incident_summary = IncidentSummary(
                    incident_id=inc_data.get("incident_id"),
                    title=inc_data.get("title", "Unknown Incident"),
                    severity=severity,
                    status=status,
                    services_affected=inc_data.get("services_affected", []),
                    root_cause=root_cause,
                    duration_minutes=inc_data.get("duration_minutes", 0),
                    estimated_cost=inc_data.get("estimated_cost", "Unknown"),
                    users_impacted=inc_data.get("users_impacted", "Unknown"),
                    mitigation_steps=inc_data.get("mitigation_steps", []),
                    lessons_learned=inc_data.get("lessons_learned", []),
                    incident_type=inc_data.get("incident_type", "unknown"),
                    start_time=inc_data.get("start_time", ""),
                )

                # Reconstruct ExternalIncident
                source_str = ext_data.get("source", "generic")
                try:
                    source = WebhookSource(source_str)
                except:
                    source = WebhookSource.GENERIC

                external_incident = ExternalIncident(
                    incident_id=ext_data.get("incident_id"),
                    source=source,
                    raw_payload=ext_data.get("raw_payload", {}),
                    created_at=ext_data.get("created_at"),
                    incident_data=incident_summary,
                    auto_analyzed=ext_data.get("auto_analyzed", False),
                    analysis_id=ext_data.get("analysis_id")
                )

                # Reconstruct full Incident
                incident = Incident(
                    summary=incident_summary,
                    logs=create_minimal_incident_logs(incident_summary, ext_data.get("raw_payload", {})),
                    metrics=create_minimal_incident_metrics(incident_summary),
                    timeline=create_minimal_incident_timeline(incident_summary),
                    status=status
                )

                # Store in memory
                incident_id = ext_data.get("incident_id")
                webhook_incidents[incident_id] = external_incident
                webhook_incident_data[incident_id] = incident

                logger.info("webhook_incident_loaded", extra_fields={"incident_id": incident_id})

            except Exception as e:
                logger.error("webhook_incident_load_failed", extra_fields={"file": str(incident_file), "error": str(e)})

        logger.info("webhook_incidents_loaded", extra_fields={"count": len(webhook_incidents)})

    except Exception as e:
        logger.error("webhook_incidents_load_all_failed", extra_fields={"error": str(e)})


# Load existing incidents on module import
load_webhook_incidents()


async def trigger_auto_analysis(incident_id: str):
    """Background task to automatically analyze webhook-ingested incident

    Args:
        incident_id: Incident to analyze
    """
    try:
        logger.info(
            "webhook_auto_analysis_started",
            extra_fields={
                "incident_id": incident_id,
                "trigger": "webhook_ingestion"
            }
        )

        # Get incident data
        if incident_id not in webhook_incident_data:
            logger.error(
                "webhook_analysis_incident_not_found",
                extra_fields={"incident_id": incident_id}
            )
            return

        incident = webhook_incident_data[incident_id]

        # Run analysis
        analyzer = IncidentAnalyzer()
        brief = await analyzer.analyze_incident(incident, max_logs=100)

        # Update external incident record
        if incident_id in webhook_incidents:
            webhook_incidents[incident_id].auto_analyzed = True
            webhook_incidents[incident_id].analysis_id = brief.incident_id

        logger.info(
            "webhook_auto_analysis_completed",
            extra_fields={
                "incident_id": incident_id,
                "analysis_status": brief.analysis_status
            }
        )

    except Exception as e:
        logger.error(
            "webhook_auto_analysis_failed",
            extra_fields={
                "incident_id": incident_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        # Don't raise - we still want the incident created even if analysis fails


@router.post("/pagerduty")
async def receive_pagerduty_webhook(
    payload: Dict,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Receive PagerDuty incident webhook

    Args:
        payload: PagerDuty webhook payload
        background_tasks: FastAPI background tasks
        request: HTTP request

    Returns:
        Success response with incident_id
    """
    try:
        # Log webhook receipt
        logger.info(
            "webhook_received",
            extra_fields={
                "source": "pagerduty",
                "ip": request.client.host if request.client else "unknown"
            }
        )

        # Validate basic structure
        if "incident" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: 'incident'"
            )

        # Transform to WardenXT format
        incident_summary = transform_pagerduty_webhook(payload)
        incident_id = incident_summary.incident_id

        # Create full incident object
        incident = Incident(
            summary=incident_summary,
            logs=create_minimal_incident_logs(incident_summary, payload),
            metrics=create_minimal_incident_metrics(incident_summary),
            timeline=create_minimal_incident_timeline(incident_summary),
            status=incident_summary.status
        )

        # Store in webhook incidents
        external_incident = ExternalIncident(
            incident_id=incident_id,
            source=WebhookSource.PAGERDUTY,
            raw_payload=payload,
            created_at=datetime.utcnow().isoformat() + "Z",
            incident_data=incident_summary,
            auto_analyzed=False
        )

        webhook_incidents[incident_id] = external_incident
        webhook_incident_data[incident_id] = incident

        # Save to file for persistence
        save_webhook_incident(incident_id, external_incident, incident)

        # Trigger auto-analysis in background
        background_tasks.add_task(trigger_auto_analysis, incident_id)

        logger.info(
            "webhook_incident_created",
            extra_fields={
                "incident_id": incident_id,
                "source": "pagerduty",
                "severity": incident_summary.severity
            }
        )

        # Return quickly (< 100ms target)
        return {
            "status": "success",
            "incident_id": incident_id,
            "message": "Incident created and queued for analysis",
            "severity": incident_summary.severity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "webhook_processing_failed",
            extra_fields={
                "source": "pagerduty",
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/slack")
async def receive_slack_webhook(
    payload: Dict,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Receive Slack alert webhook

    Args:
        payload: Slack webhook payload
        background_tasks: FastAPI background tasks
        request: HTTP request

    Returns:
        Success response with incident_id
    """
    try:
        # Log webhook receipt
        logger.info(
            "webhook_received",
            extra_fields={
                "source": "slack",
                "ip": request.client.host if request.client else "unknown"
            }
        )

        # Validate basic structure
        if "text" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: 'text'"
            )

        # Transform to WardenXT format
        incident_summary = transform_slack_webhook(payload)
        incident_id = incident_summary.incident_id

        # Create full incident object
        incident = Incident(
            summary=incident_summary,
            logs=create_minimal_incident_logs(incident_summary, payload),
            metrics=create_minimal_incident_metrics(incident_summary),
            timeline=create_minimal_incident_timeline(incident_summary),
            status=incident_summary.status
        )

        # Store in webhook incidents
        external_incident = ExternalIncident(
            incident_id=incident_id,
            source=WebhookSource.SLACK,
            raw_payload=payload,
            created_at=datetime.utcnow().isoformat() + "Z",
            incident_data=incident_summary,
            auto_analyzed=False
        )

        webhook_incidents[incident_id] = external_incident
        webhook_incident_data[incident_id] = incident

        # Save to file for persistence
        save_webhook_incident(incident_id, external_incident, incident)

        # Trigger auto-analysis in background
        background_tasks.add_task(trigger_auto_analysis, incident_id)

        logger.info(
            "webhook_incident_created",
            extra_fields={
                "incident_id": incident_id,
                "source": "slack",
                "severity": incident_summary.severity
            }
        )

        # Return quickly
        return {
            "status": "success",
            "incident_id": incident_id,
            "message": "Incident created and queued for analysis",
            "severity": incident_summary.severity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "webhook_processing_failed",
            extra_fields={
                "source": "slack",
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/generic")
async def receive_generic_webhook(
    payload: Dict,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Receive generic webhook (any JSON structure)

    Args:
        payload: Generic webhook payload (any JSON)
        background_tasks: FastAPI background tasks
        request: HTTP request

    Returns:
        Success response with incident_id
    """
    try:
        # Log webhook receipt
        logger.info(
            "webhook_received",
            extra_fields={
                "source": "generic",
                "ip": request.client.host if request.client else "unknown",
                "payload_keys": list(payload.keys())
            }
        )

        # No validation needed - accept any JSON

        # Transform to WardenXT format using intelligent extraction
        incident_summary = transform_generic_webhook(payload)
        incident_id = incident_summary.incident_id

        # Create full incident object
        incident = Incident(
            summary=incident_summary,
            logs=create_minimal_incident_logs(incident_summary, payload),
            metrics=create_minimal_incident_metrics(incident_summary),
            timeline=create_minimal_incident_timeline(incident_summary),
            status=incident_summary.status
        )

        # Store in webhook incidents
        external_incident = ExternalIncident(
            incident_id=incident_id,
            source=WebhookSource.GENERIC,
            raw_payload=payload,
            created_at=datetime.utcnow().isoformat() + "Z",
            incident_data=incident_summary,
            auto_analyzed=False
        )

        webhook_incidents[incident_id] = external_incident
        webhook_incident_data[incident_id] = incident

        # Save to file for persistence
        save_webhook_incident(incident_id, external_incident, incident)

        # Trigger auto-analysis in background
        background_tasks.add_task(trigger_auto_analysis, incident_id)

        logger.info(
            "webhook_incident_created",
            extra_fields={
                "incident_id": incident_id,
                "source": "generic",
                "severity": incident_summary.severity
            }
        )

        # Return quickly
        return {
            "status": "success",
            "incident_id": incident_id,
            "message": "Incident created and queued for analysis",
            "severity": incident_summary.severity,
            "extracted_fields": {
                "title": incident_summary.title,
                "services": incident_summary.services_affected,
                "severity": incident_summary.severity
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "webhook_processing_failed",
            extra_fields={
                "source": "generic",
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


# Helper endpoints for webhook management

@router.get("/incidents")
async def list_webhook_incidents():
    """List all webhook-ingested incidents

    Returns:
        List of webhook incidents with metadata
    """
    incidents_list = [
        {
            "incident_id": inc.incident_id,
            "source": inc.source,
            "created_at": inc.created_at,
            "auto_analyzed": inc.auto_analyzed,
            "title": inc.incident_data.title,
            "severity": inc.incident_data.severity,
            "status": inc.incident_data.status
        }
        for inc in webhook_incidents.values()
    ]

    # Sort by created_at descending (newest first)
    incidents_list.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "total": len(incidents_list),
        "incidents": incidents_list
    }


@router.get("/incidents/{incident_id}")
async def get_webhook_incident(incident_id: str):
    """Get webhook incident details including raw payload

    Args:
        incident_id: Incident identifier

    Returns:
        Complete webhook incident data
    """
    if incident_id not in webhook_incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook incident {incident_id} not found"
        )

    return webhook_incidents[incident_id]


# TODO: Add webhook signature validation for PagerDuty and Slack
# For production:
# - PagerDuty: Validate X-PagerDuty-Signature header
# - Slack: Validate X-Slack-Signature header using signing secret
# Skipped for demo to simplify integration
