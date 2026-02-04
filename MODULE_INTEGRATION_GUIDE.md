# WardenXT - Module Integration Guide

## Overview

This guide covers the integration between Module 1 (Webhook Ingestion) and Module 2 (Voice Interface), demonstrating how they work together to create a seamless incident management experience.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Systems                         │
│         (PagerDuty, Slack, Generic Monitoring Tools)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP POST Webhooks
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Module 1: Webhook Ingestion                   │
│  • Receives webhooks from external systems                       │
│  • Transforms to WardenXT format                                 │
│  • Triggers auto-analysis with Gemini AI                         │
│  • Stores in memory (webhook_incidents dict)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Merged Incident Data
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Unified Incident API                         │
│  • GET /api/incidents/ - Lists all incidents (file + webhook)   │
│  • GET /api/incidents/{id} - Get incident details               │
│  • GET /api/incidents/recent/list - Live feed with 5s polling   │
│  • POST /api/analysis/{id}/analyze - Analyze any incident       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Module 2: Voice Interface                     │
│  • POST /api/voice/query - Natural language queries             │
│  • GET /api/voice/speak/{id} - Audio summaries                  │
│  • Queries webhook + file incidents seamlessly                   │
│  • Gemini 2.0 Flash for transcription & TTS                     │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ React Components
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                              │
│  • LiveIncidentFeed - Shows webhook incidents in real-time      │
│  • VoiceCommander - Voice queries across all incidents          │
│  • Speaker icons - Audio summaries for any incident             │
│  • Dashboard - Unified view of all incident sources             │
└─────────────────────────────────────────────────────────────────┘
```

## Module 1: Webhook Ingestion

### Key Features

1. **Three Webhook Endpoints**:
   - `/api/webhooks/pagerduty` - PagerDuty incident webhooks
   - `/api/webhooks/slack` - Slack alert webhooks
   - `/api/webhooks/generic` - Generic JSON webhooks

2. **Automatic Processing**:
   - Transforms external formats to WardenXT `IncidentSummary` format
   - Generates unique incident IDs (`INC-YYYY-MMDD-HHMM`)
   - Maps severity levels (critical→P0, high→P1, medium→P2, low→P3)
   - Extracts service names, timestamps, and descriptions

3. **Auto-Analysis**:
   - Triggers Gemini AI analysis in background
   - Analyzes logs, metrics, and timeline data
   - Generates executive summary, root cause, and recommendations
   - Marks incident with `auto_analyzed: true` flag

4. **Live Feed**:
   - Real-time incident display (5-second polling)
   - Shows source icons (PagerDuty, Slack, Generic)
   - Auto-analyzed incidents marked with "AI" badge
   - Displays last 3 incidents in floating widget

### Implementation Files

**Backend**:
- [backend/app/models/incident.py](backend/app/models/incident.py) - Webhook models
- [backend/app/core/webhook_transformer.py](backend/app/core/webhook_transformer.py) - Format transformation
- [backend/app/api/webhooks.py](backend/app/api/webhooks.py) - Webhook endpoints
- [backend/app/api/incidents.py](backend/app/api/incidents.py#L209-L223) - Recent incidents endpoint

**Frontend**:
- [frontend/app/components/LiveIncidentFeed.tsx](frontend/app/components/LiveIncidentFeed.tsx) - Live feed widget
- [frontend/app/webhooks/page.tsx](frontend/app/webhooks/page.tsx) - Webhook testing UI

## Module 2: Voice Interface

### Key Features

1. **Voice Commander**:
   - Natural language queries via microphone
   - Auto-stops after 5 seconds
   - Displays transcript and response
   - Plays audio response with Gemini voice
   - Clickable incident IDs

2. **Audio Summaries**:
   - Speaker icons on incident cards
   - "Listen to Summary" button on detail pages
   - Comprehensive incident narration
   - One-click playback and stop

3. **Supported Commands**:
   - **Query**: "What are my P0 incidents?"
   - **Analyze**: "Analyze incident zero zero zero one"
   - **Status**: "What incidents are being investigated?"
   - **Summarize**: "Give me an overview of all incidents"

4. **Gemini Integration**:
   - Transcription: Speech-to-text using Gemini 2.0 Flash
   - TTS: Text-to-speech with "Puck" voice
   - NLP: Command parsing and intent recognition
   - Audio format: WebM recording, WAV playback

### Implementation Files

**Backend**:
- [backend/app/models/voice.py](backend/app/models/voice.py) - Voice models
- [backend/app/core/gemini_audio.py](backend/app/core/gemini_audio.py) - Gemini audio client
- [backend/app/core/voice_commands.py](backend/app/core/voice_commands.py) - Command execution
- [backend/app/utils/audio.py](backend/app/utils/audio.py) - Audio utilities
- [backend/app/api/voice.py](backend/app/api/voice.py) - Voice endpoints

**Frontend**:
- [frontend/app/components/VoiceCommander.tsx](frontend/app/components/VoiceCommander.tsx) - Voice UI
- [frontend/app/components/VoiceResponsePopup.tsx](frontend/app/components/VoiceResponsePopup.tsx) - Response display
- [frontend/app/components/VoiceCommandsHelp.tsx](frontend/app/components/VoiceCommandsHelp.tsx) - Help modal
- [frontend/lib/api.ts](frontend/lib/api.ts#L295-L357) - Voice API client

## Integration Points

### 1. Unified Incident Data Access

**How It Works**:
- Voice commands query both file-based and webhook incidents
- `voice_commands.py` imports webhook incident dictionaries:
  ```python
  from app.api.webhooks import webhook_incidents, webhook_incident_data
  ```
- Merges data sources before filtering/processing
- User gets seamless experience regardless of incident source

**Code Reference**:
- [backend/app/core/voice_commands.py:98-101](backend/app/core/voice_commands.py#L98-L101)

**Example Flow**:
```
User says: "What are my P0 incidents?"
↓
Voice transcription via Gemini
↓
Command parsed as "query" with severity="P0"
↓
Loads file incidents: ["INC-2026-0001", "INC-2026-0002"]
Loads webhook incidents: ["INC-2026-0129-1849"]
↓
Filters combined list for P0 severity
↓
Responds: "The most critical is INC-2026-0129-1849, a P0 database outage from PagerDuty..."
```

### 2. Auto-Analysis Integration

**How It Works**:
- Webhook arrives → transformed to WardenXT format
- Background task triggers analysis
- Gemini analyzes logs/metrics (15-30 seconds)
- Analysis cached for instant voice queries
- Voice can reference analysis results

**Code Reference**:
- [backend/app/api/webhooks.py:27-41](backend/app/api/webhooks.py#L27-L41) - Auto-analysis trigger

**Example Flow**:
```
PagerDuty sends webhook → /api/webhooks/pagerduty
↓
Transformed to INC-2026-0129-1849
↓
Background task: trigger_auto_analysis()
↓
Gemini analyzes: 500 log lines, 100 metric points, 12 timeline events
↓
Brief cached with root cause, recommendations
↓
User asks: "Analyze incident zero one two nine one eight four nine"
↓
Voice responds: "Analysis already completed! Root cause: Database connection pool exhausted..."
```

### 3. Live Feed + Voice Queries

**How It Works**:
- Live feed polls `/api/incidents/recent/list` every 5 seconds
- Shows new webhook incidents immediately
- User sees new incident → asks voice question
- Voice query includes latest webhook incidents
- Seamless real-time experience

**Code Reference**:
- [frontend/app/components/LiveIncidentFeed.tsx:20-26](frontend/app/components/LiveIncidentFeed.tsx#L20-L26)
- [backend/app/api/incidents.py:209-223](backend/app/api/incidents.py#L209-L223)

**Example Flow**:
```
t=0s: PagerDuty webhook creates INC-2026-0129-1900
↓
t=0-30s: Background analysis runs
↓
t=5s: Live feed polls and shows new incident (purple badge, "PagerDuty")
↓
t=10s: User clicks microphone, says "What's the latest incident?"
↓
Voice responds: "The latest incident is INC-2026-0129-1900, a P1 alert from PagerDuty affecting 3 services..."
```

### 4. Audio Summaries for Webhook Incidents

**How It Works**:
- Speaker icons work for all incidents (file + webhook)
- `/api/voice/speak/{id}` checks webhook_incident_data first
- Generates natural language summary
- Gemini TTS converts to audio
- User hears summary regardless of source

**Code Reference**:
- [backend/app/api/voice.py:94-129](backend/app/api/voice.py#L94-L129)

**Example Flow**:
```
User clicks speaker icon on webhook incident card
↓
Frontend: api.getIncidentAudioSummary("INC-2026-0129-1849")
↓
Backend checks webhook_incident_data dict
↓
Generates summary: "Incident INC-2026-0129-1849, severity P0, database outage affecting 5 services..."
↓
Gemini TTS with "Puck" voice
↓
Returns WAV audio file
↓
Browser plays audio
```

## End-to-End Integration Scenarios

### Scenario 1: PagerDuty Alert → Voice Query → Audio Summary

1. **PagerDuty sends webhook**:
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "PD12345",
      "title": "Database Connection Pool Exhausted",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "PostgreSQL Primary"}
    }
  }'
```

