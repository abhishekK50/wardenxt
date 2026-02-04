"""
Risk Calculator
Calculates current system risk score based on multiple factors
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from app.models.prediction import RiskScore, RiskTrendPoint
from app.models.incident import Incident
from app.core.pattern_analyzer import calculate_incident_frequency
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory storage for risk history
risk_history: List[RiskTrendPoint] = []
MAX_HISTORY_POINTS = 288  # 24 hours at 5-minute intervals


def calculate_current_risk(
    incidents: List[Incident],
    current_metrics: Optional[Dict[str, Any]] = None,
    anomaly_count: int = 0
) -> RiskScore:
    """Calculate current system risk score

    Args:
        incidents: Historical incidents for pattern analysis
        current_metrics: Current system metrics
        anomaly_count: Number of current anomalies

    Returns:
        RiskScore with contributing factors
    """
    try:
        factors = []

        # Factor 1: Time since last incident (MTBF analysis)
        mtbf_risk = calculate_mtbf_risk(incidents)
        factors.append({
            "name": "Time Since Last Incident",
            "weight": 0.15,
            "score": mtbf_risk["score"],
            "detail": mtbf_risk["detail"],
            "weighted_score": 0.15 * mtbf_risk["score"]
        })

        # Factor 2: Current metrics health
        metrics_risk = calculate_metrics_risk(current_metrics)
        factors.append({
            "name": "Current System Metrics",
            "weight": 0.25,
            "score": metrics_risk["score"],
            "detail": metrics_risk["detail"],
            "weighted_score": 0.25 * metrics_risk["score"]
        })

        # Factor 3: Recent deployments/changes
        deployment_risk = calculate_deployment_risk()
        factors.append({
            "name": "Recent Changes",
            "weight": 0.20,
            "score": deployment_risk["score"],
            "detail": deployment_risk["detail"],
            "weighted_score": 0.20 * deployment_risk["score"]
        })

        # Factor 4: Time of day risk
        temporal_risk = calculate_temporal_risk()
        factors.append({
            "name": "Time of Day",
            "weight": 0.10,
            "score": temporal_risk["score"],
            "detail": temporal_risk["detail"],
            "weighted_score": 0.10 * temporal_risk["score"]
        })

        # Factor 5: Anomaly count
        anomaly_risk_score = min(100, anomaly_count * 25)  # Each anomaly adds 25 points
        factors.append({
            "name": "Active Anomalies",
            "weight": 0.15,
            "score": anomaly_risk_score,
            "detail": f"{anomaly_count} anomalies detected",
            "weighted_score": 0.15 * anomaly_risk_score
        })

        # Factor 6: Historical pattern match
        pattern_risk = calculate_pattern_risk(incidents)
        factors.append({
            "name": "Historical Patterns",
            "weight": 0.15,
            "score": pattern_risk["score"],
            "detail": pattern_risk["detail"],
            "weighted_score": 0.15 * pattern_risk["score"]
        })

        # Calculate total weighted score
        total_score = int(sum(f["weighted_score"] for f in factors))
        total_score = min(100, max(0, total_score))  # Clamp 0-100

        # Determine level
        if total_score <= 25:
            level = "low"
        elif total_score <= 50:
            level = "medium"
        elif total_score <= 75:
            level = "high"
        else:
            level = "critical"

        # Calculate trend
        trend_data = calculate_trend()

        # Store in history
        store_risk_point(total_score, level)

        risk_score = RiskScore(
            score=total_score,
            level=level,
            calculated_at=datetime.utcnow().isoformat(),
            contributing_factors=factors,
            trend=trend_data["direction"],
            trend_percentage=trend_data["percentage"],
            forecast_change=trend_data["forecast"]
        )

        logger.info(
            "risk_score_calculated",
            extra_fields={
                "score": total_score,
                "level": level,
                "factors_count": len(factors)
            }
        )

        return risk_score

    except Exception as e:
        logger.error(f"Error calculating risk: {e}", exc_info=True)
        # Return default moderate risk
        return RiskScore(
            score=50,
            level="medium",
            calculated_at=datetime.utcnow().isoformat(),
            contributing_factors=[],
            trend="stable",
            trend_percentage=0.0,
            forecast_change="Unable to calculate forecast"
        )


def calculate_mtbf_risk(incidents: List[Incident]) -> Dict[str, Any]:
    """Calculate risk based on mean time between failures

    Args:
        incidents: Historical incidents

    Returns:
        Risk score and detail
    """
    if not incidents:
        return {"score": 30, "detail": "No historical incidents to analyze"}

    frequency = calculate_incident_frequency(incidents)
    mtbf = frequency.get("mtbf_hours", 168)
    time_since_last = frequency.get("time_since_last_hours", 0)

    # If we're past MTBF, risk increases
    if time_since_last > mtbf:
        # Overdue - higher risk
        overdue_ratio = time_since_last / mtbf
        score = min(100, int(50 + (overdue_ratio - 1) * 30))
        detail = f"Overdue for incident (MTBF: {mtbf:.0f}h, time since last: {time_since_last:.0f}h)"
    elif time_since_last > mtbf * 0.7:
        # Approaching MTBF
        score = 50
        detail = f"Approaching typical incident interval ({time_since_last:.0f}h of {mtbf:.0f}h MTBF)"
    else:
        # Within normal range
        score = int(20 + (time_since_last / mtbf) * 30)
        detail = f"Within normal interval ({time_since_last:.0f}h of {mtbf:.0f}h MTBF)"

    return {"score": score, "detail": detail}


def calculate_metrics_risk(metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate risk based on current system metrics

    Args:
        metrics: Current metric values

    Returns:
        Risk score and detail
    """
    if not metrics:
        # Simulate metrics for demo
        metrics = generate_simulated_metrics()

    issues = []
    score = 0

    # CPU risk
    cpu = metrics.get("cpu_percent", 50)
    if cpu > 85:
        score += 35
        issues.append(f"CPU critical at {cpu:.1f}%")
    elif cpu > 70:
        score += 20
        issues.append(f"CPU elevated at {cpu:.1f}%")
    elif cpu > 50:
        score += 10

    # Memory risk
    memory = metrics.get("memory_percent", 60)
    if memory > 85:
        score += 35
        issues.append(f"Memory critical at {memory:.1f}%")
    elif memory > 75:
        score += 20
        issues.append(f"Memory elevated at {memory:.1f}%")
    elif memory > 60:
        score += 10

    # Error rate risk
    error_rate = metrics.get("error_rate", 0.005)
    if error_rate > 0.05:
        score += 30
        issues.append(f"Error rate critical at {error_rate*100:.2f}%")
    elif error_rate > 0.02:
        score += 15
        issues.append(f"Error rate elevated at {error_rate*100:.2f}%")
    elif error_rate > 0.01:
        score += 5

    detail = "; ".join(issues) if issues else "All metrics within normal range"

    return {"score": min(100, score), "detail": detail}


