"""
Gemini Predictor
Uses Gemini AI for intelligent incident prediction and scenario simulation
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.incident import Incident
from app.models.prediction import (
    IncidentPrediction,
    PreventiveRecommendation,
    SimulationResult,
    PredictionForecast
)
from app.core.agent.gemini_client import get_gemini_client
from app.core.pattern_analyzer import (
    analyze_incident_patterns,
    calculate_incident_frequency
)
from app.core.risk_calculator import generate_simulated_metrics
from app.core.logging import get_logger

logger = get_logger(__name__)

# Cache for predictions
predictions_cache: Dict[str, List[IncidentPrediction]] = {}
CACHE_TTL_MINUTES = 15


async def predict_incidents(
    incidents: List[Incident],
    time_horizon: str = "24h"
) -> PredictionForecast:
    """Predict likely incidents using Gemini AI

    Args:
        incidents: Historical incidents for pattern analysis
        time_horizon: Prediction window (24h, 48h, 72h)

    Returns:
        PredictionForecast with incident predictions
    """
    try:
        logger.info(
            "prediction_started",
            extra_fields={"time_horizon": time_horizon, "incidents_count": len(incidents)}
        )

        # Check cache
        cache_key = f"{time_horizon}_{len(incidents)}"
        if cache_key in predictions_cache:
            cached = predictions_cache[cache_key]
            logger.info("prediction_cache_hit", extra_fields={"cache_key": cache_key})
            return PredictionForecast(
                generated_at=datetime.utcnow().isoformat(),
                time_horizon=time_horizon,
                predictions=cached,
                overall_risk="medium",
                summary="Retrieved from cache"
            )

        # Build comprehensive context for Gemini
        context = build_prediction_context(incidents, time_horizon)

        # Generate prediction prompt
        prompt = build_prediction_prompt(context, time_horizon)

        # Call Gemini
        gemini_client = get_gemini_client()
        response = await gemini_client.generate_content_async(prompt)
        response_text = response.text.strip()

        # Parse predictions
        predictions = parse_predictions(response_text, time_horizon)

        # Cache predictions
        predictions_cache[cache_key] = predictions

        # Determine overall risk
        if predictions:
            max_prob = max(p.probability for p in predictions)
            if max_prob > 75:
                overall_risk = "high"
            elif max_prob > 50:
                overall_risk = "medium"
            elif max_prob > 25:
                overall_risk = "low"
            else:
                overall_risk = "minimal"
        else:
            overall_risk = "low"

        # Generate summary
        summary = generate_prediction_summary(predictions, time_horizon)

        logger.info(
            "prediction_completed",
            extra_fields={
                "predictions_count": len(predictions),
                "overall_risk": overall_risk
            }
        )

        return PredictionForecast(
            generated_at=datetime.utcnow().isoformat(),
            time_horizon=time_horizon,
            predictions=predictions,
            overall_risk=overall_risk,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        # Return empty forecast on error
        return PredictionForecast(
            generated_at=datetime.utcnow().isoformat(),
            time_horizon=time_horizon,
            predictions=[],
            overall_risk="unknown",
            summary=f"Prediction failed: {str(e)}"
        )


def build_prediction_context(
    incidents: List[Incident],
    time_horizon: str
) -> Dict[str, Any]:
    """Build context for prediction prompt

    Args:
        incidents: Historical incidents
        time_horizon: Prediction window

    Returns:
        Context dictionary
    """
    # Analyze patterns
    patterns = analyze_incident_patterns(incidents)
    frequency = calculate_incident_frequency(incidents)

    # Get current metrics (simulated for demo)
    current_metrics = generate_simulated_metrics()

    # Time context
    now = datetime.now()
    time_period = "morning" if now.hour < 12 else "afternoon" if now.hour < 17 else "evening" if now.hour < 21 else "night"

    # Build incident summaries
    incident_summaries = []
    for inc in incidents:
        incident_summaries.append({
            "incident_id": inc.summary.incident_id,
            "type": inc.summary.incident_type,
            "severity": inc.summary.severity,
            "start_time": inc.summary.start_time,
            "duration_minutes": inc.summary.duration_minutes,
            "root_cause": inc.summary.root_cause.primary,
            "services": inc.summary.services_affected
        })

    return {
        "incidents": incident_summaries,
        "patterns": patterns,
        "frequency": frequency,
        "current_metrics": current_metrics,
        "current_time": now.isoformat(),
        "day_of_week": now.strftime('%A'),
        "hour": now.hour,
        "time_period": time_period,
        "time_horizon": time_horizon
    }


def build_prediction_prompt(context: Dict[str, Any], time_horizon: str) -> str:
    """Build comprehensive prediction prompt for Gemini

    Args:
        context: Context dictionary with all relevant data
        time_horizon: Prediction window

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are an expert SRE analyzing system patterns to predict future incidents.