2. **WardenXT processes**:
   - Creates `INC-2026-0130-1045`
   - Transforms to WardenXT format
   - Triggers auto-analysis in background
   - Stores in `webhook_incidents` dict

3. **User sees in Live Feed** (within 5 seconds):
   - Purple "PagerDuty" badge
   - P1 severity indicator
   - "Database Connection Pool Exhausted" title
   - Blue "AI" badge after analysis completes

4. **User asks voice question**:
   - Clicks microphone
   - Says: "What's the latest critical incident?"
   - Voice responds with details about INC-2026-0130-1045

5. **User plays audio summary**:
   - Clicks speaker icon on incident card
   - Hears: "Incident INC-2026-0130-1045, a P1 database outage from PagerDuty..."

### Scenario 2: Slack Alert → Analysis → Voice Follow-up

1. **Slack sends webhook**:
```bash
curl -X POST http://localhost:8001/api/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[CRITICAL] API Gateway 502 errors spiking",
    "channel": "#incidents",
    "user": "monitoring_bot"
  }'
```

2. **Auto-analysis runs**:
   - 30 seconds of Gemini AI analysis
   - Analyzes pattern: API Gateway → Database timeout → Connection pool
   - Confidence: 87%

3. **User checks status via voice**:
   - Says: "What incidents are being investigated?"
   - Voice responds: "There are 2 incidents currently being investigated. 1 is P0, 1 is P1..."

