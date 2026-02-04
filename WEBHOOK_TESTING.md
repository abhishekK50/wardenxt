# WardenXT Webhook Ingestion System - Testing Guide

## Overview
This guide will help you test the newly implemented webhook ingestion system that allows WardenXT to automatically receive and process incidents from external monitoring tools (PagerDuty, Slack, generic webhooks).

## Features Implemented

### Backend
- ✅ Three webhook endpoints: `/api/webhooks/pagerduty`, `/api/webhooks/slack`, `/api/webhooks/generic`
- ✅ Webhook payload transformer (converts external formats to WardenXT format)
- ✅ In-memory storage for webhook-ingested incidents
- ✅ Auto-analysis trigger (background task that runs AI analysis on webhook incidents)
- ✅ Severity mapper (maps external urgency levels to P0/P1/P2)
- ✅ `/api/incidents/recent` endpoint for live feed

### Frontend
- ✅ LiveIncidentFeed component (floating widget with live polling)
- ✅ Webhook test page at `/webhooks`
- ✅ Webhook source indicators on incident detail pages
- ✅ Raw payload viewer (collapsible section)

## Prerequisites

1. **Backend running** on `http://localhost:8000`
2. **Frontend running** on `http://localhost:3000`
3. **Gemini API key** configured in backend `.env` file

## Testing Steps

### Step 1: Start the Servers

```bash
# Terminal 1 - Start Backend
cd backend
python -m app.main

# Terminal 2 - Start Frontend
cd frontend
npm run dev
```

### Step 2: Test Webhook Endpoints (Option A: Using curl)

#### Test PagerDuty Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "PD12345",
      "title": "High memory usage on prod-db-01",
      "urgency": "high",
      "status": "triggered",
      "service": {
        "name": "Database Cluster"
      },
      "created_at": "2026-01-28T10:30:00Z"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "incident_id": "INC-2026-0128-XXXX",
  "message": "Incident created and queued for analysis",
  "severity": "P1"
}
```

#### Test Slack Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ALERT: API response time >5s on checkout service",
    "channel": "incidents",
    "timestamp": "1738063800.123456",
    "user": "U12345"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "incident_id": "INC-2026-0128-XXXX",
  "message": "Incident created and queued for analysis",
  "severity": "P2"
}
```

#### Test Generic Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/generic \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "CPU Threshold Exceeded",
    "severity": "critical",
    "host": "web-server-03",
    "message": "CPU usage at 95% for 5 minutes"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "incident_id": "INC-2026-0128-XXXX",
  "message": "Incident created and queued for analysis",
  "severity": "P0",
  "extracted_fields": {
    "title": "CPU Threshold Exceeded",
    "services": ["web-server-03"],
    "severity": "P0"
  }
}
```

### Step 3: Test Webhook Test Page (Option B: Using UI)

1. Navigate to `http://localhost:3000/webhooks`
2. Select webhook type (PagerDuty, Slack, or Generic)
3. Review the pre-filled sample payload
4. Click **"Send Test Webhook"**
5. Verify success response appears
6. Click **"View Incident"** button to navigate to detail page

### Step 4: Verify Live Feed

1. Navigate to `http://localhost:3000/incidents`
2. Look for the **Live Feed** widget in the top-right corner
3. Verify you see:
   - Green connection indicator (✓)
   - Recently created webhook incidents
   - Incident severity badges (P0/P1/P2)
   - Source icons (📟 for PagerDuty, 💬 for Slack, 🔔 for Generic)
   - "AI" badge if auto-analyzed
4. Send another test webhook
5. Within 5 seconds, the new incident should appear in the live feed
6. Click on an incident in the live feed to navigate to detail page

### Step 5: Verify Incident Detail Page

1. Click on a webhook-ingested incident
2. Verify you see:
   - **Webhook source badge** (purple badge with webhook icon)
   - Source type displayed (PagerDuty/Slack/Generic)
   - "AI" badge if auto-analyzed
3. Look for **"Webhook Source"** section below the header
4. Click to expand and view **raw webhook payload**
5. Verify the JSON payload matches what you sent

