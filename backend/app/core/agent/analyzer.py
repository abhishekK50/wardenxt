"""
Incident Analyzer
Orchestrates AI-powered incident analysis using Gemini 3
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger

from app.models.incident import Incident, LogEntry, MetricPoint
from app.models.analysis import (
    IncidentBrief, RootCauseAnalysis, MitigationAction,
    ImpactAssessment, AgentStatus, AnalysisStatus,
    ConfidenceLevel
)
from .gemini_client import GeminiClient
from .status_stream import get_status_stream


class IncidentAnalyzer:
    """Analyzes incidents using Gemini 3 AI"""
    
    def __init__(self):
        """Initialize analyzer with Gemini client"""
        self.gemini = GeminiClient()
        self.status_stream = get_status_stream()
        self.agent_status = AgentStatus(
            status="IDLE",
            progress=0.0
        )
        self.reasoning_steps: List[str] = []
        self.logger = get_logger(__name__)
    
    async def analyze_incident(
        self,
        incident: Incident,
        max_logs: int = 1000
    ) -> IncidentBrief:
        """Perform comprehensive incident analysis
        
        Args:
            incident: Complete incident data
            max_logs: Maximum number of logs to analyze
            
        Returns:
            AI-generated incident brief
        """
        
        # Reset reasoning steps
        self.reasoning_steps = []
        
        # Update agent status
        self.agent_status.status = "ANALYZING"
        self.agent_status.current_task = "Loading incident data"
        self.agent_status.progress = 0.1
        await self._emit_status_update(incident.summary.incident_id, "Loading incident data...")
        
        # Prepare data for Gemini
        summary_dict = incident.summary.model_dump()
        await self._emit_status_update(incident.summary.incident_id, f"Preparing data for analysis...")
        
        # Sample logs intelligently (prioritize errors)
        logs_dict = self._prepare_logs(incident.logs, max_logs)
        self.agent_status.logs_analyzed = len(logs_dict)
        self.agent_status.progress = 0.3
        await self._emit_status_update(
            incident.summary.incident_id,
            f"Analyzed {len(logs_dict)} log entries",
            reasoning_step=f"Found {len([l for l in logs_dict if l.get('level') in ['ERROR', 'CRITICAL']])} critical errors"
        )
        
        # Sample metrics
        metrics_dict = self._prepare_metrics(incident.metrics)
        self.agent_status.metrics_analyzed = len(metrics_dict)
        self.agent_status.progress = 0.5
        await self._emit_status_update(
            incident.summary.incident_id,
            f"Analyzed {len(metrics_dict)} metric points",
            reasoning_step="Correlating metrics with log patterns"
        )
        
        # Timeline
        timeline_dict = [event.model_dump() for event in incident.timeline]
        
        # Generate brief using Gemini
        self.agent_status.current_task = "Analyzing with Gemini 3"
        self.agent_status.progress = 0.6
        await self._emit_status_update(
            incident.summary.incident_id,
            "Sending data to Gemini 3 for analysis",
            reasoning_step="Using Total Recall context (1M+ tokens) for comprehensive analysis"
        )
        
        try:
            brief_text = self.gemini.generate_incident_brief(
                incident_summary=summary_dict,
                logs_sample=logs_dict,
                metrics_sample=metrics_dict,
                timeline=timeline_dict
            )
            
            await self._emit_status_update(
                incident.summary.incident_id,
                "Received analysis from Gemini 3",
                reasoning_step="AI identified root cause with evidence"
            )
            
            # Parse AI response
            self.agent_status.current_task = "Parsing analysis results"
            self.agent_status.progress = 0.9
            await self._emit_status_update(incident.summary.incident_id, "Structuring analysis results")
            
            brief = self._parse_brief_response(brief_text, incident.summary.incident_id)
            
            # Add final reasoning step
            self.reasoning_steps.append(f"Root cause identified: {brief.root_cause.primary_cause} (confidence: {brief.root_cause.confidence:.0%})")
            self.reasoning_steps.append(f"Generated {len(brief.recommended_actions)} mitigation actions")
            
            self.agent_status.status = "IDLE"
            self.agent_status.current_task = None
            self.agent_status.progress = 1.0
            self.agent_status.insights_generated += 1
            
            await self._emit_status_update(
                incident.summary.incident_id,
                "Analysis complete",
                progress=1.0,
                reasoning_step="Analysis completed successfully"
            )
            
            return brief
            
        except Exception as e:
            self.agent_status.status = "IDLE"
            self.agent_status.current_task = None
            self.logger.error(
                "analysis_failed",
                extra_fields={
                    "incident_id": incident.summary.incident_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise RuntimeError(f"Analysis failed: {str(e)}")
    
    def _prepare_logs(self, logs: List[LogEntry], max_logs: int) -> List[Dict]:
        """Prepare logs for analysis - prioritize errors
        
        Args:
            logs: All log entries
            max_logs: Maximum to include
            
        Returns:
            Sampled and serialized logs
        """
        # Separate by severity
        critical_logs = [log for log in logs if log.level == "CRITICAL"]
        error_logs = [log for log in logs if log.level == "ERROR"]
        warn_logs = [log for log in logs if log.level == "WARN"]
        info_logs = [log for log in logs if log.level == "INFO"]
        
        # Prioritize critical errors
        sampled = []
        
        # All critical logs
        sampled.extend(critical_logs)
        
        # Most error logs
        remaining = max_logs - len(sampled)
        sampled.extend(error_logs[:remaining])
        
        # Some warn logs
        remaining = max_logs - len(sampled)
        sampled.extend(warn_logs[:remaining // 4])
        
        # Few info logs for context
        remaining = max_logs - len(sampled)
        sampled.extend(info_logs[:remaining // 2])
        
        return [log.model_dump() for log in sampled[:max_logs]]
    
    def _prepare_metrics(self, metrics: List[MetricPoint]) -> List[Dict]:
        """Prepare metrics for analysis
        
        Args:
            metrics: All metric points
            
        Returns:
            Sampled metrics showing progression
        """
        # Sample evenly to show progression over time
        total = len(metrics)
        
        if total <= 50:
            # Include all if small dataset
            return [m.model_dump() for m in metrics]
        
        # Sample ~50 points evenly distributed
        step = total // 50
        sampled = [metrics[i] for i in range(0, total, step)]
        
        return [m.model_dump() for m in sampled]
    
    def _parse_brief_response(self, response_text: str, incident_id: str) -> IncidentBrief:
        """Parse Gemini response into IncidentBrief
        
        Args:
            response_text: Raw text from Gemini
            incident_id: Incident identifier
            
        Returns:
            Structured IncidentBrief
        """
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                # Extract JSON from code block
                parts = cleaned.split('```')
                for part in parts:
                    if part.strip().startswith('{'):
                        cleaned = part.strip()
                        break
                    elif part.strip().startswith('json'):
                        cleaned = part.strip()[4:].strip()
                        break
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Build RootCauseAnalysis
            root_cause_data = data.get('root_cause', {})
            root_cause = RootCauseAnalysis(
                primary_cause=root_cause_data.get('primary_cause', 'Unknown'),
                confidence=root_cause_data.get('confidence', 0.5),
                confidence_level=self._confidence_to_level(root_cause_data.get('confidence', 0.5)),
                evidence=root_cause_data.get('evidence', []),
                contributing_factors=root_cause_data.get('contributing_factors'),
                similar_incidents=root_cause_data.get('similar_incidents')
            )
            
            # Build ImpactAssessment
            impact_data = data.get('impact', {})
            impact = ImpactAssessment(
                users_affected=impact_data.get('users_affected', 'Unknown'),
                estimated_cost=impact_data.get('estimated_cost', 'Unknown'),
                services_impacted=impact_data.get('services_impacted', []),
                severity_justification=impact_data.get('severity_justification', '')
            )
            
            # Build MitigationActions
            actions_data = data.get('recommended_actions', [])
            actions = [
                MitigationAction(
                    priority=action.get('priority', 'MEDIUM'),
                    action=action.get('action', ''),
                    estimated_time=action.get('estimated_time', 'Unknown'),
                    risk_level=action.get('risk_level', 'Medium'),
                    command=action.get('command')
                )
                for action in actions_data
            ]
            
            # Build complete brief
            brief = IncidentBrief(
                incident_id=incident_id,
                executive_summary=data.get('executive_summary', ''),
                root_cause=root_cause,
                impact=impact,
                recommended_actions=actions,
                timeline_summary=data.get('timeline_summary', ''),
                generated_at=datetime.utcnow().isoformat() + 'Z',
                analysis_status=AnalysisStatus.COMPLETED
            )
            
            return brief
            
        except json.JSONDecodeError as e:
            # Fallback: create basic brief from raw text
            return self._create_fallback_brief(response_text, incident_id)
        except Exception as e:
            raise RuntimeError(f"Failed to parse brief: {str(e)}")
    
    def _confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to level
        
        Args:
            confidence: 0.0-1.0
            
        Returns:
            ConfidenceLevel enum
        """
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.75:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _create_fallback_brief(self, text: str, incident_id: str) -> IncidentBrief:
        """Create basic brief when JSON parsing fails
        
        Args:
            text: Raw response text
            incident_id: Incident identifier
            
        Returns:
            Basic IncidentBrief
        """
        return IncidentBrief(
            incident_id=incident_id,
            executive_summary=text[:500],  # First 500 chars
            root_cause=RootCauseAnalysis(
                primary_cause="Analysis completed - see summary",
                confidence=0.5,
                confidence_level=ConfidenceLevel.MEDIUM,
                evidence=["See full analysis text"]
            ),
            impact=ImpactAssessment(
                users_affected="See analysis",
                estimated_cost="See analysis",
                services_impacted=[],
                severity_justification="See analysis text"
            ),
            recommended_actions=[
                MitigationAction(
                    priority="MEDIUM",
                    action="Review full analysis for recommendations",
                    estimated_time="N/A",
                    risk_level="Low"
                )
            ],
            timeline_summary=text,
            generated_at=datetime.utcnow().isoformat() + 'Z',
            analysis_status=AnalysisStatus.COMPLETED
        )
    
    async def _emit_status_update(
        self,
        incident_id: str,
        task: str,
        progress: Optional[float] = None,
        reasoning_step: Optional[str] = None
    ):
        """Emit status update to stream
        
        Args:
            incident_id: Incident identifier
            task: Task description
            progress: Optional progress override
            reasoning_step: Optional reasoning step to add
        """
        if reasoning_step:
            self.reasoning_steps.append(reasoning_step)
        
        await self.status_stream.update_status(
            incident_id=incident_id,
            status=self.agent_status.status,
            current_task=task,
            progress=progress if progress is not None else self.agent_status.progress,
            logs_analyzed=self.agent_status.logs_analyzed,
            metrics_analyzed=self.agent_status.metrics_analyzed,
            reasoning_steps=self.reasoning_steps.copy()
        )
    
    def get_agent_status(self) -> AgentStatus:
        """Get current agent status
        
        Returns:
            Current AgentStatus
        """
        return self.agent_status