4. **User navigates to detail page**:
   - Clicks incident ID in voice response
   - Sees auto-analysis results
   - Clicks "Listen to Summary"
   - Hears full incident narration

### Scenario 3: Generic Webhook → Multi-Source Query

1. **Custom monitoring tool sends webhook**:
```bash
curl -X POST http://localhost:8001/api/webhooks/generic \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CPU Threshold Exceeded on prod-web-01",
    "severity": "medium",
    "timestamp": "2026-01-30T15:30:00Z",
    "description": "CPU usage above 90% for 5 minutes",
    "service": "Web Server Pool"
  }'
```

2. **User queries all incidents**:
   - Says: "Summarize all incidents"
   - Voice responds: "You have 7 total incidents. 1 is P0, 3 are P1, and 3 are P2..."
   - Includes webhook incidents + file-based incidents

3. **User filters by severity**:
   - Says: "Show me all P2 incidents"
   - Voice lists all P2 including the new webhook incident

## Testing the Integration

### Quick Integration Test

1. **Start both services**:
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8001

# Terminal 2: Frontend
cd frontend
npm run dev
```

2. **Send test webhook**:
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "TEST001",
      "title": "Test Integration Incident",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "Test Service"}
    }
  }'
```

3. **Verify in UI**:
   - Open `http://localhost:3000/incidents`
   - See new incident in live feed (within 5 seconds)
   - Purple "PagerDuty" badge visible

4. **Test voice query**:
   - Click microphone button
   - Say: "What are my latest incidents?"
   - Verify response includes test incident

5. **Test audio summary**:
   - Click speaker icon on test incident
   - Verify audio plays

### Full Integration Test Matrix

| Test | Module 1 | Module 2 | Expected Result |
|------|----------|----------|-----------------|
| Send PagerDuty webhook → Ask voice "What's new?" | ✓ | ✓ | Voice lists webhook incident |
| Send Slack webhook → Play audio summary | ✓ | ✓ | Audio narrates Slack incident |
| Auto-analysis completes → Voice query "Analyze X" | ✓ | ✓ | Voice says "Already analyzed" |
| Live feed shows webhook → Click speaker icon | ✓ | ✓ | Audio plays immediately |
| Send webhook → Voice "Summarize all" | ✓ | ✓ | Count includes webhook |
| Multiple webhooks → Voice "Show P0" | ✓ | ✓ | Filters across all sources |

## Configuration

### Environment Variables

