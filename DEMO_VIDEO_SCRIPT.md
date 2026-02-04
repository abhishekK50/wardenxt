# WardenXT Demo Video Script

## Video Details

- **Target Length:** 3-5 minutes
- **Format:** Screen recording with voiceover
- **Resolution:** 1920x1080 (Full HD)
- **Audio:** Clear voiceover, no background music during demos

---

## Pre-Recording Checklist

- [ ] Backend running on port 8001
- [ ] Frontend running on port 3000
- [ ] Logged in as admin (admin/admin123)
- [ ] Clear browser cache
- [ ] Close unnecessary tabs/notifications
- [ ] Test microphone levels
- [ ] Prepare webhook curl command in terminal
- [ ] Have incident INC-2026-0001 ready for analysis

---

## Script with Timestamps

### Opening (0:00 - 0:30)

**[SCREEN: WardenXT landing page]**

**VOICEOVER:**
> "When a production incident hits, every minute costs thousands of dollars. Engineers frantically search through logs, guess at root causes, and scramble for fixes.

> WardenXT changes everything. Using Google Gemini 3, it transforms reactive firefighting into proactive prevention.

> Let me show you how."

**[ACTION: Smooth scroll through landing page features]**

---

### Demo 1: Real-Time Incident Ingestion (0:30 - 1:15)

**[SCREEN: Split view - Terminal on left, Browser on right]**

**VOICEOVER:**
> "First, let's see how WardenXT handles a real incident from PagerDuty."

**[ACTION: Show terminal with curl command]**

**VOICEOVER:**
> "I'll send a PagerDuty webhook simulating a database alert."

**[ACTION: Execute the command]**
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
      "service": {"name": "Production Database"}
    }
  }'