## HISTORICAL INCIDENT DATA
{json.dumps(context["incidents"], indent=2)}

## CURRENT SYSTEM STATE
- Current time: {context["current_time"]}
- Day of week: {context["day_of_week"]}
- Time of day: {context["hour"]}:00 ({context["time_period"]})

## CURRENT METRICS (Last 30 minutes average)
- CPU: {context["current_metrics"]["cpu_percent"]:.1f}%
- Memory: {context["current_metrics"]["memory_percent"]:.1f}%
- Error Rate: {context["current_metrics"]["error_rate"]*100:.2f}%
- Requests/sec: {context["current_metrics"]["requests_per_second"]}
- Latency P99: {context["current_metrics"]["latency_p99_ms"]}ms

## PATTERN ANALYSIS
- Mean Time Between Failures: {context["frequency"].get("mtbf_hours", "N/A")} hours
- Time since last incident: {context["frequency"].get("time_since_last_hours", "N/A")} hours
- Peak incident hour: {context["patterns"].get("temporal_analysis", {}).get("peak_hour", "N/A")}

## TASK
Predict likelihood of incidents in the next {time_horizon}.

Consider:
1. Historical patterns (when do incidents typically occur?)
2. Current metric trends (are resources trending toward thresholds?)
3. Time-based factors (peak hours, maintenance windows)
4. Correlated failures (if X happened before, what usually follows?)
5. MTBF analysis (are we overdue for an incident?)

For EACH potential incident (0-3 predictions based on actual risk), provide:
- Incident type (be specific: memory_leak, database_outage, high_latency, etc.)
- Probability (0-100, be realistic and conservative)
- Confidence in prediction (0-100)
- Predicted severity (P0/P1/P2)
- Time window (e.g., "next 6-12 hours")
- Likely affected services
- Warning signs to watch for
- Your reasoning (detailed explanation)
- Recommended preventive actions

OUTPUT FORMAT: Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "predicted_incident_type": "memory_leak",
    "probability": 72,
    "confidence": 85,
    "predicted_severity": "P1",
    "time_window": "next 18-24 hours",
    "likely_services": ["api-service", "worker-service"],
    "warning_signs": [
      "Memory usage trending upward",
      "GC frequency increasing",
      "Response time degradation"
    ],
    "reasoning": "Detailed explanation of why this incident is predicted...",
    "recommended_actions": [
      "Monitor memory closely",
      "Prepare rollback plan",
      "Schedule proactive restart"
    ]
  }}
]

