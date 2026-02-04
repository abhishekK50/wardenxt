"""
Runbook API Router
Endpoints for generating and executing incident runbooks
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.runbook import (
    Runbook,
    RunbookExecuteRequest,
    RunbookValidationResult,
    RunbookGenerateRequest,
    ExecutionResult
)
from app.core.data_loader import DataLoader
from app.core.runbook_generator import get_runbook_generator
from app.core.command_executor import execute_command, validate_command_safety
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/runbooks", tags=["runbooks"])

# In-memory storage for runbooks and execution history
# In production, this would be a database
runbooks_cache: Dict[str, Runbook] = {}
execution_history: Dict[str, List[ExecutionResult]] = {}

# Cache TTL: 1 hour
CACHE_TTL_MINUTES = 60


def get_data_loader():
    """Dependency injection for data loader"""
    return DataLoader()


def get_runbook_from_cache(incident_id: str) -> Optional[Runbook]:
    """Get runbook from cache if not expired

    Args:
        incident_id: Incident ID

    Returns:
        Cached runbook or None if expired/not found
    """
    if incident_id not in runbooks_cache:
        return None

    runbook = runbooks_cache[incident_id]

    # Check if cache is expired
    generated_at = datetime.fromisoformat(runbook.generated_at)
    if datetime.utcnow() - generated_at > timedelta(minutes=CACHE_TTL_MINUTES):
        logger.info("runbook_cache_expired", extra_fields={"incident_id": incident_id})
        del runbooks_cache[incident_id]
        return None

    return runbook


def get_webhook_incident_data():
    """Get webhook incident data from webhooks module"""
    try:
        from app.api.webhooks import webhook_incidents, webhook_incident_data
        return webhook_incidents, webhook_incident_data
    except ImportError:
        return {}, {}


@router.post("/{incident_id}/generate", response_model=Runbook)
async def generate_runbook(
    incident_id: str,
    request: Optional[RunbookGenerateRequest] = None,
    data_loader: DataLoader = Depends(get_data_loader)
):
    """Generate executable runbook for incident

    Args:
        incident_id: Incident to generate runbook for
        request: Optional generation parameters
        data_loader: Data loader dependency

    Returns:
        Generated runbook

    Raises:
        HTTPException: If incident not found or generation fails
    """
    try:
        logger.info(
            "runbook_generation_requested",
            extra_fields={"incident_id": incident_id}
        )

        # Load incident data
        webhook_incidents_dict, webhook_incident_data_dict = get_webhook_incident_data()

        if incident_id in webhook_incident_data_dict:
            incident = webhook_incident_data_dict[incident_id]
        else:
            try:
                incident = data_loader.load_incident(incident_id)
            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Incident not found: {incident_id}"
                )

        # Get generation parameters
        focus_area = request.focus_area if request else "all"
        max_steps = request.max_steps if request else 10

        # Generate runbook
        generator = get_runbook_generator()
        runbook = await generator.generate_runbook(
            incident=incident,
            focus_area=focus_area,
            max_steps=max_steps
        )

        # Cache runbook
        runbooks_cache[incident_id] = runbook

        logger.info(
            "runbook_generated_successfully",
            extra_fields={
                "incident_id": incident_id,
                "steps_count": runbook.total_steps,
                "estimated_time": runbook.estimated_total_time
            }
        )

        return runbook

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "runbook_generation_api_error",
            extra_fields={
                "incident_id": incident_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate runbook: {str(e)}"
        )


@router.get("/{incident_id}", response_model=Runbook)
async def get_runbook(incident_id: str):
    """Get cached runbook for incident

    Args:
        incident_id: Incident ID

    Returns:
        Cached runbook

    Raises:
        HTTPException: If runbook not found
    """
    runbook = get_runbook_from_cache(incident_id)

    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No runbook found for incident {incident_id}. Generate one first."
        )

    return runbook


@router.post("/{incident_id}/execute-step", response_model=ExecutionResult)
async def execute_runbook_step(
    incident_id: str,
    request: RunbookExecuteRequest
):
    """Execute a single runbook step

    Args:
        incident_id: Incident ID
        request: Execution request with step number and parameters

    Returns:
        Execution result

    Raises:
        HTTPException: If runbook not found or execution fails
    """
    try:
        logger.info(
            "runbook_step_execution_requested",
            extra_fields={
                "incident_id": incident_id,
                "step_number": request.step_number,
                "dry_run": request.dry_run
            }
        )

        # Get runbook from cache
        runbook = get_runbook_from_cache(incident_id)
        if not runbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No runbook found for incident {incident_id}"
            )

        # Find step
        step = next(
            (s for s in runbook.steps if s.step_number == request.step_number),
            None
        )
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {request.step_number} not found in runbook"
            )

        # Get command
        if request.command_index >= len(step.commands):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Command index {request.command_index} out of range"
            )

        command = step.commands[request.command_index]

        # Verify high-risk commands have confirmation
        if command.risk_level == "high" and not request.dry_run:
            if request.confirmation_text != "EXECUTE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="High-risk command requires confirmation text 'EXECUTE'"
                )

        # Execute command
        result = execute_command(
            command=command,
            dry_run=request.dry_run,
            executed_by=request.executed_by
        )

        # Update result with step info
        result.step_number = request.step_number
        result.command_index = request.command_index

        # Store in execution history
        if incident_id not in execution_history:
            execution_history[incident_id] = []
        execution_history[incident_id].append(result)

        logger.info(
            "runbook_step_executed",
            extra_fields={
                "incident_id": incident_id,
                "step_number": request.step_number,
                "success": result.success,
                "dry_run": result.dry_run
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "runbook_execution_api_error",
            extra_fields={
                "incident_id": incident_id,
                "step_number": request.step_number,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute step: {str(e)}"
        )


@router.get("/{incident_id}/history", response_model=Dict)
async def get_execution_history(incident_id: str):
    """Get execution history for incident runbook

    Args:
        incident_id: Incident ID

    Returns:
        Dictionary with execution history

    Raises:
        HTTPException: If no history found
    """
    if incident_id not in execution_history:
        return {
            "incident_id": incident_id,
            "executions_count": 0,
            "history": []
        }

    history = execution_history[incident_id]

    return {
        "incident_id": incident_id,
        "executions_count": len(history),
        "history": history,
        "successful_count": sum(1 for h in history if h.success),
        "failed_count": sum(1 for h in history if not h.success),
        "dry_run_count": sum(1 for h in history if h.dry_run)
    }


@router.post("/{incident_id}/validate", response_model=RunbookValidationResult)
async def validate_runbook(incident_id: str):
    """Validate runbook for safety before execution

    Args:
        incident_id: Incident ID

    Returns:
        Validation result

    Raises:
        HTTPException: If runbook not found
    """
    runbook = get_runbook_from_cache(incident_id)

    if not runbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No runbook found for incident {incident_id}"
        )

    generator = get_runbook_generator()
    validation = generator.validate_runbook(runbook)

    return validation


@router.delete("/{incident_id}", response_model=Dict)
async def clear_runbook_cache(incident_id: str):
    """Clear cached runbook for incident

    Args:
        incident_id: Incident ID

    Returns:
        Success message

    Raises:
        HTTPException: If runbook not found
    """
    if incident_id not in runbooks_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached runbook found for incident {incident_id}"
        )

    del runbooks_cache[incident_id]

    # Also clear execution history
    if incident_id in execution_history:
        del execution_history[incident_id]

    logger.info("runbook_cache_cleared", extra_fields={"incident_id": incident_id})

    return {
        "success": True,
        "incident_id": incident_id,
        "message": "Runbook cache cleared successfully"
    }


@router.get("/", response_model=Dict)
async def list_cached_runbooks():
    """List all cached runbooks

    Returns:
        Dictionary with cached runbook information
    """
    runbooks_info = []

    for incident_id, runbook in runbooks_cache.items():
        generated_at = datetime.fromisoformat(runbook.generated_at)
        age_minutes = (datetime.utcnow() - generated_at).total_seconds() / 60

        runbooks_info.append({
            "incident_id": incident_id,
            "generated_at": runbook.generated_at,
            "age_minutes": int(age_minutes),
            "total_steps": runbook.total_steps,
            "severity": runbook.severity,
            "estimated_time": runbook.estimated_total_time
        })

    return {
        "cached_count": len(runbooks_cache),
        "cache_ttl_minutes": CACHE_TTL_MINUTES,
        "runbooks": runbooks_info
    }