```

**VOICEOVER:**
> "In under 100 milliseconds, WardenXT receives the webhook, transforms it to our format, assigns a severity, estimates business impact, and creates an incident."

**[ACTION: Click to incidents page, show new incident appearing]**

**VOICEOVER:**
> "Notice the LIVE indicator showing real-time duration tracking. The estimated cost and user impact are calculated automatically based on severity."

**[ACTION: Highlight the $15,000+ cost and 5000+ users]**

---

### Demo 2: AI Root Cause Analysis (1:15 - 2:15)

**[SCREEN: Incident detail page]**

**VOICEOVER:**
> "Now let's see Gemini's power. This incident has over 10,000 log entries across multiple services."

**[ACTION: Click on an incident (INC-2026-0001)]**

**VOICEOVER:**
> "Traditionally, an engineer would spend 30-45 minutes manually correlating these logs. Let's trigger AI analysis."

**[ACTION: Click "Analyze with AI" button]**

**VOICEOVER:**
> "Watch the AI reasoning panel. Gemini is analyzing logs, identifying patterns, and building a timeline."

**[ACTION: Show the reasoning/progress indicators]**

**VOICEOVER (as results appear):**
> "In just 4 seconds, Gemini identified the root cause: a disk controller failure that triggered a cascade of errors. It even shows its reasoning process—how it correlated error timestamps, identified the primary failure point, and traced the impact across services."

**[ACTION: Scroll through the analysis showing:]**
- Root cause identification
- Contributing factors
- Timeline of events
- Recommendations

**VOICEOVER:**
> "This transparency is crucial. Engineers can verify the AI's reasoning rather than blindly trusting a black box."

---

### Demo 3: Voice AI Commander (2:15 - 2:45)

**[SCREEN: Incident page with Voice Commander visible]**

**VOICEOVER:**
> "During an incident, engineers need their hands free. WardenXT's voice interface lets them investigate without typing."

**[ACTION: Click on the microphone/voice button]**

**VOICEOVER:**
> "Let's ask about this incident."

**[ACTION: Click "Listen to Summary" or use voice command]**

**[AUDIO: Browser TTS reads the incident summary]**

**VOICEOVER (after TTS completes):**
> "The AI provided a concise spoken summary—perfect for an on-call engineer driving to the office or working on multiple monitors."

---

### Demo 4: Auto Runbook Generation (2:45 - 3:30)

**[SCREEN: Incident detail page - Runbook section]**

**VOICEOVER:**
> "Knowing the cause is only half the battle. Engineers need executable fixes. Let's generate a runbook."

**[ACTION: Click "Generate Runbook" button]**

**VOICEOVER:**
> "Gemini generates a complete remediation playbook with diagnostic commands, remediation steps, and rollback procedures."

**[ACTION: Show the generated runbook with:]**
- Diagnostic commands (bash, kubectl, SQL)
- Step-by-step remediation
- Verification checks
- Rollback instructions

**VOICEOVER:**
> "Each command is categorized by risk level. High-risk commands require approval before execution. This isn't just documentation—it's an executable playbook."

**[ACTION: Show export options - Markdown, JSON, Script]**

**VOICEOVER:**
> "Teams can export this as Markdown for documentation, JSON for automation, or a shell script for direct execution."

---

### Demo 5: Predictive Analytics (3:30 - 4:15)

**[SCREEN: Predictive Dashboard]**

**VOICEOVER:**
> "But the real innovation is prevention. WardenXT doesn't just respond to incidents—it predicts them."

**[ACTION: Navigate to /dashboard]**

**VOICEOVER:**
> "The risk score gauge shows our current system health. Right now we're at medium risk."

**[ACTION: Point to Risk Score Gauge]**

**VOICEOVER:**
> "The trend chart shows how risk has evolved over the past 24 hours. These colored zones indicate severity thresholds."

**[ACTION: Point to Risk Trend Chart]**

**VOICEOVER:**
> "And here are active predictions. Gemini analyzes patterns from past incidents, current metrics, and anomalies to forecast potential issues."

**[ACTION: Show Prediction Cards]**

**VOICEOVER:**
> "We can even run what-if simulations. What happens if we add more replicas? Will that reduce our risk?"

**[ACTION: Show What-If Simulator if time permits]**

---

### Closing (4:15 - 4:45)

**[SCREEN: Return to landing page or dashboard overview]**

**VOICEOVER:**
> "WardenXT demonstrates how Google Gemini transforms enterprise operations:

> - **Analysis in seconds, not hours** - Gemini processes thousands of logs instantly
> - **Voice-first interface** - Hands-free investigation when every second counts
> - **Executable outputs** - Not just recommendations, but ready-to-run commands
> - **Predictive prevention** - Stop incidents before they happen

> This is the future of incident management. From reactive firefighting to proactive prevention.

> Thank you for watching."

**[SCREEN: WardenXT logo with tagline: "From reactive firefighting to proactive prevention"]**

---

## B-Roll Suggestions

If you want to add visual variety:

1. **0:00-0:10:** Quick montage of alert notifications, log scrolling, stressed engineer
2. **Between demos:** Brief transition showing Gemini logo
3. **Closing:** Side-by-side comparison: "Before" (manual log search) vs "After" (AI analysis)

---

## Alternative Short Version (2 minutes)

If you need a shorter video:

### Short Script

**[0:00-0:15] Hook**
> "A production incident is costing you $5,000 per minute. WardenXT powered by Google Gemini solves it in seconds."

**[0:15-0:45] Webhook + Auto-Analysis**
> Show webhook trigger → incident creation → AI analysis → results

**[0:45-1:15] Runbook Generation**
> Show one-click runbook with executable commands

**[1:15-1:45] Predictive Dashboard**
> Quick tour of risk score and predictions

**[1:45-2:00] Closing**
> "WardenXT: From reactive firefighting to proactive prevention. Built with Google Gemini."

---

## Recording Tips

1. **Pace:** Speak slowly and clearly, pause between sections
2. **Mouse movements:** Move cursor smoothly, not erratically
3. **Highlighting:** Use cursor to point at key elements
4. **Timing:** Practice the flow before recording
5. **Backup:** Record multiple takes of each section
6. **Audio:** Record voiceover separately for cleaner audio if needed

---

## Post-Production Checklist

- [ ] Trim dead air and pauses
- [ ] Add subtle transitions between sections
- [ ] Include captions/subtitles
- [ ] Add Gemini/Google branding where appropriate
- [ ] Ensure audio levels are consistent
- [ ] Export at 1080p, high bitrate

---

## Commands to Prepare Before Recording

### Terminal Commands (have these ready to paste)

**1. PagerDuty Webhook:**
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{"event_type":"incident.triggered","incident":{"id":"PD-DEMO-001","title":"CRITICAL: Database connection pool exhausted on prod-db-primary","urgency":"high","status":"triggered","service":{"name":"Production Database"}}}'
```

**2. Check Health (backup):**
```bash
curl http://localhost:8001/health | jq
```

**3. List Incidents (backup):**
```bash
curl http://localhost:8001/api/incidents/ -H "Authorization: Bearer $TOKEN" | jq '.incidents | length'
```

---

## Timing Summary

| Section | Duration | Cumulative |
|---------|----------|------------|
| Opening | 30 sec | 0:30 |
| Webhook Ingestion | 45 sec | 1:15 |
| AI Analysis | 60 sec | 2:15 |
| Voice Interface | 30 sec | 2:45 |
| Runbook Generation | 45 sec | 3:30 |
| Predictive Analytics | 45 sec | 4:15 |
| Closing | 30 sec | 4:45 |

**Total: ~4 minutes 45 seconds**

---

*Script prepared for Google Gemini API Developer Competition*
