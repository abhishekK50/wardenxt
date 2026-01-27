"""
Database Models
SQLAlchemy models for persistent storage
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles"""
    ADMIN = "admin"
    INCIDENT_MANAGER = "incident_manager"
    VIEWER = "viewer"
    ANALYST = "analyst"


class IncidentStatusEnum(str, enum.Enum):
    """Incident status enum"""
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    IDENTIFIED = "IDENTIFIED"
    MITIGATING = "MITIGATING"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SeverityEnum(str, enum.Enum):
    """Severity enum"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    incidents_created = relationship("Incident", back_populates="created_by_user", foreign_keys="Incident.created_by_id")
    status_updates = relationship("StatusUpdate", back_populates="updated_by_user")


class Incident(Base):
    """Incident model"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(SQLEnum(SeverityEnum), nullable=False)
    status = Column(SQLEnum(IncidentStatusEnum), default=IncidentStatusEnum.DETECTED, nullable=False)
    incident_type = Column(String, nullable=True)
    
    # Timestamps
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    
    # Impact
    services_affected = Column(JSON, nullable=False)  # List of strings
    estimated_cost = Column(String, nullable=True)
    users_impacted = Column(String, nullable=True)
    
    # Root cause
    root_cause_primary = Column(Text, nullable=True)
    root_cause_secondary = Column(Text, nullable=True)
    root_cause_factors = Column(JSON, nullable=True)  # List of strings
    
    # Metadata
    mitigation_steps = Column(JSON, nullable=True)  # List of strings
    lessons_learned = Column(JSON, nullable=True)  # List of strings
    
    # Relationships
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="incidents_created", foreign_keys=[created_by_id])
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    status_history = relationship("StatusUpdate", back_populates="incident", order_by="StatusUpdate.timestamp")
    analysis_briefs = relationship("AnalysisBrief", back_populates="incident")


class StatusUpdate(Base):
    """Status update model"""
    __tablename__ = "status_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    from_status = Column(SQLEnum(IncidentStatusEnum), nullable=False)
    to_status = Column(SQLEnum(IncidentStatusEnum), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    incident = relationship("Incident", back_populates="status_history")
    updated_by_user = relationship("User", back_populates="status_updates")


class AnalysisBrief(Base):
    """AI-generated analysis brief model"""
    __tablename__ = "analysis_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    # Analysis content
    executive_summary = Column(Text, nullable=False)
    root_cause_primary = Column(Text, nullable=False)
    root_cause_confidence = Column(Float, nullable=False)
    root_cause_evidence = Column(JSON, nullable=True)  # List of strings
    root_cause_factors = Column(JSON, nullable=True)  # List of strings
    
    # Impact
    users_affected = Column(String, nullable=True)
    estimated_cost = Column(String, nullable=True)
    services_impacted = Column(JSON, nullable=True)  # List of strings
    
    # Actions
    recommended_actions = Column(JSON, nullable=True)  # List of action objects
    timeline_summary = Column(Text, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)
    model_version = Column(String, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="analysis_briefs")


class AuditLog(Base):
    """Audit log for tracking all actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String, nullable=True)  # Denormalized for historical records
    action = Column(String, nullable=False)  # e.g., "incident_created", "status_updated"
    resource_type = Column(String, nullable=False)  # e.g., "incident", "user"
    resource_id = Column(String, nullable=True)  # ID of the resource
    details = Column(JSON, nullable=True)  # Additional action details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