**Backend** (`backend/.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
APP_HOST=0.0.0.0
APP_PORT=8001
CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Port Configuration

- **Backend**: 8001 (changed from 8000 to avoid ComfyUI conflict)
- **Frontend**: 3000 (Next.js default)
- **Webhook Receiver**: 8001 (same as backend API)

## Performance Considerations

### Webhook Ingestion
- **Latency**: < 100ms from webhook receipt to response
- **Auto-Analysis**: Runs in background, doesn't block webhook response
- **Throughput**: Handles concurrent webhooks (FastAPI async)
- **Memory**: In-memory storage (production should use database)

### Voice Interface
- **Voice Query**: < 3 seconds (transcription + processing + TTS)
- **Audio Summary**: < 2 seconds (first byte)
- **Concurrent Queries**: Supported via FastAPI async
- **Audio Caching**: Brief results cached to speed up voice responses

### Live Feed
- **Polling Interval**: 5 seconds
- **Data Transfer**: Only incident summaries (not full logs/metrics)
- **Connection Status**: Shows "Connected" / "Connecting" indicator

## Troubleshooting Integration Issues

### Webhook Not Appearing in Voice Queries

**Symptom**: Webhook creates incident but voice doesn't find it

**Fix**:
1. Check `backend/app/core/voice_commands.py` imports webhook data
2. Verify `webhook_incidents` and `webhook_incident_data` are populated
3. Check incident ID format matches (INC-YYYY-MMDD-HHMM)

### Auto-Analysis Not Triggering

**Symptom**: Webhook incident created but not analyzed

**Fix**:
1. Check `GEMINI_API_KEY` is set in `backend/.env`
2. Verify background task started (check logs for "Analysis started")
3. Ensure incident has logs/metrics to analyze (webhook may have minimal data)

### Live Feed Not Updating

**Symptom**: Webhook sent but live feed doesn't show it

**Fix**:
1. Check `/api/incidents/recent/list` endpoint returns webhook incidents
2. Verify polling interval in `LiveIncidentFeed.tsx` (should be 5000ms)
3. Check browser console for fetch errors

### Audio Summary Fails for Webhook Incident

**Symptom**: Speaker icon doesn't work on webhook incidents

**Fix**:
1. Verify `backend/app/api/voice.py` checks webhook_incident_data
2. Check incident exists in webhook_incident_data dict
3. Ensure Gemini API key is valid for TTS

## Next Steps

After verifying integration:

1. **Production Deployment**:
   - Deploy backend to cloud service (GCP Cloud Run, AWS Lambda)
   - Deploy frontend to Vercel/Netlify
   - Configure production webhook URLs
   - Enable HTTPS (required for voice interface)

2. **Database Migration**:
   - Replace in-memory `webhook_incidents` with PostgreSQL/MongoDB
   - Add persistence for webhook incident data
   - Implement incident archival and cleanup

3. **Enhanced Integration**:
   - Real-time WebSocket for live feed (replace polling)
   - Voice-triggered status updates ("Mark incident X as resolved")
   - Voice-triggered webhook testing ("Send a test PagerDuty alert")
   - Multi-language voice support

4. **Monitoring**:
   - Add metrics for webhook ingestion rate
   - Track voice query success rate
   - Monitor auto-analysis completion time
   - Alert on failed webhook deliveries

## Success Metrics

Integration is successful when:

✅ Webhook incidents appear in voice query results
✅ Auto-analysis completes for webhook incidents
✅ Live feed shows webhook incidents in real-time
✅ Audio summaries work for all incident sources
✅ Voice commands filter across all incident types
✅ No errors when querying mixed incident sources
✅ Performance stays within latency targets

## Demo Flow for Hackathon

1. **Introduction** (30 seconds):
   - Show dashboard with existing file-based incidents
   - Explain WardenXT's AI-powered incident management

2. **Module 1 Demo** (1 minute):
   - Send PagerDuty webhook via curl
   - Show incident appear in live feed with purple badge
   - Show auto-analysis completing (blue "AI" badge)
   - Click incident to show detail page with webhook metadata

3. **Module 2 Demo** (1 minute):
   - Click microphone, ask "What are my P0 incidents?"
   - Show transcript and natural language response
   - Play audio response
   - Click incident ID to navigate

4. **Integration Demo** (1 minute):
   - Ask "What's the latest incident?" (includes webhook)
   - Show voice response references webhook incident
   - Click speaker icon on webhook incident card
   - Listen to audio summary
   - Navigate to detail page, click "Listen to Summary"

5. **Conclusion** (30 seconds):
   - Highlight Gemini multimodal capabilities
   - Mention real-world enterprise applications
   - Show help modal with available commands

Total: 4 minutes
