# WardenXT - Gemini Integration Deep Dive

## Overview

WardenXT leverages Google Gemini across **5 distinct AI capabilities**, demonstrating the versatility of the Gemini API for enterprise applications.

---

## 1. Root Cause Analysis (gemini-3-flash-preview)

### Purpose
Analyze thousands of log entries and metrics to identify incident root causes in seconds.

### Implementation

**File:** `backend/app/core/agent/analyzer.py`

```python
import google.generativeai as genai

class IncidentAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name='gemini-3-flash-preview',
            generation_config={
                "temperature": 0.2,      # Low for consistency
                "max_output_tokens": 4096,
                "top_p": 0.95
            }
        )

    async def analyze_incident(self, incident: Incident, max_logs: int = 500):
        # Build context from logs, metrics, timeline
        context = self._build_context(incident, max_logs)

        prompt = f"""You are an expert Site Reliability Engineer analyzing a production incident.

## Incident Details
- Title: {incident.summary.title}
- Severity: {incident.summary.severity}
- Services Affected: {', '.join(incident.summary.services_affected)}
- Start Time: {incident.summary.start_time}

## Log Entries ({len(incident.logs)} total, showing {min(len(incident.logs), max_logs)})
{self._format_logs(incident.logs[:max_logs])}

## Metrics
{self._format_metrics(incident.metrics)}

## Your Task
Analyze this incident and provide:
1. **Root Cause**: The primary cause of the incident
2. **Contributing Factors**: Secondary issues that worsened the situation
3. **Timeline**: Key events in chronological order
4. **Impact Assessment**: Business and technical impact
5. **Recommendations**: Immediate and long-term fixes
6. **Your Reasoning**: Explain how you reached these conclusions

Be specific. Reference actual log entries and timestamps."""

        response = await self.model.generate_content_async(prompt)
        return self._parse_analysis(response.text)
```

### Prompt Engineering Techniques

1. **Persona Setting**: "You are an expert Site Reliability Engineer"
2. **Structured Input**: Clear sections for logs, metrics, timeline
3. **Structured Output**: Numbered list of required outputs
4. **Reasoning Request**: Explicit ask for explanation
5. **Specificity Instruction**: "Reference actual log entries"

### Performance Optimization

- **Log Chunking**: Process max 500 logs per request
- **Caching**: 60-minute TTL for repeated analyses
- **Rate Limiting**: 10 requests/minute per user
- **Token Efficiency**: ~2,500 tokens average per analysis

---

## 2. Runbook Generation (gemini-3-flash-preview)

### Purpose
Generate executable remediation scripts based on incident analysis.

### Implementation

**File:** `backend/app/core/runbook_generator.py`

```python
class RunbookGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    async def generate_runbook(self, incident: Incident, analysis: dict):
        prompt = f"""Generate a detailed runbook for this incident.

## Incident
- Type: {incident.summary.incident_type}
- Severity: {incident.summary.severity}
- Root Cause: {analysis.get('root_cause', 'Unknown')}
- Services: {incident.summary.services_affected}

## Requirements
Generate a runbook with:

1. **Diagnostic Commands** (safe, read-only)
   - Commands to verify the issue
   - Expected output for each command

2. **Remediation Steps** (may modify state)
   - Step-by-step fix procedure
   - Mark high-risk commands that need approval
   - Include verification after each step

3. **Rollback Procedure**
   - How to undo changes if they fail
   - Data backup commands if needed

4. **Verification Checklist**
   - How to confirm the fix worked

## Output Format
Return valid JSON:
{{
  "title": "Runbook title",
  "steps": [
    {{
      "step_number": 1,
      "category": "diagnostic|remediation|verification|rollback",
      "title": "Step title",
      "commands": [
        {{
          "command": "actual bash/kubectl command",
          "description": "What this does",
          "risk_level": "safe|medium|high",
          "expected_output": "What success looks like",
          "requires_approval": false
        }}
      ]
    }}
  ],
  "warnings": ["Important warnings"],
  "prerequisites": ["Required access/tools"]
}}"""

        response = await self.model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.1}  # Very low for code
        )
        return json.loads(response.text)
```

### Key Techniques

1. **JSON Output**: Structured format for parsing
2. **Risk Classification**: Commands tagged by safety level
3. **Approval Gates**: High-risk commands flagged
4. **Context Injection**: Uses analysis results

---

## 3. Voice Transcription (gemini-2.0-flash)

### Purpose
Transcribe audio queries for hands-free incident investigation.

### Implementation

**File:** `backend/app/core/gemini_audio.py`

```python
class GeminiAudioProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str):
        """Transcribe audio to text using Gemini"""

        # Upload audio to Gemini
        audio_file = genai.upload_file(
            io.BytesIO(audio_bytes),
            mime_type=mime_type
        )

        prompt = """Transcribe this audio accurately.
        Return only the transcription, no commentary.
        If the audio mentions incident IDs like "INC-2024-0001", preserve the exact format."""

        response = await self.model.generate_content_async([
            prompt,
            audio_file
        ])

        return response.text.strip()
```

