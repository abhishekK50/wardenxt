# WardenXT Webhook System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Start the Servers (2 minutes)

```bash
# Terminal 1 - Backend
cd backend
python -m app.main

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Wait for both servers to start:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

### Step 2: Test Your First Webhook (1 minute)

**Option A: Using the UI (Easiest)**

1. Open `http://localhost:3000/webhooks`
2. Click **"Send Test Webhook"** (PagerDuty is pre-selected)
3. See success response with incident ID
4. Click **"View Incident"**

**Option B: Using curl**

```bash
curl -X POST http://localhost:8000/api/webhooks/generic \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "Test Alert",
    "severity": "critical",
    "host": "test-server",
    "message": "This is a test"
  }'
```

### Step 3: See It in Action (2 minutes)

1. **Open Dashboard**: Go to `http://localhost:3000/incidents`

2. **Watch Live Feed**: Look at the top-right corner
   - You'll see a floating "Live Feed" widget
   - Green dot = connected
   - Your test incident appears within 5 seconds

3. **Click the Incident**: In the live feed widget
   - Navigate to detail page
   - See purple "Webhook" badge
   - View auto-analysis results (wait 10-30 seconds)

4. **Expand Webhook Info**:
   - Click "Webhook Source" section
   - View raw JSON payload you sent

## 🎯 What Just Happened?

1. ✅ External webhook received at `/api/webhooks/generic`
2. ✅ Transformed into WardenXT incident format
3. ✅ Stored with unique incident ID
4. ✅ Background AI analysis started with Gemini 3
5. ✅ Live feed polled and updated (5-second interval)
6. ✅ Incident displayed with source information

## 🧪 Try Different Webhook Types

### PagerDuty
```bash
curl -X POST http://localhost:8000/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "title": "Database overload",
      "urgency": "high",
      "service": {"name": "PostgreSQL"}
    }
  }'
```

### Slack
```bash
curl -X POST http://localhost:8000/api/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{
    "text": "CRITICAL: API gateway down",
    "channel": "alerts"
  }'
```

### Generic (Any JSON)
```bash
curl -X POST http://localhost:8000/api/webhooks/generic \
  -H "Content-Type: application/json" \
  -d '{
    "whatever": "fields",
    "you": "want",
    "severity": "critical"
  }'
```

## 🎬 Demo Flow (For Video)

1. **Setup Shot**: Show WardenXT dashboard with existing incidents

2. **Send Webhook**: Use webhook test page or curl

3. **Live Feed Animation**:
   - Watch top-right corner
   - New incident slides in within 5 seconds
   - Point out severity (P0/P1/P2) and source icon

4. **Detail View**:
   - Click incident in live feed
   - Show webhook source badge
   - Expand raw payload section
   - Show AI analysis results

5. **Multiple Sources**:
   - Send 3 different webhook types
   - Show all in dashboard with different icons:
     - 📟 = PagerDuty
     - 💬 = Slack
     - 🔔 = Generic

## 📊 Expected Results

### Backend Response (< 100ms)
```json
{
  "status": "success",
  "incident_id": "INC-2026-0129-1245",
  "message": "Incident created and queued for analysis",
  "severity": "P2"
}
```

### Live Feed (Updates in 5 seconds)
- New incident appears at top
- Severity badge (colored)
- Source icon (emoji)
- "AI" badge (if analyzed)
- Time received ("2m ago")

### Detail Page Shows
- Purple "Webhook" badge with source name
- Auto-analysis section with Gemini results
- Collapsible raw payload viewer
- All standard incident details

## ❓ Troubleshooting

### "Backend not running"
```bash
cd backend
python -m app.main
```
Check for port conflicts (default: 8000)

### "Live feed not updating"
- Refresh page
- Check browser console for errors
- Verify you're logged in
- Check `/api/incidents/recent/list` endpoint

### "Webhook returns 500"
- Check backend logs for details
- Verify Gemini API key is set in `.env`
- Incident should still be created (analysis may fail)

### "No auto-analysis"
- Wait 10-30 seconds
- Check backend logs for "webhook_auto_analysis_started"
- Verify Gemini API is accessible

## 🔗 Useful URLs

- **Frontend Dashboard**: http://localhost:3000/incidents
- **Webhook Test Page**: http://localhost:3000/webhooks
- **Backend Health**: http://localhost:8000/health
- **Backend Docs**: http://localhost:8000/docs
- **Recent Incidents API**: http://localhost:8000/api/incidents/recent/list

## 📚 Next Steps

- Read [WEBHOOK_TESTING.md](./WEBHOOK_TESTING.md) for comprehensive testing
- Read [WEBHOOK_IMPLEMENTATION_SUMMARY.md](./WEBHOOK_IMPLEMENTATION_SUMMARY.md) for technical details
- Configure external tools to send webhooks to your endpoints
- Customize webhook transformers for your specific needs

## 💡 Pro Tips

1. **Use the Test Page** during development - easier than curl
2. **Watch Backend Logs** to see auto-analysis progress
3. **Open Two Browser Windows** - one for sending, one for watching live feed
4. **Test Error Cases** - send invalid JSON to see error handling
5. **Try Different Severities** - "critical", "high", "low" get mapped to P0/P1/P2

---

**Ready to integrate with PagerDuty, Slack, or any webhook-enabled tool!** 🎉