def calculate_deployment_risk() -> Dict[str, Any]:
    """Calculate risk based on recent deployments

    Returns:
        Risk score and detail
    """
    # Simulate deployment activity for demo
    # In production, would integrate with CI/CD system

    hours_since_deploy = random.randint(12, 72)

    if hours_since_deploy < 2:
        score = 80
        detail = "Deployment within last 2 hours - high change risk"
    elif hours_since_deploy < 6:
        score = 60
        detail = "Recent deployment (< 6h) - elevated change risk"
    elif hours_since_deploy < 24:
        score = 40
        detail = "Deployment within last 24h - moderate change risk"
    elif hours_since_deploy < 48:
        score = 20
        detail = "Deployment 1-2 days ago - low change risk"
    else:
        score = 10
        detail = "No recent deployments - minimal change risk"

    return {"score": score, "detail": detail}


def calculate_temporal_risk() -> Dict[str, Any]:
    """Calculate risk based on time of day

    Returns:
        Risk score and detail
    """
    current_hour = datetime.now().hour
    day_of_week = datetime.now().weekday()  # 0=Monday

    # Peak hours (9 AM - 6 PM weekdays) have higher risk due to traffic
    if day_of_week < 5:  # Weekday
        if 9 <= current_hour <= 18:
            score = 60
            detail = "Peak business hours - higher traffic risk"
        elif 6 <= current_hour <= 9 or 18 <= current_hour <= 21:
            score = 40
            detail = "Transition hours - moderate traffic"
        else:
            score = 20
            detail = "Off-peak hours - lower traffic risk"
    else:  # Weekend
        if 10 <= current_hour <= 20:
            score = 35
            detail = "Weekend daytime - moderate traffic"
        else:
            score = 15
            detail = "Weekend off-peak - low traffic risk"

    return {"score": score, "detail": detail}


def calculate_pattern_risk(incidents: List[Incident]) -> Dict[str, Any]:
    """Calculate risk based on historical pattern matching

    Args:
        incidents: Historical incidents

    Returns:
        Risk score and detail
    """
    if not incidents:
        return {"score": 30, "detail": "Insufficient historical data"}

    # Check for patterns that match current conditions
    current_hour = datetime.now().hour

    # Count incidents at similar time
    similar_time_incidents = 0
    for incident in incidents:
        try:
            inc_time = datetime.fromisoformat(incident.summary.start_time.replace('Z', '+00:00'))
            if abs(inc_time.hour - current_hour) <= 2:
                similar_time_incidents += 1
        except Exception:
            continue

    if similar_time_incidents >= 3:
        score = 70
        detail = f"High incident frequency at this time ({similar_time_incidents} historical)"
    elif similar_time_incidents >= 2:
        score = 50
        detail = f"Some incidents historically at this time ({similar_time_incidents})"
    elif similar_time_incidents == 1:
        score = 30
        detail = "One historical incident at similar time"
    else:
        score = 15
        detail = "No pattern match at current time"

    return {"score": score, "detail": detail}