Be realistic - if risk is genuinely low, return an empty array [].
Provide 0-3 predictions based on actual risk assessment.
"""
    return prompt


def parse_predictions(response_text: str, time_horizon: str) -> List[IncidentPrediction]:
    """Parse Gemini response into IncidentPrediction objects

    Args:
        response_text: Raw response from Gemini
        time_horizon: Prediction window

    Returns:
        List of parsed predictions
    """
    try:
        # Try to parse JSON directly
        predictions_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            try:
                predictions_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Could not parse predictions from Gemini response")
                return []
        else:
            logger.warning("No JSON array found in Gemini response")
            return []

    predictions = []
    for data in predictions_data:
        try:
            prediction = IncidentPrediction(
                prediction_id=f"PRED-{uuid.uuid4().hex[:8].upper()}",
                predicted_at=datetime.utcnow().isoformat(),
                time_horizon=time_horizon,
                probability=data.get("probability", 50),
                confidence=data.get("confidence", 70),
                predicted_incident_type=data.get("predicted_incident_type", "unknown"),
                predicted_severity=data.get("predicted_severity", "P2"),
                time_window=data.get("time_window", f"next {time_horizon}"),
                likely_services=data.get("likely_services", []),
                warning_signs=data.get("warning_signs", []),
                recommended_actions=data.get("recommended_actions", []),
                reasoning=data.get("reasoning", "")
            )
            predictions.append(prediction)
        except Exception as e:
            logger.warning(f"Could not parse prediction: {e}")
            continue

    return predictions


def generate_prediction_summary(
    predictions: List[IncidentPrediction],
    time_horizon: str
) -> str:
    """Generate natural language summary of predictions

    Args:
        predictions: List of predictions
        time_horizon: Prediction window

    Returns:
        Summary string
    """
    if not predictions:
        return f"No significant incidents predicted in the next {time_horizon}. System appears stable."

    high_risk = [p for p in predictions if p.probability > 70]
    medium_risk = [p for p in predictions if 40 <= p.probability <= 70]

    summary_parts = []

    if high_risk:
        types = [p.predicted_incident_type.replace("_", " ") for p in high_risk]
        summary_parts.append(f"⚠️ High risk: {', '.join(types)} ({high_risk[0].probability}% likely)")

    if medium_risk:
        types = [p.predicted_incident_type.replace("_", " ") for p in medium_risk]
        summary_parts.append(f"⚡ Moderate risk: {', '.join(types)}")

    if not summary_parts:
        return f"Low risk period expected in the next {time_horizon}."

    return " | ".join(summary_parts)


async def generate_preventive_recommendations(
    predictions: List[IncidentPrediction],
    incidents: List[Incident]
) -> List[PreventiveRecommendation]:
    """Generate preventive recommendations based on predictions

    Args:
        predictions: Current predictions
        incidents: Historical incidents for context

    Returns:
        List of preventive recommendations
    """
    recommendations = []

    for prediction in predictions:
        if prediction.probability < 30:
            continue  # Skip low probability predictions

        # Generate recommendations based on prediction
        priority = "urgent" if prediction.probability > 75 else "high" if prediction.probability > 50 else "medium"

        # Get type-specific recommendations
        type_recs = get_type_specific_recommendations(prediction.predicted_incident_type)

        for rec in type_recs[:2]:  # Top 2 recommendations per prediction
            recommendations.append(PreventiveRecommendation(
                recommendation_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
                priority=priority,
                title=rec["title"],
                description=rec["description"],
                estimated_impact=f"Reduces {prediction.predicted_incident_type.replace('_', ' ')} risk by {rec['impact']}%",
                implementation_effort=rec["effort"],
                commands=rec["commands"],
                related_prediction_id=prediction.prediction_id,
                status="pending"
            ))

    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

    return recommendations[:5]  # Return top 5


def get_type_specific_recommendations(incident_type: str) -> List[Dict[str, Any]]:
    """Get recommendations specific to incident type

    Args:
        incident_type: Type of predicted incident

    Returns:
        List of recommendation dictionaries
    """
    recommendations_map = {
        "memory_leak": [
            {
                "title": "Schedule proactive service restart",
                "description": "Restart service during low-traffic window to reset memory state",
                "impact": 45,
                "effort": "5 minutes",
                "commands": ["kubectl rollout restart deployment/api-service -n production"]
            },
            {
                "title": "Enable heap dump collection",
                "description": "Configure heap dumps to capture memory state for analysis",
                "impact": 20,
                "effort": "10 minutes",
                "commands": ["kubectl set env deployment/api-service JAVA_OPTS=-XX:+HeapDumpOnOutOfMemoryError"]
            }
        ],
        "database_outage": [
            {
                "title": "Optimize slow queries",
                "description": "Review and optimize queries taking >1s",
                "impact": 40,
                "effort": "30 minutes",
                "commands": ["psql -c \"SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '1 second'\""]
            },
            {
                "title": "Increase connection pool size",
                "description": "Temporarily increase pool to handle higher load",
                "impact": 30,
                "effort": "5 minutes",
                "commands": ["kubectl set env deployment/api-service DB_POOL_SIZE=150"]
            }
        ],
        "high_latency": [
            {
                "title": "Scale horizontally",
                "description": "Add additional pods to distribute load",
                "impact": 50,
                "effort": "2 minutes",
                "commands": ["kubectl scale deployment/api-service --replicas=5 -n production"]
            },
            {
                "title": "Enable response caching",
                "description": "Configure caching for frequently accessed endpoints",
                "impact": 35,
                "effort": "15 minutes",
                "commands": ["kubectl apply -f cache-config.yaml"]
            }
        ],
        "connection_pool_exhaustion": [
            {
                "title": "Scale down non-critical services",
                "description": "Reduce connection usage from background workers",
                "impact": 40,
                "effort": "5 minutes",
                "commands": ["kubectl scale deployment/worker-service --replicas=2"]
            },
            {
                "title": "Implement connection pooler",
                "description": "Add PgBouncer to manage database connections",
                "impact": 60,
                "effort": "45 minutes",
                "commands": ["helm install pgbouncer charts/pgbouncer"]
            }
        ]
    }

    return recommendations_map.get(incident_type, [
        {
            "title": "Increase monitoring alerting",
            "description": "Lower alert thresholds to catch issues earlier",
            "impact": 25,
            "effort": "10 minutes",
            "commands": ["kubectl apply -f alert-rules-strict.yaml"]
        },
        {
            "title": "Review recent changes",
            "description": "Audit recent deployments and config changes",
            "impact": 30,
            "effort": "15 minutes",
            "commands": ["git log --oneline -20", "kubectl rollout history deployment/api-service"]
        }
    ])


async def simulate_scenario(
    scenario: str,
    time_horizon: str,
    incidents: List[Incident],
    current_risk: int
) -> SimulationResult:
    """Simulate a what-if scenario using Gemini

    Args:
        scenario: Scenario description
        time_horizon: Time horizon for simulation
        incidents: Historical incidents
        current_risk: Current risk score

    Returns:
        SimulationResult with outcome analysis
    """
    try:
        logger.info("simulation_started", extra_fields={"scenario": scenario})

        prompt = f"""You are an expert SRE analyzing a "what-if" scenario.

