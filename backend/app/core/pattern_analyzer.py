"""
Pattern Analyzer
Analyzes historical incidents to identify patterns and precursor signals
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from app.models.incident import Incident
from app.models.prediction import HistoricalPattern
from app.core.logging import get_logger

logger = get_logger(__name__)


def analyze_incident_patterns(incidents: List[Incident]) -> Dict[str, Any]:
    """Analyze patterns across historical incidents

    Args:
        incidents: List of historical incidents

    Returns:
        Dictionary containing identified patterns
    """
    if not incidents:
        return {
            "patterns": [],
            "temporal_analysis": {},
            "service_correlations": {},
            "metric_thresholds": {}
        }

    patterns = []

    # Temporal patterns (time of day, day of week)
    temporal = analyze_temporal_patterns(incidents)
    if temporal.get("peak_hour"):
        patterns.append(HistoricalPattern(
            pattern_id=f"PAT-TEMPORAL-001",
            pattern_type="temporal",
            description=f"Incidents most common at {temporal['peak_hour']}:00 ({temporal['peak_hour_count']} occurrences)",
            frequency=temporal['peak_hour_count'],
            confidence=min(100, temporal['peak_hour_count'] * 20),
            associated_incident_types=temporal.get('types_at_peak', []),
            precursor_signals=[f"Time approaching {temporal['peak_hour']}:00"],
            typical_lead_time="1-2 hours before peak time"
        ))

    # Service correlation patterns
    correlations = analyze_service_correlations(incidents)
    for correlation in correlations:
        patterns.append(HistoricalPattern(
            pattern_id=f"PAT-CORR-{len(patterns)+1:03d}",
            pattern_type="correlation",
            description=f"When {correlation['service_a']} fails, {correlation['service_b']} often follows",
            frequency=correlation['occurrences'],
            confidence=correlation['confidence'],
            associated_incident_types=correlation['incident_types'],
            precursor_signals=[f"Issues in {correlation['service_a']}"],
            typical_lead_time=correlation.get('typical_delay', 'minutes to hours')
        ))

    # Incident type patterns
    type_patterns = analyze_incident_type_patterns(incidents)
    for type_pattern in type_patterns:
        patterns.append(HistoricalPattern(
            pattern_id=f"PAT-TYPE-{len(patterns)+1:03d}",
            pattern_type="sequence",
            description=type_pattern['description'],
            frequency=type_pattern['frequency'],
            confidence=type_pattern['confidence'],
            associated_incident_types=[type_pattern['incident_type']],
            precursor_signals=type_pattern.get('precursors', []),
            typical_lead_time=type_pattern.get('lead_time', 'unknown')
        ))

    # Metric threshold patterns
    thresholds = analyze_metric_threshold_patterns(incidents)

    return {
        "patterns": [p.dict() for p in patterns],
        "temporal_analysis": temporal,
        "service_correlations": correlations,
        "metric_thresholds": thresholds,
        "total_incidents_analyzed": len(incidents),
        "patterns_identified": len(patterns)
    }


def analyze_temporal_patterns(incidents: List[Incident]) -> Dict[str, Any]:
    """Analyze time-based patterns in incidents

    Args:
        incidents: List of incidents

    Returns:
        Temporal pattern analysis
    """
    hour_counts = defaultdict(int)
    day_counts = defaultdict(int)
    types_by_hour = defaultdict(list)

    for incident in incidents:
        try:
            # Parse timestamp from incident
            start_time = incident.summary.start_time
            if isinstance(start_time, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                dt = start_time

            hour = dt.hour
            day = dt.strftime('%A')

            hour_counts[hour] += 1
            day_counts[day] += 1
            types_by_hour[hour].append(incident.summary.incident_type)

        except Exception as e:
            logger.warning(f"Could not parse timestamp: {e}")
            continue

    # Find peak hour
    peak_hour = max(hour_counts.keys(), key=lambda h: hour_counts[h]) if hour_counts else None
    peak_day = max(day_counts.keys(), key=lambda d: day_counts[d]) if day_counts else None

    return {
        "hour_distribution": dict(hour_counts),
        "day_distribution": dict(day_counts),
        "peak_hour": peak_hour,
        "peak_hour_count": hour_counts.get(peak_hour, 0) if peak_hour else 0,
        "peak_day": peak_day,
        "peak_day_count": day_counts.get(peak_day, 0) if peak_day else 0,
        "types_at_peak": list(set(types_by_hour.get(peak_hour, []))) if peak_hour else [],
        "low_risk_hours": [h for h, c in hour_counts.items() if c == min(hour_counts.values())] if hour_counts else []
    }


def analyze_service_correlations(incidents: List[Incident]) -> List[Dict[str, Any]]:
    """Find correlations between services in incidents

    Args:
        incidents: List of incidents

    Returns:
        List of service correlation patterns
    """
    # Track which services appear together in incidents
    service_pairs = defaultdict(int)
    service_incident_types = defaultdict(list)

    for incident in incidents:
        services = incident.summary.services_affected
        incident_type = incident.summary.incident_type

        # Track service pairs
        for i, service_a in enumerate(services):
            service_incident_types[service_a].append(incident_type)
            for service_b in services[i+1:]:
                pair = tuple(sorted([service_a, service_b]))
                service_pairs[pair] += 1

    # Build correlation list
    correlations = []
    for (service_a, service_b), count in service_pairs.items():
        if count >= 2:  # At least 2 co-occurrences
            correlations.append({
                "service_a": service_a,
                "service_b": service_b,
                "occurrences": count,
                "confidence": min(100, count * 25),
                "incident_types": list(set(
                    service_incident_types[service_a] +
                    service_incident_types[service_b]
                )),
                "typical_delay": "immediate to 30 minutes"
            })

    return sorted(correlations, key=lambda x: x['occurrences'], reverse=True)


def analyze_incident_type_patterns(incidents: List[Incident]) -> List[Dict[str, Any]]:
    """Analyze patterns specific to incident types

    Args:
        incidents: List of incidents

    Returns:
        List of incident type patterns
    """
    type_stats = defaultdict(lambda: {
        "count": 0,
        "severities": [],
        "durations": [],
        "services": []
    })

    for incident in incidents:
        inc_type = incident.summary.incident_type
        type_stats[inc_type]["count"] += 1
        type_stats[inc_type]["severities"].append(incident.summary.severity)
        type_stats[inc_type]["durations"].append(incident.summary.duration_minutes)
        type_stats[inc_type]["services"].extend(incident.summary.services_affected)

    patterns = []
    for inc_type, stats in type_stats.items():
        avg_duration = statistics.mean(stats["durations"]) if stats["durations"] else 0
        most_common_severity = max(set(stats["severities"]), key=stats["severities"].count) if stats["severities"] else "P2"

        # Identify precursors based on incident type
        precursors = get_type_specific_precursors(inc_type)

        patterns.append({
            "incident_type": inc_type,
            "description": f"{inc_type.replace('_', ' ').title()} incidents occur {stats['count']} times, typically {most_common_severity}",
            "frequency": stats["count"],
            "confidence": min(100, stats["count"] * 20),
            "average_duration_minutes": avg_duration,
            "most_common_severity": most_common_severity,
            "affected_services": list(set(stats["services"])),
            "precursors": precursors,
            "lead_time": get_typical_lead_time(inc_type)
        })

    return patterns


def get_type_specific_precursors(incident_type: str) -> List[str]:
    """Get known precursor signals for specific incident types

    Args:
        incident_type: Type of incident

    Returns:
        List of precursor signals
    """
    precursor_map = {
        "memory_leak": [
            "Memory usage steadily increasing over hours",
            "Garbage collection frequency increasing",
            "Response times gradually degrading",
            "Heap size approaching maximum"
        ],
        "database_outage": [
            "Connection pool utilization above 80%",
            "Slow query count increasing",
            "Database CPU trending upward",
            "Replication lag increasing"
        ],
        "connection_pool_exhaustion": [
            "Active connections trending toward max",
            "Connection wait time increasing",
            "Connection timeout errors appearing",
            "Query queue depth growing"
        ],
        "high_latency": [
            "P99 latency trending upward",
            "Upstream service response times increasing",
            "CPU utilization spikes",
            "Network timeout errors"
        ],
        "deployment_failure": [
            "Recent deployment activity",
            "Config changes in last 24h",
            "New error types in logs",
            "Health check failures starting"
        ],
        "kubernetes_crashloop": [
            "Pod restarts increasing",
            "OOMKilled events appearing",
            "Liveness probe failures",
            "Container startup errors"
        ],
        "api_timeout": [
            "Response time p99 increasing",
            "Upstream dependency latency",
            "Connection pool pressure",
            "Thread pool exhaustion signs"
        ]
    }

    return precursor_map.get(incident_type, [
        "Unusual metric patterns",
        "Error rate increasing",
        "Resource utilization trending up"
    ])


def get_typical_lead_time(incident_type: str) -> str:
    """Get typical lead time for precursor signals

    Args:
        incident_type: Type of incident

    Returns:
        Typical lead time string
    """
    lead_times = {
        "memory_leak": "2-6 hours",
        "database_outage": "30 minutes to 2 hours",
        "connection_pool_exhaustion": "1-3 hours",
        "high_latency": "15-45 minutes",
        "deployment_failure": "5-30 minutes",
        "kubernetes_crashloop": "10-30 minutes",
        "api_timeout": "15-60 minutes"
    }

    return lead_times.get(incident_type, "30 minutes to 2 hours")


def analyze_metric_threshold_patterns(incidents: List[Incident]) -> Dict[str, Any]:
    """Analyze metric values that preceded incidents

    Args:
        incidents: List of incidents

    Returns:
        Metric threshold patterns
    """
    # Analyze metrics from incidents to find thresholds
    cpu_values = []
    memory_values = []
    error_rates = []

    for incident in incidents:
        for metric in incident.metrics[:10]:  # First 10 metrics (near incident start)
            metrics_data = metric.metrics
            if "cpu_percent" in metrics_data:
                cpu_values.append(metrics_data["cpu_percent"])
            if "memory_mb" in metrics_data:
                memory_values.append(metrics_data["memory_mb"])
            if "error_rate" in metrics_data:
                error_rates.append(metrics_data["error_rate"])

    return {
        "cpu_threshold": {
            "warning": statistics.mean(cpu_values) * 0.8 if cpu_values else 70,
            "critical": statistics.mean(cpu_values) if cpu_values else 85,
            "observed_values": cpu_values[:5] if cpu_values else []
        },
        "memory_threshold": {
            "warning": statistics.mean(memory_values) * 0.85 if memory_values else 1500,
            "critical": statistics.mean(memory_values) if memory_values else 1800,
            "observed_values": memory_values[:5] if memory_values else []
        },
        "error_rate_threshold": {
            "warning": 0.02,  # 2%
            "critical": 0.05,  # 5%
            "observed_values": error_rates[:5] if error_rates else []
        }
    }


def calculate_incident_frequency(incidents: List[Incident]) -> Dict[str, Any]:
    """Calculate incident frequency metrics

    Args:
        incidents: List of incidents

    Returns:
        Frequency analysis including MTBF
    """
    if len(incidents) < 2:
        return {
            "mtbf_hours": 168,  # Default 1 week
            "incidents_per_week": len(incidents),
            "time_since_last_hours": 0
        }

    # Sort by start time
    sorted_incidents = sorted(
        incidents,
        key=lambda i: i.summary.start_time
    )

    # Calculate time between incidents
    intervals = []
    for i in range(1, len(sorted_incidents)):
        try:
            t1 = datetime.fromisoformat(sorted_incidents[i-1].summary.start_time.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(sorted_incidents[i].summary.start_time.replace('Z', '+00:00'))
            delta = (t2 - t1).total_seconds() / 3600  # Hours
            intervals.append(delta)
        except Exception:
            continue

    mtbf = statistics.mean(intervals) if intervals else 168

    # Time since last incident
    try:
        last_incident_time = datetime.fromisoformat(
            sorted_incidents[-1].summary.start_time.replace('Z', '+00:00')
        )
        time_since_last = (datetime.now(last_incident_time.tzinfo) - last_incident_time).total_seconds() / 3600
    except Exception:
        time_since_last = 0

    return {
        "mtbf_hours": round(mtbf, 1),
        "incidents_per_week": round(168 / mtbf, 1) if mtbf > 0 else 0,
        "time_since_last_hours": round(time_since_last, 1),
        "intervals_hours": intervals,
        "mtbf_status": "overdue" if time_since_last > mtbf else "within_normal"
    }


def identify_precursor_signals(incident: Incident) -> List[Dict[str, Any]]:
    """Identify what signals appeared before an incident

    Args:
        incident: Single incident to analyze

    Returns:
        List of precursor signals found
    """
    signals = []

    # Analyze early logs (first 20%)
    if incident.logs:
        early_logs = incident.logs[:max(1, len(incident.logs) // 5)]

        error_count = sum(1 for log in early_logs if log.level in ['ERROR', 'CRITICAL'])
        warning_count = sum(1 for log in early_logs if log.level == 'WARNING')

        if error_count > 0:
            signals.append({
                "signal": "Early error logs",
                "value": f"{error_count} errors in first 20% of incident",
                "lead_time_minutes": 0,
                "severity": "high"
            })

        if warning_count > 2:
            signals.append({
                "signal": "Warning log spike",
                "value": f"{warning_count} warnings before incident escalated",
                "lead_time_minutes": 5,
                "severity": "medium"
            })

    # Analyze early metrics (first 20%)
    if incident.metrics:
        early_metrics = incident.metrics[:max(1, len(incident.metrics) // 5)]

        for metric in early_metrics:
            data = metric.metrics

            if data.get("cpu_percent", 0) > 80:
                signals.append({
                    "signal": "High CPU usage",
                    "value": f"{data['cpu_percent']:.1f}%",
                    "lead_time_minutes": 10,
                    "severity": "medium"
                })
                break

            if data.get("memory_mb", 0) > 1800:
                signals.append({
                    "signal": "High memory usage",
                    "value": f"{data['memory_mb']:.0f}MB",
                    "lead_time_minutes": 15,
                    "severity": "medium"
                })
                break

            if data.get("error_rate", 0) > 0.02:
                signals.append({
                    "signal": "Elevated error rate",
                    "value": f"{data['error_rate']*100:.2f}%",
                    "lead_time_minutes": 5,
                    "severity": "high"
                })
                break

    # Add type-specific precursors
    type_precursors = get_type_specific_precursors(incident.summary.incident_type)
    for precursor in type_precursors[:2]:  # Add top 2
        signals.append({
            "signal": precursor,
            "value": "Pattern match",
            "lead_time_minutes": 30,
            "severity": "medium"
        })

    return signals
