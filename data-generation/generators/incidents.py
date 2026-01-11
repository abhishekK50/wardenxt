"""
Incident Generator - Orchestrates generation of complete incident datasets
Combines logs, metrics, and timeline into coherent incident scenarios
"""

import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .logs import LogGenerator, LogEntry
from .metrics import MetricsGenerator, MetricPoint


@dataclass
class IncidentScenario:
    """Complete incident scenario definition"""
    incident_id: str
    incident_type: str
    severity: str
    title: str
    description: str
    start_time: datetime
    duration_minutes: int
    services_affected: List[str]
    timeline: List[Dict]
    root_cause: Dict
    mitigation_steps: List[str]
    lessons_learned: List[str]
    estimated_cost: str
    users_impacted: str
    mttr_actual: Optional[str] = None
    technical_metadata: Optional[Dict] = None
    business_impact: Optional[Dict] = None
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'IncidentScenario':
        """Load incident scenario from YAML file"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse start_time if it's a string
        if isinstance(data.get('start_time'), str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        
        # Extract only fields that belong to IncidentScenario
        valid_fields = {
            'incident_id', 'incident_type', 'severity', 'title', 'description',
            'start_time', 'duration_minutes', 'services_affected', 'timeline',
            'root_cause', 'mitigation_steps', 'lessons_learned', 'estimated_cost',
            'users_impacted', 'mttr_actual', 'technical_metadata', 'business_impact'
        }
        
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


@dataclass
class IncidentDataset:
    """Complete generated dataset for an incident"""
    scenario: IncidentScenario
    logs: List[LogEntry]
    metrics: List[MetricPoint]
    timeline: List[Dict]
    summary: Dict
    
    def save_to_directory(self, output_dir: Path):
        """Save all incident data to directory"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        incident_dir = output_dir / self.scenario.incident_id
        incident_dir.mkdir(exist_ok=True)
        
        # Save logs
        logs_file = incident_dir / "logs.jsonl"
        with open(logs_file, 'w') as f:
            for log in self.logs:
                f.write(log.to_json() + '\n')
        
        # Save metrics
        metrics_file = incident_dir / "metrics.jsonl"
        with open(metrics_file, 'w') as f:
            for metric in self.metrics:
                f.write(metric.to_json() + '\n')
        
        # Save timeline
        timeline_file = incident_dir / "timeline.json"
        with open(timeline_file, 'w') as f:
            json.dump(self.timeline, f, indent=2)
        
        # Save summary
        summary_file = incident_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(self.summary, f, indent=2)
        
        print(f"✓ Saved incident data to {incident_dir}")
        print(f"  - {len(self.logs)} log entries")
        print(f"  - {len(self.metrics)} metric points")
        print(f"  - {len(self.timeline)} timeline events")


