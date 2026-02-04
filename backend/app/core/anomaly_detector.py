"""
Anomaly Detector
Detects anomalies in metrics, logs, and system behavior
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics
import random
import uuid

from app.models.prediction import Anomaly
from app.models.incident import MetricPoint, LogEntry
from app.core.logging import get_logger

logger = get_logger(__name__)

# Baseline thresholds (would be learned from historical data in production)
BASELINES = {
    "cpu_percent": {"mean": 55, "std": 15, "warning": 75, "critical": 85},
    "memory_percent": {"mean": 65, "std": 12, "warning": 80, "critical": 90},
    "memory_mb": {"mean": 1200, "std": 300, "warning": 1600, "critical": 1900},
    "error_rate": {"mean": 0.005, "std": 0.01, "warning": 0.02, "critical": 0.05},
    "requests_per_sec": {"mean": 500, "std": 150, "warning_low": 200, "warning_high": 900},
    "latency_p99_ms": {"mean": 150, "std": 50, "warning": 300, "critical": 500},
}

# In-memory storage for detected anomalies
detected_anomalies: List[Anomaly] = []
MAX_ANOMALIES = 50


def detect_metric_anomalies(metrics: List[MetricPoint]) -> List[Anomaly]:
    """Detect anomalies in metric data

    Args:
        metrics: List of metric points to analyze

    Returns:
        List of detected anomalies
    """
    anomalies = []

    if not metrics:
        # Generate simulated anomalies for demo
        return detect_simulated_anomalies()

    for metric in metrics[-10:]:  # Analyze last 10 data points
        metric_data = metric.metrics

        # Check each metric against baselines
        for metric_name, value in metric_data.items():
            if metric_name not in BASELINES:
                continue

            baseline = BASELINES[metric_name]
            expected = baseline["mean"]

            # Calculate deviation
            if expected > 0:
                deviation_pct = abs((value - expected) / expected) * 100
            else:
                deviation_pct = abs(value) * 100

            # Check for anomaly
            anomaly = None

            if "critical" in baseline and value > baseline["critical"]:
                anomaly = create_anomaly(
                    metric_name=metric_name,
                    metric_type=get_metric_type(metric_name),
                    current_value=value,
                    expected_value=expected,
                    deviation_pct=deviation_pct,
                    severity="severe",
                    timestamp=metric.timestamp
                )
            elif "warning" in baseline and value > baseline["warning"]:
                anomaly = create_anomaly(
                    metric_name=metric_name,
                    metric_type=get_metric_type(metric_name),
                    current_value=value,
                    expected_value=expected,
                    deviation_pct=deviation_pct,
                    severity="moderate",
                    timestamp=metric.timestamp
                )
            elif deviation_pct > 50:  # 50% deviation is always noteworthy
                anomaly = create_anomaly(
                    metric_name=metric_name,
                    metric_type=get_metric_type(metric_name),
                    current_value=value,
                    expected_value=expected,
                    deviation_pct=deviation_pct,
                    severity="minor",
                    timestamp=metric.timestamp
                )

            if anomaly:
                anomalies.append(anomaly)

    # Store anomalies
    for anomaly in anomalies:
        store_anomaly(anomaly)

    return anomalies


def detect_log_anomalies(logs: List[LogEntry]) -> List[Anomaly]:
    """Detect anomalies in log data

    Args:
        logs: List of log entries to analyze

    Returns:
        List of detected anomalies
    """
    anomalies = []

    if not logs:
        return []

    # Analyze last 100 logs
    recent_logs = logs[-100:]

    # Count error types
    error_count = sum(1 for log in recent_logs if log.level in ['ERROR', 'CRITICAL'])
    warning_count = sum(1 for log in recent_logs if log.level == 'WARNING')

    # Expected: ~0.5% errors, ~2% warnings
    error_rate = error_count / len(recent_logs) if recent_logs else 0
    warning_rate = warning_count / len(recent_logs) if recent_logs else 0

    # Check for error rate anomaly
    if error_rate > 0.05:  # >5% errors is severe
        anomaly = Anomaly(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            detected_at=datetime.utcnow().isoformat(),
            metric_name="error_log_rate",
            metric_type="error",
            current_value=error_rate * 100,
            expected_value=0.5,
            deviation_percentage=(error_rate - 0.005) / 0.005 * 100,
            severity="severe",
            likely_cause="High error rate in application logs",
            recommended_action="Investigate recent error logs for root cause",
            related_service=extract_service_from_logs(recent_logs)
        )
        anomalies.append(anomaly)
        store_anomaly(anomaly)
    elif error_rate > 0.02:  # >2% errors is moderate
        anomaly = Anomaly(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            detected_at=datetime.utcnow().isoformat(),
            metric_name="error_log_rate",
            metric_type="error",
            current_value=error_rate * 100,
            expected_value=0.5,
            deviation_percentage=(error_rate - 0.005) / 0.005 * 100,
            severity="moderate",
            likely_cause="Elevated error rate in application logs",
            recommended_action="Monitor error trends and investigate if persists",
            related_service=extract_service_from_logs(recent_logs)
        )
        anomalies.append(anomaly)
        store_anomaly(anomaly)

    # Check for new error types
    error_messages = [log.message for log in recent_logs if log.level == 'ERROR']
    unique_errors = set(error_messages)

    if len(unique_errors) > 5:  # Multiple unique errors
        anomaly = Anomaly(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            detected_at=datetime.utcnow().isoformat(),
            metric_name="unique_error_types",
            metric_type="error",
            current_value=len(unique_errors),
            expected_value=2,
            deviation_percentage=((len(unique_errors) - 2) / 2) * 100,
            severity="moderate",
            likely_cause=f"{len(unique_errors)} different error types detected",
            recommended_action="Review error diversity - may indicate cascading failures",
            related_service=extract_service_from_logs(recent_logs)
        )
        anomalies.append(anomaly)
        store_anomaly(anomaly)

    return anomalies


def detect_behavioral_anomalies() -> List[Anomaly]:
    """Detect behavioral anomalies (traffic patterns, resource usage)

    Returns:
        List of detected behavioral anomalies
    """
    anomalies = []

    # Simulate behavioral analysis for demo
    current_hour = datetime.now().hour

    # Check if traffic is unusual for time of day
    if current_hour in [2, 3, 4, 5]:  # Low traffic hours
        # Simulate checking for unexpected high traffic
        if random.random() < 0.3:  # 30% chance of anomaly
            anomaly = Anomaly(
                anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
                detected_at=datetime.utcnow().isoformat(),
                metric_name="traffic_pattern",
                metric_type="network",
                current_value=800,  # requests/sec
                expected_value=200,  # low traffic expected
                deviation_percentage=300,
                severity="moderate",
                likely_cause="Unexpected high traffic during off-peak hours",
                recommended_action="Investigate traffic source - potential bot/DDoS",
                related_service=None
            )
            anomalies.append(anomaly)
            store_anomaly(anomaly)

    return anomalies


def detect_simulated_anomalies() -> List[Anomaly]:
    """Generate simulated anomalies for demo purposes

    Returns:
        List of simulated anomalies
    """
    anomalies = []
    now = datetime.utcnow().isoformat()

    # Simulate 1-3 anomalies based on random factors
    num_anomalies = random.randint(0, 3)

    possible_anomalies = [
        {
            "metric_name": "memory_percent",
            "metric_type": "memory",
            "current_value": 82 + random.randint(0, 10),
            "expected_value": 65,
            "severity": "moderate",
            "cause": "Memory usage trending above baseline",
            "action": "Monitor memory trends and prepare for potential restart"
        },
        {
            "metric_name": "cpu_percent",
            "metric_type": "cpu",
            "current_value": 78 + random.randint(0, 15),
            "expected_value": 55,
            "severity": "moderate" if random.random() < 0.7 else "severe",
            "cause": "CPU utilization above expected levels",
            "action": "Check for resource-intensive processes"
        },
        {
            "metric_name": "error_rate",
            "metric_type": "error",
            "current_value": 2.5 + random.random() * 2,
            "expected_value": 0.5,
            "severity": "moderate",
            "cause": "Error rate elevated above normal baseline",
            "action": "Review recent error logs for patterns"
        },
        {
            "metric_name": "latency_p99",
            "metric_type": "latency",
            "current_value": 320 + random.randint(0, 100),
            "expected_value": 150,
            "severity": "minor",
            "cause": "API response latency increased",
            "action": "Check upstream dependencies and database queries"
        },
        {
            "metric_name": "connection_pool",
            "metric_type": "database",
            "current_value": 85 + random.randint(0, 10),
            "expected_value": 60,
            "severity": "moderate",
            "cause": "Database connection pool utilization high",
            "action": "Review query patterns and connection management"
        }
    ]

    selected = random.sample(possible_anomalies, min(num_anomalies, len(possible_anomalies)))

    for data in selected:
        deviation = ((data["current_value"] - data["expected_value"]) /
                    data["expected_value"] * 100) if data["expected_value"] > 0 else 100

        anomaly = Anomaly(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            detected_at=now,
            metric_name=data["metric_name"],
            metric_type=data["metric_type"],
            current_value=data["current_value"],
            expected_value=data["expected_value"],
            deviation_percentage=round(deviation, 1),
            severity=data["severity"],
            likely_cause=data["cause"],
            recommended_action=data["action"],
            related_service=random.choice(["api-service", "payment-service", "user-service", None])
        )
        anomalies.append(anomaly)
        store_anomaly(anomaly)

    return anomalies


def create_anomaly(
    metric_name: str,
    metric_type: str,
    current_value: float,
    expected_value: float,
    deviation_pct: float,
    severity: str,
    timestamp: str
) -> Anomaly:
    """Create an Anomaly object with appropriate context

    Args:
        metric_name: Name of the anomalous metric
        metric_type: Type of metric (cpu, memory, etc.)
        current_value: Current value
        expected_value: Expected/baseline value
        deviation_pct: Percentage deviation
        severity: Severity level
        timestamp: When anomaly was detected

    Returns:
        Anomaly object
    """
    cause_map = {
        "cpu_percent": "CPU utilization above expected levels",
        "memory_percent": "Memory usage trending above baseline",
        "memory_mb": "Memory consumption elevated",
        "error_rate": "Error rate above acceptable threshold",
        "requests_per_sec": "Request volume outside normal range",
        "latency_p99_ms": "API latency degradation detected"
    }

    action_map = {
        "cpu_percent": "Check for resource-intensive processes or scale horizontally",
        "memory_percent": "Investigate memory usage patterns and consider service restart",
        "memory_mb": "Monitor for memory leak and prepare mitigation",
        "error_rate": "Review error logs and recent deployments",
        "requests_per_sec": "Verify traffic source and scaling configuration",
        "latency_p99_ms": "Check database queries and upstream dependencies"
    }

    return Anomaly(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        detected_at=timestamp,
        metric_name=metric_name,
        metric_type=metric_type,
        current_value=round(current_value, 2),
        expected_value=round(expected_value, 2),
        deviation_percentage=round(deviation_pct, 1),
        severity=severity,
        likely_cause=cause_map.get(metric_name, "Metric outside expected range"),
        recommended_action=action_map.get(metric_name, "Investigate and monitor"),
        related_service=None
    )


def get_metric_type(metric_name: str) -> str:
    """Get metric type from metric name

    Args:
        metric_name: Name of metric

    Returns:
        Metric type category
    """
    type_map = {
        "cpu_percent": "cpu",
        "memory_percent": "memory",
        "memory_mb": "memory",
        "error_rate": "error",
        "requests_per_sec": "network",
        "latency_p99_ms": "latency"
    }
    return type_map.get(metric_name, "system")


def extract_service_from_logs(logs: List[LogEntry]) -> Optional[str]:
    """Extract service name from log entries

    Args:
        logs: List of log entries

    Returns:
        Service name if found
    """
    # In production, would parse log format for service name
    # For demo, return None or random service
    return None


def store_anomaly(anomaly: Anomaly):
    """Store anomaly in memory

    Args:
        anomaly: Anomaly to store
    """
    global detected_anomalies

    detected_anomalies.append(anomaly)

    # Trim to max size
    if len(detected_anomalies) > MAX_ANOMALIES:
        detected_anomalies = detected_anomalies[-MAX_ANOMALIES:]


def get_current_anomalies() -> List[Anomaly]:
    """Get currently active anomalies

    Returns:
        List of recent anomalies
    """
    # Return anomalies from last 30 minutes
    cutoff = datetime.utcnow().isoformat()  # Simplified for demo
    return detected_anomalies[-10:]  # Last 10 anomalies


def clear_anomaly(anomaly_id: str) -> bool:
    """Dismiss/clear an anomaly

    Args:
        anomaly_id: ID of anomaly to clear

    Returns:
        True if cleared, False if not found
    """
    global detected_anomalies

    original_len = len(detected_anomalies)
    detected_anomalies = [a for a in detected_anomalies if a.anomaly_id != anomaly_id]

    return len(detected_anomalies) < original_len
