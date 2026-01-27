"""
Audit Logging
Tracks all user actions for compliance and security
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from fastapi import Request

from app.db.models import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


def audit_log(
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: str = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[Session] = None
):
    """Log an audit event
    
    Args:
        action: Action performed (e.g., "incident_created", "status_updated")
        user_id: User ID who performed the action
        username: Username (denormalized for historical records)
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        details: Additional action details
        ip_address: IP address of request
        user_agent: User agent string
        db: Database session (optional, will log to file if not provided)
    """
    try:
        # Always log to application logs
        logger.info(
            "audit_event",
            extra_fields={
                "action": action,
                "user_id": user_id,
                "username": username,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "ip_address": ip_address
            }
        )
        
        # If database session provided, also log to database
        if db:
            audit_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit_entry)
            db.commit()
    except Exception as e:
        # Don't fail the request if audit logging fails
        logger.error("audit_log_failed", extra_fields={"error": str(e), "action": action})


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded IP (when behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")