class IncidentGenerator:
    """Generates complete incident datasets from scenario definitions"""
    
    def __init__(self, scenario: IncidentScenario):
        """Initialize incident generator
        
        Args:
            scenario: Incident scenario definition
        """
        self.scenario = scenario
        self.log_gen = LogGenerator(
            start_time=scenario.start_time,
            service=scenario.services_affected[0] if scenario.services_affected else "payment-api"
        )
        self.metrics_gen = MetricsGenerator(
            start_time=scenario.start_time,
            service=scenario.services_affected[0] if scenario.services_affected else "payment-api"
        )
    
    def generate(self) -> IncidentDataset:
        """Generate complete incident dataset"""
        
        # Parse timeline to extract phases
        phases = self._extract_phases_from_timeline()
        
        # Generate logs based on incident type
        logs = self._generate_incident_logs(phases)
        
        # Generate metrics based on incident type
        metrics = self._generate_incident_metrics(phases)
        
        # Build enhanced timeline
        timeline = self._build_detailed_timeline()
        
        # Create summary
        summary = self._create_summary()
        
        return IncidentDataset(
            scenario=self.scenario,
            logs=logs,
            metrics=metrics,
            timeline=timeline,
            summary=summary
        )
    
    def _extract_phases_from_timeline(self) -> List[Dict]:
        """Extract incident phases from timeline"""
        phases = []
        
        for idx, event in enumerate(self.scenario.timeline):
            # Parse time from timeline event
            event_time = event.get('time', '00:00')
            
            # Calculate minutes from start
            if ':' in event_time:
                hours, minutes = map(int, event_time.split(':'))
                minutes_from_start = hours * 60 + minutes
            else:
                minutes_from_start = 0
            
            phases.append({
                'event': event.get('event', ''),
                'impact': event.get('impact', ''),
                'minutes_from_start': minutes_from_start,
                'duration': 0  # Will be calculated
            })
        
        # Calculate durations between phases
        for i in range(len(phases) - 1):
            phases[i]['duration'] = phases[i + 1]['minutes_from_start'] - phases[i]['minutes_from_start']
        
        # Last phase duration
        if phases:
            phases[-1]['duration'] = self.scenario.duration_minutes - phases[-1]['minutes_from_start']
        
        return phases
    
    def _generate_incident_logs(self, phases: List[Dict]) -> List[LogEntry]:
        """Generate logs for the incident"""
        all_logs = []
        
        # Map incident type to error progression
        if self.scenario.incident_type == "bmr_recovery":
            # BMR has distinct phases: failure, recovery start, restoration
            severity_progression = [0.0, 1.0, 0.8, 0.4, 0.1, 0.0]
        elif "connection" in self.scenario.incident_type.lower():
            severity_progression = [0.0, 0.1, 0.3, 0.7, 0.4, 0.1]
        elif "memory" in self.scenario.incident_type.lower():
            severity_progression = [0.0, 0.05, 0.15, 0.35, 0.6, 0.3]
        else:
            severity_progression = [0.0, 0.2, 0.5, 0.7, 0.4, 0.1]
        
        logs = self.log_gen.generate_incident_logs(
            incident_type=self._map_incident_to_log_type(),
            duration_minutes=self.scenario.duration_minutes,
            severity_progression=severity_progression
        )
        
        all_logs.extend(logs)
        
        return all_logs
    
    def _generate_incident_metrics(self, phases: List[Dict]) -> List[MetricPoint]:
        """Generate metrics for the incident"""
        
        # Build phase configurations based on incident type
        if self.scenario.incident_type == "bmr_recovery":
            phase_configs = self._build_bmr_phases()
        elif "connection" in self.scenario.incident_type.lower():
            phase_configs = self._build_connection_pool_phases()
        elif "memory" in self.scenario.incident_type.lower():
            phase_configs = self._build_memory_leak_phases()
        else:
            phase_configs = self._build_generic_phases()
        
        metrics = self.metrics_gen.generate_incident_metrics(
            incident_type=self.scenario.incident_type,
            duration_minutes=self.scenario.duration_minutes,
            phases=phase_configs,
            interval_seconds=60
        )
        
        return metrics
    
    def _build_bmr_phases(self) -> List[Dict]:
        """Build metric phases for BMR recovery"""
        return [
            # Pre-incident (normal)
            {"cpu": 25, "memory": 1200, "requests": 150, "error_rate": 0.002, "latency": 45, "recovering": False},
            # Server failure detected
            {"cpu": 0, "memory": 0, "requests": 0, "error_rate": 1.0, "latency": 0, "recovering": False},
            # BMR in progress (still down)
            {"cpu": 0, "memory": 0, "requests": 0, "error_rate": 1.0, "latency": 0, "recovering": False},
            # OS restored, DB installing
            {"cpu": 5, "memory": 200, "requests": 0, "error_rate": 1.0, "latency": 0, "recovering": True},
            # DB restored, verification
            {"cpu": 15, "memory": 800, "requests": 20, "error_rate": 0.3, "latency": 500, "recovering": True},
            # Service back online
            {"cpu": 25, "memory": 1200, "requests": 140, "error_rate": 0.01, "latency": 60, "recovering": True}
        ]
    
    def _build_connection_pool_phases(self) -> List[Dict]:
        """Build metric phases for connection pool exhaustion"""
        return [
            {"cpu": 25, "memory": 1200, "requests": 150, "error_rate": 0.002, "latency": 45, 
             "active_connections": 50, "max_connections": 100, "pool_usage": 0.5},
            {"cpu": 30, "memory": 1400, "requests": 160, "error_rate": 0.01, "latency": 80,
             "active_connections": 50, "max_connections": 100, "pool_usage": 0.7},
            {"cpu": 35, "memory": 1800, "requests": 150, "error_rate": 0.05, "latency": 200,
             "active_connections": 50, "max_connections": 100, "pool_usage": 0.9},
            {"cpu": 40, "memory": 2200, "requests": 100, "error_rate": 0.15, "latency": 500,
             "active_connections": 50, "max_connections": 100, "pool_usage": 0.98},
            {"cpu": 30, "memory": 1600, "requests": 130, "error_rate": 0.03, "latency": 100,
             "active_connections": 50, "max_connections": 150, "pool_usage": 0.5},
            {"cpu": 25, "memory": 1300, "requests": 145, "error_rate": 0.005, "latency": 50,
             "active_connections": 50, "max_connections": 150, "pool_usage": 0.4}
        ]
    
    def _build_memory_leak_phases(self) -> List[Dict]:
        """Build metric phases for memory leak"""
        return [
            {"cpu": 25, "memory_base": 1200, "memory_growth": 0, "requests": 150, "error_rate": 0.002, "latency": 45},
            {"cpu": 28, "memory_base": 1200, "memory_growth": 400, "requests": 145, "error_rate": 0.005, "latency": 60},
            {"cpu": 32, "memory_base": 1200, "memory_growth": 900, "requests": 135, "error_rate": 0.02, "latency": 100},
            {"cpu": 38, "memory_base": 1200, "memory_growth": 1500, "requests": 110, "error_rate": 0.08, "latency": 250},
            {"cpu": 30, "memory_base": 1200, "memory_growth": 200, "requests": 140, "error_rate": 0.01, "latency": 70},
            {"cpu": 26, "memory_base": 1200, "memory_growth": 0, "requests": 148, "error_rate": 0.003, "latency": 48}
        ]
    
    def _build_generic_phases(self) -> List[Dict]:
        """Build generic degradation phases"""
        return [
            {"cpu": 25, "memory": 1200, "requests": 150, "error_rate": 0.002, "latency": 45},
            {"cpu": 35, "memory": 1400, "requests": 140, "error_rate": 0.02, "latency": 100},
            {"cpu": 50, "memory": 1600, "requests": 120, "error_rate": 0.08, "latency": 200},
            {"cpu": 65, "memory": 1800, "requests": 90, "error_rate": 0.15, "latency": 350},
            {"cpu": 40, "memory": 1500, "requests": 130, "error_rate": 0.04, "latency": 120},
            {"cpu": 28, "memory": 1250, "requests": 145, "error_rate": 0.005, "latency": 55}
        ]
    
    def _map_incident_to_log_type(self) -> str:
        """Map incident type to log message category"""
        incident_lower = self.scenario.incident_type.lower()
        
        if "connection" in incident_lower or "pool" in incident_lower:
            return "connection"
        elif "memory" in incident_lower:
            return "memory"
        elif "timeout" in incident_lower:
            return "timeout"
        else:
            return "general"
    
    def _build_detailed_timeline(self) -> List[Dict]:
        """Build detailed timeline with all events"""
        timeline = []
        
        for event in self.scenario.timeline:
            timeline.append({
                "time": event.get("time", ""),
                "event": event.get("event", ""),
                "impact": event.get("impact", ""),
                "type": "incident_event"
            })
        
        return timeline
    
    def _create_summary(self) -> Dict:
        """Create incident summary"""
        return {
            "incident_id": self.scenario.incident_id,
            "title": self.scenario.title,
            "severity": self.scenario.severity,
            "duration_minutes": self.scenario.duration_minutes,
            "services_affected": self.scenario.services_affected,
            "root_cause": self.scenario.root_cause,
            "estimated_cost": self.scenario.estimated_cost,
            "users_impacted": self.scenario.users_impacted,
            "mitigation_steps": self.scenario.mitigation_steps,
            "lessons_learned": self.scenario.lessons_learned
        }