### Step 6: Verify Auto-Analysis

1. Send a webhook
2. Wait 10-30 seconds for auto-analysis to complete
3. Navigate to the incident detail page
4. Verify:
   - **"AI" badge** appears on the webhook source badge
   - **AI Analysis section** shows Gemini 3 analysis results
   - Root cause analysis is populated
   - Recommended actions are present

### Step 7: Verify Incidents List Integration

1. Navigate to `http://localhost:3000/incidents`
2. Verify webhook-ingested incidents appear alongside file-based incidents
3. Look for the **purple webhook badge** on webhook incidents
4. Verify severity and status are correctly displayed

### Step 8: Test Error Handling

#### Invalid JSON
```bash
curl -X POST http://localhost:8000/api/webhooks/generic \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

**Expected:** 400 Bad Request with error message

#### Missing Required Fields (PagerDuty)
```bash
curl -X POST http://localhost:8000/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered"
  }'
```

**Expected:** 400 Bad Request with "Missing required field: 'incident'"

#### Missing Required Fields (Slack)
```bash
curl -X POST http://localhost:8000/api/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "incidents"
  }'
```

**Expected:** 400 Bad Request with "Missing required field: 'text'"

## Success Criteria Checklist

- [ ] Can POST to `/api/webhooks/pagerduty` and get incident created
- [ ] Can POST to `/api/webhooks/slack` and get incident created
- [ ] Can POST to `/api/webhooks/generic` and get incident created
- [ ] Auto-analysis triggers in background (check backend logs)
- [ ] Frontend live feed updates within 5 seconds of webhook
- [ ] Webhook test page successfully creates incidents
- [ ] Dashboard shows mix of manual + webhook incidents
- [ ] Detail page displays webhook source information
- [ ] Invalid JSON returns proper 400 error
- [ ] Backend returns 200 OK in <100ms (before analysis completes)

## Backend Logs to Watch

When a webhook is received, you should see logs like:

```
INFO: webhook_received - source=pagerduty ip=127.0.0.1
INFO: webhook_incident_created - incident_id=INC-2026-0128-1045 source=pagerduty severity=P1
INFO: webhook_auto_analysis_started - incident_id=INC-2026-0128-1045
INFO: webhook_auto_analysis_completed - incident_id=INC-2026-0128-1045 analysis_status=COMPLETED
```

## Demo Scenario for Video

1. **Open WardenXT Dashboard**
   - Show empty or minimal incidents dashboard
   - Point out Live Feed widget in top-right

2. **Navigate to Webhook Test Page**
   - Go to `/webhooks`
   - Select "PagerDuty" webhook type
   - Show pre-filled payload

3. **Send Test Webhook**
   - Click "Send Test Webhook"
   - Show success response
   - Highlight incident_id and severity

4. **Live Feed Animation**
   - Return to dashboard (`/incidents`)
   - Within 5 seconds, new incident slides into Live Feed
   - Point out severity badge (P1), source icon (📟), and "AI" badge

5. **Incident Detail Page**
   - Click on incident in Live Feed
   - Navigate to detail page
   - Show webhook source badge in header
   - Expand "Webhook Source" section
   - Show raw payload

6. **AI Analysis Results**
   - Wait for auto-analysis to complete (if not done)
   - Scroll to "Gemini 3 Analysis" section
   - Show root cause analysis
   - Show recommended mitigation actions

7. **Multiple Sources**
   - Send Slack webhook
   - Send Generic webhook
   - Return to dashboard
   - Show all three incidents with different source icons

This demonstrates: **Real-time ingestion, auto-analysis, and enterprise integration capability.**

## Troubleshooting

### Live Feed Not Updating
- Check browser console for API errors
- Verify `/api/incidents/recent/list` endpoint is accessible
- Check if you're logged in (authentication required)

### Webhook Returns 500 Error
- Check backend logs for detailed error
- Verify Gemini API key is configured
- Check if analysis is failing (webhook should still create incident)

### Auto-Analysis Not Running
- Check backend logs for "webhook_auto_analysis_started"
- Verify Gemini API is accessible
- Analysis runs in background - may take 10-30 seconds

### Incident Not Appearing in List
- Check if `/api/incidents/` endpoint includes webhook incidents
- Verify `get_webhook_incidents()` function is being called
- Check backend logs for errors

## Next Steps

1. **Production Deployment:**
   - Implement webhook signature validation (PagerDuty, Slack)
   - Add database persistence for webhook incidents
   - Configure rate limiting for webhook endpoints
   - Set up monitoring and alerting for webhook ingestion

2. **Enhancements:**
   - Add webhook retry mechanism
   - Implement webhook event log/audit trail
   - Support additional webhook sources (Datadog, New Relic, etc.)
   - Add webhook configuration UI

## API Reference

### Webhook Endpoints

#### POST /api/webhooks/pagerduty
Receive PagerDuty incident webhooks

**Request Body:**
```json
{
  "event_type": "incident.triggered",
  "incident": {
    "id": "string",
    "title": "string",
    "urgency": "high" | "low",
    "status": "string",
    "service": {
      "name": "string"
    },
    "created_at": "ISO8601 timestamp"
  }
}
```

**Response:** 200 OK
```json
{
  "status": "success",
  "incident_id": "INC-YYYY-MMDD-HHMM",
  "message": "Incident created and queued for analysis",
  "severity": "P0" | "P1" | "P2"
}
```

#### POST /api/webhooks/slack
Receive Slack alert webhooks

**Request Body:**
```json
{
  "text": "string (required)",
  "channel": "string",
  "timestamp": "string",
  "user": "string"
}
```

**Response:** 200 OK (same format as PagerDuty)

#### POST /api/webhooks/generic
Receive generic JSON webhooks

**Request Body:** Any valid JSON object

**Response:** 200 OK
```json
{
  "status": "success",
  "incident_id": "INC-YYYY-MMDD-HHMM",
  "message": "Incident created and queued for analysis",
  "severity": "P0" | "P1" | "P2",
  "extracted_fields": {
    "title": "string",
    "services": ["string"],
    "severity": "string"
  }
}
```

#### GET /api/incidents/recent/list?limit=5
Get recent incidents for live feed

**Query Parameters:**
- `limit` (optional): Number of incidents to return (1-50, default: 5)

**Response:** 200 OK
```json
{
  "total": number,
  "limit": number,
  "incidents": [
    {
      "incident_id": "string",
      "title": "string",
      "severity": "string",
      "status": "string",
      "created_at": "ISO8601 timestamp",
      "source": "pagerduty" | "slack" | "generic" | "manual",
      "auto_analyzed": boolean,
      "services_affected": ["string"]
    }
  ]
}
```

#### GET /api/webhooks/incidents/{incident_id}
Get webhook incident metadata (including raw payload)

**Response:** 200 OK
```json
{
  "incident_id": "string",
  "source": "pagerduty" | "slack" | "generic",
  "raw_payload": {},
  "created_at": "ISO8601 timestamp",
  "incident_data": {},
  "auto_analyzed": boolean,
  "analysis_id": "string" (optional)
}
```

## File Changes Summary

### Backend Files Created/Modified:
1. `backend/app/models/incident.py` - Added webhook models
2. `backend/app/core/webhook_transformer.py` - NEW: Webhook payload transformer
3. `backend/app/api/webhooks.py` - NEW: Webhook router with 3 endpoints
4. `backend/app/main.py` - Registered webhook router
5. `backend/app/api/incidents.py` - Updated to include webhook incidents

### Frontend Files Created/Modified:
1. `frontend/lib/api.ts` - Added `getRecentIncidents()` and `getWebhookIncident()` methods
2. `frontend/app/components/LiveIncidentFeed.tsx` - NEW: Live feed widget
3. `frontend/app/webhooks/page.tsx` - NEW: Webhook test page
4. `frontend/app/incidents/page.tsx` - Added LiveIncidentFeed component
5. `frontend/app/incidents/[id]/page.tsx` - Added webhook source display
6. `frontend/app/globals.css` - Added slide-in animation

---

**Built with ❤️ for the Gemini 3 Hackathon**
