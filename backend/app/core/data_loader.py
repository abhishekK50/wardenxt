"""
Data Loader
Loads generated incident data from disk
"""

import json
from pathlib import Path
from typing import Optional, List, Dict

from app.models.incident import (
    Incident, IncidentSummary, LogEntry, MetricPoint,
    TimelineEvent, RootCause, IncidentStatus, Severity
)


class DataLoader:
    """Loads incident data from generated datasets"""
    
    def __init__(self, data_directory: str = "../data-generation/output"):
        """Initialize data loader
        
        Args:
            data_directory: Path to generated data directory
        """
        self.data_dir = Path(data_directory)
        
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")
    
    def list_incidents(self) -> List[str]:
        """List all available incident IDs
        
        Returns:
            List of incident IDs
        """
        incident_dirs = [
            d.name for d in self.data_dir.iterdir() 
            if d.is_dir() and (d / "summary.json").exists()
        ]
        return sorted(incident_dirs)
    
    def load_incident(self, incident_id: str) -> Incident:
        """Load complete incident data
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Complete Incident object
            
        Raises:
            ValueError: If incident not found
        """
        incident_dir = self.data_dir / incident_id
        
        if not incident_dir.exists():
            raise ValueError(f"Incident not found: {incident_id}")
        
        # Load summary
        summary = self._load_summary(incident_dir)
        
        # Load logs
        logs = self._load_logs(incident_dir)
        
        # Load metrics
        metrics = self._load_metrics(incident_dir)
        
        # Load timeline
        timeline = self._load_timeline(incident_dir)
        
        return Incident(
            summary=summary,
            logs=logs,
            metrics=metrics,
            timeline=timeline,
            status=IncidentStatus.DETECTED
        )
    
    def _load_summary(self, incident_dir: Path) -> IncidentSummary:
        """Load incident summary
        
        Args:
            incident_dir: Path to incident directory
            
        Returns:
            IncidentSummary object
        """
        summary_file = incident_dir / "summary.json"
        
        with open(summary_file, 'r') as f:
            data = json.load(f)
        
        # Parse root cause
        root_cause_data = data.get('root_cause', {})
        root_cause = RootCause(
            primary=root_cause_data.get('primary', 'Unknown'),
            secondary=root_cause_data.get('secondary'),
            contributing_factors=root_cause_data.get('contributing_factors')
        )
        
        # Map severity string to enum
        severity_str = data.get('severity', 'P2')
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.P2
        
        return IncidentSummary(
            incident_id=data.get('incident_id'),
            title=data.get('title'),
            severity=severity,
            duration_minutes=data.get('duration_minutes'),
            services_affected=data.get('services_affected', []),
            root_cause=root_cause,
            estimated_cost=data.get('estimated_cost', 'Unknown'),
            users_impacted=data.get('users_impacted', 'Unknown'),
            mitigation_steps=data.get('mitigation_steps', []),
            lessons_learned=data.get('lessons_learned', [])
        )
    
    def _load_logs(self, incident_dir: Path) -> List[LogEntry]:
        """Load log entries
        
        Args:
            incident_dir: Path to incident directory
            
        Returns:
            List of LogEntry objects
        """
        logs_file = incident_dir / "logs.jsonl"
        logs = []
        
        with open(logs_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    logs.append(LogEntry(**data))
        
        return logs
    
    def _load_metrics(self, incident_dir: Path) -> List[MetricPoint]:
        """Load metric points
        
        Args:
            incident_dir: Path to incident directory
            
        Returns:
            List of MetricPoint objects
        """
        metrics_file = incident_dir / "metrics.jsonl"
        metrics = []
        
        with open(metrics_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    metrics.append(MetricPoint(**data))
        
        return metrics
    
    def _load_timeline(self, incident_dir: Path) -> List[TimelineEvent]:
        """Load timeline events
        
        Args:
            incident_dir: Path to incident directory
            
        Returns:
            List of TimelineEvent objects
        """
        timeline_file = incident_dir / "timeline.json"
        
        with open(timeline_file, 'r') as f:
            data = json.load(f)
        
        return [TimelineEvent(**event) for event in data]