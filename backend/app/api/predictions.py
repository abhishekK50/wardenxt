"""
Predictions API Router
Endpoints for predictive analytics and incident forecasting
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.models.prediction import (
    PredictionForecast,
    RiskScore,
    Anomaly,
    PreventiveRecommendation,
    SimulationRequest,
    SimulationResult,
    PredictionAccuracy,
    HistoricalPattern
)
from app.core.data_loader import DataLoader
from app.core.pattern_analyzer import analyze_incident_patterns, calculate_incident_frequency
from app.core.risk_calculator import (
    calculate_current_risk,
    get_risk_history,
    calculate_service_risk
)
from app.core.anomaly_detector import (
    detect_metric_anomalies,
    detect_log_anomalies,
    detect_simulated_anomalies,
    get_current_anomalies,
    clear_anomaly
)
from app.core.gemini_predictor import (
    predict_incidents,
    generate_preventive_recommendations,
    simulate_scenario
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

# In-memory storage for accuracy tracking
prediction_outcomes: Dict[str, Dict] = {}  # prediction_id -> outcome


def get_data_loader():
    """Dependency injection for data loader"""
    return DataLoader()


def get_all_incidents(data_loader: DataLoader):
    """Load all incidents from data loader and webhooks"""
    incidents = []

    # Load file-based incidents
    try:
        incident_ids = data_loader.list_incidents()
        for inc_id in incident_ids:
            try:
                incident = data_loader.load_incident(inc_id)
                incidents.append(incident)
            except Exception:
                continue
    except Exception:
        pass

    # Load webhook incidents
    try:
        from app.api.webhooks import webhook_incident_data
        for incident in webhook_incident_data.values():
            incidents.append(incident)
    except ImportError:
        pass

    return incidents


@router.get("/forecast", response_model=PredictionForecast)
async def get_incident_forecast(
    time_horizon: str = Query(default="24h", pattern="^(24h|48h|72h)$"),
    data_loader: DataLoader = Depends(get_data_loader)
):
    """Get incident predictions for specified time horizon

    Args:
        time_horizon: Prediction window (24h, 48h, or 72h)
        data_loader: Data loader dependency

    Returns:
        PredictionForecast with incident predictions
    """
    try:
        logger.info("forecast_requested", extra_fields={"time_horizon": time_horizon})

        # Load all incidents
        incidents = get_all_incidents(data_loader)

        # Generate predictions
        forecast = await predict_incidents(incidents, time_horizon)

        return forecast

    except Exception as e:
        logger.error(f"Forecast failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )


@router.get("/risk-score", response_model=RiskScore)
async def get_risk_score(data_loader: DataLoader = Depends(get_data_loader)):
    """Get current system risk score

    Returns:
        RiskScore with contributing factors and trend
    """
    try:
        logger.info("risk_score_requested")

        # Load incidents for analysis
        incidents = get_all_incidents(data_loader)

        # Get current anomalies
        anomalies = get_current_anomalies()

        # Calculate risk score
        risk_score = calculate_current_risk(
            incidents=incidents,
            current_metrics=None,  # Will use simulated
            anomaly_count=len(anomalies)
        )

        return risk_score

    except Exception as e:
        logger.error(f"Risk score failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate risk score: {str(e)}"
        )


@router.get("/anomalies", response_model=Dict)
async def get_anomalies():
    """Get current system anomalies

    Returns:
        Dictionary with anomalies list and stats
    """
    try:
        logger.info("anomalies_requested")

        # Detect new anomalies (includes simulated for demo)
        new_anomalies = detect_simulated_anomalies()

        # Get all current anomalies
        all_anomalies = get_current_anomalies()

        # Group by severity
        by_severity = {
            "severe": [a for a in all_anomalies if a.severity == "severe"],
            "moderate": [a for a in all_anomalies if a.severity == "moderate"],
            "minor": [a for a in all_anomalies if a.severity == "minor"]
        }

        return {
            "total_count": len(all_anomalies),
            "anomalies": [a.dict() for a in all_anomalies],
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "detected_at": all_anomalies[0].detected_at if all_anomalies else None
        }

    except Exception as e:
        logger.error(f"Anomalies fetch failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch anomalies: {str(e)}"
        )


@router.delete("/anomalies/{anomaly_id}", response_model=Dict)
async def dismiss_anomaly(anomaly_id: str):
    """Dismiss/clear an anomaly

    Args:
        anomaly_id: ID of anomaly to dismiss

    Returns:
        Success message
    """
    try:
        cleared = clear_anomaly(anomaly_id)

        if cleared:
            return {"success": True, "message": f"Anomaly {anomaly_id} dismissed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anomaly {anomaly_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dismiss anomaly failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss anomaly: {str(e)}"
        )


@router.get("/recommendations", response_model=Dict)
async def get_recommendations(data_loader: DataLoader = Depends(get_data_loader)):
    """Get preventive action recommendations

    Returns:
        Dictionary with prioritized recommendations
    """
    try:
        logger.info("recommendations_requested")

        # Load incidents
        incidents = get_all_incidents(data_loader)

        # Get current predictions
        forecast = await predict_incidents(incidents, "24h")

        # Generate recommendations
        recommendations = await generate_preventive_recommendations(
            forecast.predictions,
            incidents
        )

        # Group by priority
        by_priority = {
            "urgent": [r for r in recommendations if r.priority == "urgent"],
            "high": [r for r in recommendations if r.priority == "high"],
            "medium": [r for r in recommendations if r.priority == "medium"],
            "low": [r for r in recommendations if r.priority == "low"]
        }

        return {
            "total_count": len(recommendations),
            "recommendations": [r.dict() for r in recommendations],
            "by_priority": {k: len(v) for k, v in by_priority.items()},
            "generated_at": forecast.generated_at
        }

    except Exception as e:
        logger.error(f"Recommendations failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/simulate", response_model=SimulationResult)
async def simulate_what_if(
    request: SimulationRequest,
    data_loader: DataLoader = Depends(get_data_loader)
):
    """Simulate a what-if scenario

    Args:
        request: Simulation request with scenario and time horizon

    Returns:
        SimulationResult with outcome analysis
    """
    try:
        logger.info("simulation_requested", extra_fields={"scenario": request.scenario})

        # Load incidents
        incidents = get_all_incidents(data_loader)

        # Get current risk
        risk_score = calculate_current_risk(incidents, None, 0)

        # Run simulation
        result = await simulate_scenario(
            scenario=request.scenario,
            time_horizon=request.time_horizon,
            incidents=incidents,
            current_risk=risk_score.score
        )

        return result

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to simulate scenario: {str(e)}"
        )


@router.get("/accuracy", response_model=PredictionAccuracy)
async def get_prediction_accuracy():
    """Get prediction accuracy metrics

    Returns:
        PredictionAccuracy with precision, recall, F1 score
    """
    try:
        # Calculate accuracy from stored outcomes
        total = len(prediction_outcomes)

        if total == 0:
            return PredictionAccuracy(
                period="all_time",
                total_predictions=0,
                true_positives=0,
                false_positives=0,
                false_negatives=0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                average_lead_time=0.0
            )

        tp = sum(1 for o in prediction_outcomes.values() if o.get("true_positive", False))
        fp = sum(1 for o in prediction_outcomes.values() if o.get("false_positive", False))
        fn = sum(1 for o in prediction_outcomes.values() if o.get("false_negative", False))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Calculate average lead time for true positives
        lead_times = [o.get("lead_time_hours", 0) for o in prediction_outcomes.values() if o.get("true_positive")]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0

        return PredictionAccuracy(
            period="all_time",
            total_predictions=total,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1, 3),
            average_lead_time=round(avg_lead_time, 1)
        )

    except Exception as e:
        logger.error(f"Accuracy calculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate accuracy: {str(e)}"
        )


@router.get("/historical-patterns", response_model=Dict)
async def get_historical_patterns(data_loader: DataLoader = Depends(get_data_loader)):
    """Get analyzed historical patterns

    Returns:
        Dictionary with pattern analysis results
    """
    try:
        logger.info("historical_patterns_requested")

        # Load incidents
        incidents = get_all_incidents(data_loader)

        # Analyze patterns
        patterns = analyze_incident_patterns(incidents)
        frequency = calculate_incident_frequency(incidents)

        return {
            "patterns": patterns.get("patterns", []),
            "temporal_analysis": patterns.get("temporal_analysis", {}),
            "service_correlations": patterns.get("service_correlations", []),
            "metric_thresholds": patterns.get("metric_thresholds", {}),
            "frequency": frequency,
            "analyzed_incidents": len(incidents)
        }

    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze patterns: {str(e)}"
        )


@router.get("/risk-history", response_model=Dict)
async def get_risk_history_endpoint(hours: int = Query(default=24, ge=1, le=72)):
    """Get risk score history

    Args:
        hours: Number of hours to retrieve

    Returns:
        Dictionary with risk history points
    """
    try:
        history = get_risk_history(hours)

        return {
            "hours": hours,
            "data_points": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Risk history failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch risk history: {str(e)}"
        )


@router.get("/service-risk/{service_name}", response_model=Dict)
async def get_service_risk(
    service_name: str,
    data_loader: DataLoader = Depends(get_data_loader)
):
    """Get risk assessment for a specific service

    Args:
        service_name: Name of service to assess

    Returns:
        Service-specific risk assessment
    """
    try:
        incidents = get_all_incidents(data_loader)
        risk = calculate_service_risk(service_name, incidents)

        return risk

    except Exception as e:
        logger.error(f"Service risk failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate service risk: {str(e)}"
        )


@router.post("/record-outcome", response_model=Dict)
async def record_prediction_outcome(
    prediction_id: str,
    incident_occurred: bool,
    incident_id: Optional[str] = None,
    lead_time_hours: Optional[float] = None
):
    """Record actual outcome for a prediction (for accuracy tracking)

    Args:
        prediction_id: ID of the prediction
        incident_occurred: Whether the predicted incident occurred
        incident_id: ID of incident if it occurred
        lead_time_hours: Hours of warning before incident

    Returns:
        Confirmation
    """
    try:
        prediction_outcomes[prediction_id] = {
            "true_positive": incident_occurred,
            "false_positive": not incident_occurred,
            "false_negative": False,  # Would be set separately
            "incident_id": incident_id,
            "lead_time_hours": lead_time_hours or 0,
            "recorded_at": "now"
        }

        return {
            "success": True,
            "prediction_id": prediction_id,
            "outcome_recorded": "true_positive" if incident_occurred else "false_positive"
        }

    except Exception as e:
        logger.error(f"Record outcome failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record outcome: {str(e)}"
        )