### Supported Formats
- WAV, MP3, WebM, OGG
- Max file size: 10MB
- Sample rate: Any (Gemini handles conversion)

---

## 4. Voice Response Generation (gemini-3-flash-preview)

### Purpose
Generate natural language summaries for text-to-speech.

### Implementation

**File:** `backend/app/api/voice.py`

```python
@router.get("/speak/{incident_id}")
async def get_spoken_summary(incident_id: str):
    """Generate a speakable summary of an incident"""

    incident = load_incident(incident_id)

    prompt = f"""Create a brief spoken summary of this incident for an on-call engineer.

Incident: {incident.summary.title}
Severity: {incident.summary.severity}
Status: {incident.summary.status}
Services: {', '.join(incident.summary.services_affected)}
Duration: {incident.summary.duration_minutes} minutes
Root Cause: {incident.summary.root_cause.primary}

Requirements:
- Keep it under 30 seconds when spoken
- Use natural, conversational language
- Start with severity and status
- Mention key services affected
- End with current recommendation

Example style: "This is a P1 incident affecting the payment service.
The database connection pool is exhausted, causing checkout failures.
The team is currently investigating. Recommended action: scale the database pods."
"""

    response = model.generate_content(prompt)

    return {
        "summary_text": response.text,
        "use_browser_tts": True  # Frontend uses Web Speech API
    }
```

---

## 5. Predictive Analytics (gemini-3-flash-preview)

### Purpose
Forecast potential incidents based on patterns and anomalies.

### Implementation

**File:** `backend/app/core/gemini_predictor.py`

```python
class GeminiPredictor:
    async def predict_incidents(self, current_metrics: dict, historical_incidents: list):
        prompt = f"""Analyze system health and predict potential incidents.

## Current Metrics
{json.dumps(current_metrics, indent=2)}

## Recent Incidents (last 30 days)
{self._format_historical_incidents(historical_incidents)}

## Your Task
Based on patterns in historical incidents and current metrics:

1. **Risk Assessment**: Score from 0-100
2. **Predictions**: Likely incidents in next 24-72 hours
3. **Anomalies**: Unusual patterns in current metrics
4. **Recommendations**: Preventive actions

Return JSON:
{{
  "risk_score": 0-100,
  "risk_level": "low|medium|high|critical",
  "predictions": [
    {{
      "type": "Incident type",
      "probability": 0.0-1.0,
      "timeframe": "24h|48h|72h",
      "affected_services": ["service1"],
      "reasoning": "Why this is predicted"
    }}
  ],
  "anomalies": [
    {{
      "metric": "metric_name",
      "current_value": 123,
      "expected_range": "50-100",
      "severity": "warning|critical"
    }}
  ],
  "recommendations": [
    "Specific preventive action"
  ]
}}"""

        response = await self.model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.3}
        )
        return json.loads(response.text)
```

---

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional (defaults shown)
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_AUDIO_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=4096
```

### Model Selection Rationale

| Task | Model | Why |
|------|-------|-----|
| Analysis | gemini-3-flash-preview | Best reasoning, fast |
| Runbooks | gemini-3-flash-preview | Code generation quality |
| Audio | gemini-2.0-flash | Multi-modal support |
| Predictions | gemini-3-flash-preview | Pattern analysis |

---

## Error Handling

```python
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted, InvalidArgument

async def safe_generate(prompt: str):
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except ResourceExhausted:
        # Rate limit hit
        logger.warning("Gemini rate limit reached")
        raise HTTPException(429, "AI service temporarily unavailable")
    except InvalidArgument as e:
        # Bad input (too long, invalid content)
        logger.error(f"Invalid Gemini input: {e}")
        raise HTTPException(400, "Invalid input for AI analysis")
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise HTTPException(500, "AI analysis failed")
```

---

## Token Usage Optimization

### Strategies Used

1. **Log Sampling**: Show representative logs, not all
2. **Metric Aggregation**: Summary stats, not raw data points
3. **Prompt Caching**: Reuse analysis for same incident
4. **Chunked Processing**: Split large inputs across calls

### Typical Token Usage

| Operation | Input Tokens | Output Tokens |
|-----------|--------------|---------------|
| Analysis | ~2,000 | ~500 |
| Runbook | ~800 | ~1,200 |
| Prediction | ~1,500 | ~400 |
| Transcription | ~100 | ~50 |

---

## Testing Gemini Integration

```python
# backend/tests/test_gemini.py

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_incident_analysis():
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_model.return_value.generate_content_async = AsyncMock(
            return_value=Mock(text="Root cause: Database failure")
        )

        analyzer = IncidentAnalyzer()
        result = await analyzer.analyze_incident(sample_incident)

        assert "root_cause" in result
        mock_model.return_value.generate_content_async.assert_called_once()
```

---

## Future Enhancements

1. **Fine-tuning**: Train on organization's past incidents
2. **Embeddings**: Semantic search across incident history
3. **Multi-turn**: Conversational incident investigation
4. **Vision**: Analyze dashboards and architecture diagrams

---

*Gemini integration documentation for WardenXT*