CURRENT SITUATION:
- Current risk score: {current_risk}/100
- Historical incidents: {len(incidents)}
- Time horizon: {time_horizon}

SCENARIO TO ANALYZE:
"{scenario}"

Analyze this scenario and predict:
1. What would likely happen if this action is taken?
2. How would it affect incident probability?
3. What are the risks and benefits?

OUTPUT FORMAT: Return ONLY valid JSON (no markdown):
{{
  "predicted_outcome": "Description of what would happen",
  "incident_probability_change": -25,
  "impact_assessment": "Brief assessment of overall impact",
  "recommendation": "proceed" or "caution" or "avoid",
  "risks": ["risk 1", "risk 2"],
  "benefits": ["benefit 1", "benefit 2"]
}}
"""

        gemini_client = get_gemini_client()
        response = await gemini_client.generate_content_async(prompt)
        response_text = response.text.strip()

        # Parse response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse simulation result")

        prob_change = data.get("incident_probability_change", 0)
        prob_before = min(100, current_risk + 20)  # Estimate current probability
        prob_after = max(0, min(100, prob_before + prob_change))

        result = SimulationResult(
            scenario=scenario,
            simulated_at=datetime.utcnow().isoformat(),
            time_horizon=time_horizon,
            predicted_outcome=data.get("predicted_outcome", ""),
            incident_probability_before=prob_before,
            incident_probability_after=prob_after,
            probability_change=prob_change,
            impact_assessment=data.get("impact_assessment", ""),
            recommendation=data.get("recommendation", "caution"),
            risks=data.get("risks", []),
            benefits=data.get("benefits", [])
        )

        logger.info("simulation_completed", extra_fields={"recommendation": result.recommendation})

        return result

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return SimulationResult(
            scenario=scenario,
            simulated_at=datetime.utcnow().isoformat(),
            time_horizon=time_horizon,
            predicted_outcome=f"Simulation failed: {str(e)}",
            incident_probability_before=50,
            incident_probability_after=50,
            probability_change=0,
            impact_assessment="Unable to assess",
            recommendation="caution",
            risks=["Simulation failed - proceed with caution"],
            benefits=[]
        )
