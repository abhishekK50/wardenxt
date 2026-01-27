"""
Incident Analyzer Tests
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.core.agent.analyzer import IncidentAnalyzer
from app.models.incident import Incident, IncidentSummary, LogEntry, MetricPoint, TimelineEvent, RootCause, Severity, IncidentStatus


@pytest.fixture
def sample_incident():
    """Create a sample incident for testing"""
    return Incident(
        summary=IncidentSummary(
            incident_id="TEST-001",
            title="Test Incident",
            severity=Severity.P1,
            status=IncidentStatus.DETECTED,
            duration_minutes=60,
            services_affected=["test-service"],
            root_cause=RootCause(primary="Test root cause"),
            estimated_cost="$1000",
            users_impacted="100",
            mitigation_steps=["Step 1", "Step 2"],
            lessons_learned=["Lesson 1"]
        ),
        logs=[
            LogEntry(
                timestamp="2024-01-01T00:00:00Z",
                level="ERROR",
                service="test-service",
                host="host1",
                message="Test error message"
            )
        ],
        metrics=[
            MetricPoint(
                timestamp="2024-01-01T00:00:00Z",
                service="test-service",
                host="host1",
                metrics={"cpu_percent": 80.0}
            )
        ],
        timeline=[
            TimelineEvent(
                time="00:00",
                event="Incident detected",
                impact="Service degraded"
            )
        ],
        status=IncidentStatus.DETECTED
    )


@pytest.mark.asyncio
async def test_analyzer_initialization():
    """Test analyzer initialization"""
    analyzer = IncidentAnalyzer()
    
    assert analyzer.agent_status.status == "IDLE"
    assert analyzer.agent_status.progress == 0.0
    assert len(analyzer.reasoning_steps) == 0


@pytest.mark.asyncio
@patch('app.core.agent.analyzer.GeminiClient')
async def test_analyze_incident_mock(mock_gemini_class, sample_incident):
    """Test incident analysis with mocked Gemini client"""
    # Setup mock
    mock_gemini = Mock()
    mock_gemini.generate_incident_brief.return_value = """{
        "executive_summary": "Test summary",
        "root_cause": {
            "primary_cause": "Test cause",
            "confidence": 0.9,
            "evidence": ["Evidence 1"],
            "contributing_factors": []
        },
        "impact": {
            "users_affected": "100",
            "estimated_cost": "$1000",
            "services_impacted": ["test-service"],
            "severity_justification": "High impact"
        },
        "recommended_actions": [
            {
                "priority": "HIGH",
                "action": "Test action",
                "estimated_time": "5 minutes",
                "risk_level": "Low"
            }
        ],
        "timeline_summary": "Test timeline"
    }"""
    mock_gemini_class.return_value = mock_gemini
    
    analyzer = IncidentAnalyzer()
    analyzer.gemini = mock_gemini
    
    # Run analysis
    brief = await analyzer.analyze_incident(sample_incident, max_logs=100)
    
    assert brief is not None
    assert brief.incident_id == "TEST-001"
    assert brief.executive_summary == "Test summary"
    assert brief.root_cause.primary_cause == "Test cause"
    assert len(brief.recommended_actions) > 0


def test_log_preparation(sample_incident):
    """Test log preparation prioritizes errors"""
    analyzer = IncidentAnalyzer()
    
    # Add more logs with different levels
    sample_incident.logs.extend([
        LogEntry(
            timestamp="2024-01-01T00:01:00Z",
            level="INFO",
            service="test-service",
            host="host1",
            message="Info message"
        ),
        LogEntry(
            timestamp="2024-01-01T00:02:00Z",
            level="CRITICAL",
            service="test-service",
            host="host1",
            message="Critical message"
        )
    ])
    
    prepared = analyzer._prepare_logs(sample_incident.logs, max_logs=10)
    
    # Critical logs should be included
    critical_count = sum(1 for log in prepared if log.get("level") == "CRITICAL")
    assert critical_count > 0


def test_metrics_preparation(sample_incident):
    """Test metrics preparation"""
    analyzer = IncidentAnalyzer()
    
    # Add more metrics
    for i in range(100):
        sample_incident.metrics.append(
            MetricPoint(
                timestamp=f"2024-01-01T00:{i:02d}:00Z",
                service="test-service",
                host="host1",
                metrics={"cpu_percent": 50.0 + i}
            )
        )
    
    prepared = analyzer._prepare_metrics(sample_incident.metrics)
    
    # Should sample metrics (not all 100)
    assert len(prepared) <= 50
    assert len(prepared) > 0
