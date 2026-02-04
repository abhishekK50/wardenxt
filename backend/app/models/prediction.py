"""
Prediction Models
Data models for predictive analytics and incident forecasting
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class IncidentPrediction(BaseModel):
    """Predicted incident with probability and reasoning"""
    prediction_id: str = Field(..., description="Unique prediction identifier")
    predicted_at: str = Field(..., description="ISO timestamp when prediction was made")
    time_horizon: str = Field(..., description="Prediction window: 24h, 48h, 72h")
    probability: float = Field(..., ge=0, le=100, description="Probability of incident (0-100)")
    confidence: float = Field(..., ge=0, le=100, description="Confidence in prediction (0-100)")
    predicted_incident_type: str = Field(..., description="Type of predicted incident")
    predicted_severity: str = Field(..., description="Predicted severity: P0, P1, P2, P3, N/A")
    time_window: Optional[str] = Field(None, description="Specific time window (e.g., 'next 18-24 hours')")
    likely_services: List[str] = Field(default_factory=list, description="Services likely to be affected")
    warning_signs: List[str] = Field(default_factory=list, description="Early warning indicators")
    recommended_actions: List[str] = Field(default_factory=list, description="Preventive actions to take")
    reasoning: str = Field(..., description="Gemini's detailed explanation for this prediction")


class RiskScore(BaseModel):
    """Current system risk assessment"""
    score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    level: str = Field(..., description="Risk level: low, medium, high, critical")
    calculated_at: str = Field(..., description="ISO timestamp when calculated")
    contributing_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Factors increasing risk with weights and scores"
    )
    trend: str = Field(..., description="Risk trend: increasing, stable, decreasing")
    trend_percentage: float = Field(default=0.0, description="Percentage change in risk")
    forecast_change: str = Field(default="", description="Projected change (e.g., '+15% in next 6h')")


class Anomaly(BaseModel):
    """Detected system anomaly"""
    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    detected_at: str = Field(..., description="ISO timestamp when detected")
    metric_name: str = Field(..., description="Name of the anomalous metric")
    metric_type: str = Field(default="system", description="Type: cpu, memory, network, error, latency")
    current_value: float = Field(..., description="Current metric value")
    expected_value: float = Field(..., description="Expected/baseline value")
    deviation_percentage: float = Field(..., description="Percentage deviation from expected")
    severity: str = Field(..., description="Severity: minor, moderate, severe")
    likely_cause: str = Field(default="", description="Probable cause of anomaly")
    recommended_action: str = Field(default="", description="Recommended response")
    related_service: Optional[str] = Field(None, description="Service related to this anomaly")


class PreventiveRecommendation(BaseModel):
    """Recommended preventive action"""
    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    priority: str = Field(..., description="Priority: urgent, high, medium, low")
    title: str = Field(..., description="Short title for the recommendation")
    description: str = Field(..., description="Detailed description")
    estimated_impact: str = Field(..., description="Expected risk reduction (e.g., 'Reduces P1 risk by 45%')")
    implementation_effort: str = Field(..., description="Time/effort estimate (e.g., '15 minutes')")
    commands: List[str] = Field(default_factory=list, description="Commands to execute")
    related_prediction_id: Optional[str] = Field(None, description="Related prediction if any")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed, dismissed")


class SimulationRequest(BaseModel):
    """Request to simulate a scenario"""
    scenario: str = Field(..., description="Scenario to simulate (e.g., 'scale down to 2 replicas')")
    time_horizon: str = Field(default="24h", description="Time horizon: 6h, 12h, 24h")


class SimulationResult(BaseModel):
    """Result of scenario simulation"""
    scenario: str = Field(..., description="The simulated scenario")
    simulated_at: str = Field(..., description="ISO timestamp of simulation")
    time_horizon: str = Field(..., description="Time horizon used")
    predicted_outcome: str = Field(..., description="What would likely happen")
    incident_probability_before: float = Field(..., description="Incident probability before action")
    incident_probability_after: float = Field(..., description="Incident probability after action")
    probability_change: float = Field(..., description="Change in probability (negative = good)")
    impact_assessment: str = Field(..., description="Assessment of impact")
    recommendation: str = Field(..., description="Whether to proceed with scenario")
    risks: List[str] = Field(default_factory=list, description="Risks of this scenario")
    benefits: List[str] = Field(default_factory=list, description="Benefits of this scenario")


class PredictionAccuracy(BaseModel):
    """Tracking prediction accuracy over time"""
    period: str = Field(..., description="Time period (e.g., 'last_7_days')")
    total_predictions: int = Field(default=0, description="Total predictions made")
    true_positives: int = Field(default=0, description="Predicted incidents that occurred")
    false_positives: int = Field(default=0, description="Predicted incidents that didn't occur")
    false_negatives: int = Field(default=0, description="Incidents that weren't predicted")
    precision: float = Field(default=0.0, description="TP / (TP + FP)")
    recall: float = Field(default=0.0, description="TP / (TP + FN)")
    f1_score: float = Field(default=0.0, description="Harmonic mean of precision and recall")
    average_lead_time: float = Field(default=0.0, description="Avg hours warning before incident")


class HistoricalPattern(BaseModel):
    """Identified pattern from historical data"""
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: str = Field(..., description="Type: temporal, correlation, threshold, sequence")
    description: str = Field(..., description="Human-readable pattern description")
    frequency: int = Field(default=1, description="How often this pattern has occurred")
    confidence: float = Field(..., ge=0, le=100, description="Confidence in pattern")
    associated_incident_types: List[str] = Field(default_factory=list)
    precursor_signals: List[str] = Field(default_factory=list, description="Signals that precede this pattern")
    typical_lead_time: str = Field(default="", description="How long before incident pattern appears")


class RiskTrendPoint(BaseModel):
    """Single point in risk trend history"""
    timestamp: str = Field(..., description="ISO timestamp")
    score: int = Field(..., ge=0, le=100, description="Risk score at this time")
    level: str = Field(..., description="Risk level at this time")
    incident_occurred: bool = Field(default=False, description="Whether incident occurred at this time")


class PredictionForecast(BaseModel):
    """Complete forecast response"""
    generated_at: str = Field(..., description="When forecast was generated")
    time_horizon: str = Field(..., description="Forecast window")
    predictions: List[IncidentPrediction] = Field(default_factory=list)
    overall_risk: str = Field(..., description="Overall risk assessment for period")
    summary: str = Field(..., description="Natural language summary")
