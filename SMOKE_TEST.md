# WardenXT Smoke Test & Demo Scenarios

**Backend URL:** http://localhost:8001
**Frontend URL:** http://localhost:3000
**Test Date:** 2026-02-02

---

## Quick Smoke Test Checklist

### 1. Health & Authentication
- [ ] Backend health check
- [ ] Login with admin/admin123
- [ ] JWT token received

### 2. Incidents Module
- [ ] List all incidents
- [ ] View incident detail
- [ ] Live duration tracking visible
- [ ] Status badge displays correctly

### 3. AI Analysis
- [ ] Trigger AI analysis on incident
- [ ] View analysis results
- [ ] Reasoning transparency visible

### 4. Voice Interface
- [ ] Voice commander button visible
- [ ] Listen to Summary works (browser TTS)
- [ ] Voice commands help modal

### 5. Runbook Generation
- [ ] Generate runbook for incident
- [ ] View diagnostic commands
- [ ] Export as Markdown works

### 6. Predictive Analytics
- [ ] Dashboard loads
- [ ] Risk score gauge displays
- [ ] Risk trend chart renders
- [ ] Anomaly alerts visible

### 7. Webhook Ingestion
- [ ] Send test PagerDuty webhook
- [ ] Incident auto-created
- [ ] Appears in incident list

---

## Demo Scenario 1: "Production Database Alert"

**Story:** A P1 alert comes in from PagerDuty about high memory usage on the production database.

### Steps:
1. **Trigger Webhook** (Terminal):
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "PD-DEMO-001",
      "title": "CRITICAL: Database connection pool exhausted on prod-db-primary",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "Production Database"},
      "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }
  }'
```

2. **Show Incident List** - New incident appears with LIVE duration
3. **Click Incident** - View detailed page
4. **Trigger AI Analysis** - Show Gemini analyzing logs
5. **Show Reasoning** - AI explains its conclusions
6. **Generate Runbook** - One-click remediation steps
7. **Update Status** - Move from DETECTED to INVESTIGATING

### Key Talking Points:
- "Incident auto-ingested in under 100ms"
- "AI analyzed 1000+ log entries in seconds"
- "Executable runbook generated automatically"

---

## Demo Scenario 2: "Voice-First Incident Response"

**Story:** On-call engineer uses voice commands hands-free during incident.

### Steps:
1. **Open any incident detail page**
2. **Click Voice Commander** (microphone button)
3. **Say:** "What's happening with this incident?"
4. **Show Response** - AI provides spoken summary
5. **Click "Listen to Summary"** - Browser reads incident aloud
6. **Show Voice Commands Help** - Available commands

### Key Talking Points:
- "Hands-free incident investigation"
- "Natural language queries"
- "Works in high-pressure situations"

---

## Demo Scenario 3: "Predictive Prevention"

**Story:** System predicts potential incident 24 hours before it happens.

### Steps:
1. **Navigate to Predictive Dashboard** (/dashboard)
2. **Show Risk Score Gauge** - Current risk level
3. **Explain Risk Factors** - What's contributing to risk
4. **Show Risk Trend Chart** - Historical pattern
5. **Point out Anomalies** - Early warning signals
6. **Show Recommendations** - Preventive actions
7. **What-If Simulator** - "What if we add more replicas?"

### Key Talking Points:
- "From reactive to proactive"
- "Predict incidents before they happen"
- "Data-driven recommendations"

---

## Test Commands Reference

### Login & Get Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
echo "Token: $TOKEN"
```

### List Incidents
```bash
curl -s http://localhost:8001/api/incidents/ \
  -H "Authorization: Bearer $TOKEN" | jq '.incidents | length'
```

### Get Incident Detail
```bash
curl -s "http://localhost:8001/api/incidents/INC-2026-0001" \
  -H "Authorization: Bearer $TOKEN" | jq '.summary.title'
```

### Trigger AI Analysis
```bash
curl -s -X POST "http://localhost:8001/api/analysis/INC-2026-0001/analyze" \
  -H "Authorization: Bearer $TOKEN" | jq '.analysis_status'
```

### Get Risk Score
```bash
curl -s http://localhost:8001/api/predictions/risk-score \
  -H "Authorization: Bearer $TOKEN" | jq '.score'
```

### Send PagerDuty Webhook
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "PD12345",
      "title": "High CPU usage on api-server-03",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "API Gateway"},
      "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }
  }'
```

### Update Status
```bash
curl -s -X POST "http://localhost:8001/api/status/INC-2026-0001/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_status":"INVESTIGATING","updated_by":"admin","notes":"Starting investigation"}' | jq
```

### Generate Runbook
```bash
curl -s -X POST "http://localhost:8001/api/runbooks/INC-2026-0001/generate" \
  -H "Authorization: Bearer $TOKEN" | jq '.runbook.title'
```

---

## Expected Results

| Test | Expected | Pass/Fail |
|------|----------|-----------|
| Health Check | `{"status":"healthy"...}` | |
| Login | JWT token returned | |
| List Incidents | Array of incidents | |
| Incident Detail | Full incident object | |
| AI Analysis | Analysis with recommendations | |
| Risk Score | 0-100 score with factors | |
| Webhook Ingest | New incident created | |
| Status Update | Status changed | |
| Runbook | Commands generated | |

---

## Troubleshooting

### Backend Not Responding
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Not Responding
```bash
cd frontend
npm run dev
```

### Gemini API Error
- Check `GEMINI_API_KEY` in `.env`
- Verify API key is valid at https://makersuite.google.com

### Authentication Failed
- Use credentials: admin / admin123
- Check token not expired

---

## Demo Tips

1. **Have backup plan** - Screenshots/video if live demo fails
2. **Pre-warm the cache** - Run AI analysis before demo
3. **Use real-looking data** - The generated incidents look realistic
4. **Show the speed** - Emphasize <5 second AI analysis
5. **Highlight Gemini** - This is a Gemini hackathon!

---

*Generated for Google Gemini 3 Hackathon Demo*