def calculate_trend() -> Dict[str, Any]:
    """Calculate risk trend from history

    Returns:
        Trend direction and percentage
    """
    if len(risk_history) < 12:  # Need at least 1 hour of data
        return {
            "direction": "stable",
            "percentage": 0.0,
            "forecast": "Insufficient data for trend"
        }

    # Compare last hour to previous hour
    recent = [p.score for p in risk_history[-12:]]  # Last hour
    previous = [p.score for p in risk_history[-24:-12]]  # Previous hour

    if not previous:
        return {
            "direction": "stable",
            "percentage": 0.0,
            "forecast": "Building trend data"
        }

    recent_avg = sum(recent) / len(recent)
    previous_avg = sum(previous) / len(previous)

    if previous_avg > 0:
        change_pct = ((recent_avg - previous_avg) / previous_avg) * 100
    else:
        change_pct = 0

    if change_pct > 10:
        direction = "increasing"
        forecast = f"+{change_pct:.0f}% if trend continues"
    elif change_pct < -10:
        direction = "decreasing"
        forecast = f"{change_pct:.0f}% if trend continues"
    else:
        direction = "stable"
        forecast = "Risk level stable"

    return {
        "direction": direction,
        "percentage": round(change_pct, 1),
        "forecast": forecast
    }


def store_risk_point(score: int, level: str):
    """Store risk score in history

    Args:
        score: Current risk score
        level: Current risk level
    """
    global risk_history

    point = RiskTrendPoint(
        timestamp=datetime.utcnow().isoformat(),
        score=score,
        level=level,
        incident_occurred=False
    )

    risk_history.append(point)

    # Trim to max size
    if len(risk_history) > MAX_HISTORY_POINTS:
        risk_history = risk_history[-MAX_HISTORY_POINTS:]


def get_risk_history(hours: int = 24) -> List[Dict[str, Any]]:
    """Get risk history for specified hours

    Args:
        hours: Number of hours to retrieve

    Returns:
        List of risk trend points
    """
    points_needed = hours * 12  # 5-minute intervals
    history = risk_history[-points_needed:] if risk_history else []

    return [p.dict() for p in history]


def calculate_service_risk(
    service_name: str,
    incidents: List[Incident]
) -> Dict[str, Any]:
    """Calculate risk for a specific service

    Args:
        service_name: Name of service
        incidents: Historical incidents

    Returns:
        Service-specific risk assessment
    """
    # Find incidents affecting this service
    service_incidents = [
        inc for inc in incidents
        if service_name in inc.summary.services_affected
    ]

    if not service_incidents:
        return {
            "service": service_name,
            "risk_score": 20,
            "risk_level": "low",
            "incident_count": 0,
            "detail": "No historical incidents for this service"
        }

    # Calculate service-specific metrics
    incident_count = len(service_incidents)
    severities = [inc.summary.severity for inc in service_incidents]
    p0_p1_count = sum(1 for s in severities if s in ["P0", "P1"])

    # Base score on incident count and severity
    score = min(100, incident_count * 15 + p0_p1_count * 20)

    if score <= 25:
        level = "low"
    elif score <= 50:
        level = "medium"
    elif score <= 75:
        level = "high"
    else:
        level = "critical"

    return {
        "service": service_name,
        "risk_score": score,
        "risk_level": level,
        "incident_count": incident_count,
        "p0_p1_count": p0_p1_count,
        "detail": f"{incident_count} incidents ({p0_p1_count} critical/high)"
    }


def generate_simulated_metrics() -> Dict[str, Any]:
    """Generate simulated current metrics for demo

    Returns:
        Simulated metric values
    """
    # Generate realistic-looking metrics with some variance
    base_cpu = 55 + random.randint(-10, 25)
    base_memory = 65 + random.randint(-10, 20)
    base_error = 0.005 + random.random() * 0.02

    return {
        "cpu_percent": min(95, base_cpu),
        "memory_percent": min(95, base_memory),
        "error_rate": min(0.1, base_error),
        "requests_per_second": 500 + random.randint(-100, 200),
        "latency_p99_ms": 150 + random.randint(-50, 100)
    }
