# WardenXT Demo Video Script (3 Minutes)

## Video Specifications
- **Duration:** 3:00 MAX (judges won't watch beyond this)
- **Format:** Screen recording with voiceover
- **Resolution:** 1920x1080
- **Upload to:** YouTube (unlisted) or Loom

---

## Pre-Recording Setup

```bash
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --port 8001

# Terminal 2 - Frontend
cd frontend && npm run dev

# Have this curl ready:
curl -X POST http://localhost:8001/api/webhooks/pagerduty -H "Content-Type: application/json" -d '{"event_type":"incident.triggered","incident":{"id":"DEMO","title":"CRITICAL: Database connection pool exhausted","urgency":"high","service":{"name":"Production Database"}}}'
```

- [ ] Logged in as admin
- [ ] Browser at incidents page
- [ ] Terminal visible for webhook
- [ ] Incident INC-2026-0001 ready

---

## SCRIPT (3:00 Total)

### [0:00 - 0:20] HOOK (20 sec)

**[SCREEN: Incident list with alerts]**

**VOICEOVER:**
> "A production incident is costing you $5,000 per minute. Your engineers are drowning in logs. WardenXT uses Gemini 3 to solve it in seconds. Let me show you."

---

### [0:20 - 0:55] WEBHOOK INGESTION + DATA FLOW (35 sec)

**[SCREEN: Split - Terminal left, Browser right]**

**VOICEOVER:**
> "First, real-time ingestion. A PagerDuty alert comes in..."

**[ACTION: Execute curl command]**

**VOICEOVER:**
> "In under 100 milliseconds, WardenXT receives the alert metadata and creates the incident. But here's the key—PagerDuty only sends metadata, not logs."

**[ACTION: Show incident appearing in list with LIVE badge]**

**VOICEOVER:**
> "WardenXT's architecture connects to your log aggregators—Datadog, CloudWatch, Splunk—to fetch the actual logs for analysis. The demo uses realistic synthetic data to showcase Gemini's capabilities."

**[ACTION: Point to services affected, cost estimate]**

---

### [0:55 - 1:40] AI ANALYSIS - THE WOW MOMENT (45 sec)

**[SCREEN: Click into incident detail]**

**VOICEOVER:**
> "Now the magic. This incident has over 10,000 log entries. An engineer would spend 45 minutes searching. Watch what Gemini does."

**[ACTION: Click "Analyze with AI"]**

**VOICEOVER:**
> "Gemini 3 Flash analyzes logs, correlates timestamps, builds a timeline..."

**[ACTION: Show progress/reasoning panel]**

**VOICEOVER (as results appear ~4 seconds):**
> "Four seconds. Root cause identified. Contributing factors listed. And critically—Gemini shows its reasoning. Engineers can verify, not just trust a black box."

**[ACTION: Scroll through analysis showing root cause, factors, recommendations]**

---

### [1:40 - 2:10] RUNBOOK GENERATION (30 sec)

**[SCREEN: Runbook section]**

**VOICEOVER:**
> "Knowing the cause is half the battle. Gemini also generates executable runbooks."

**[ACTION: Click "Generate Runbook"]**

**VOICEOVER:**
> "Diagnostic commands for investigation. Remediation steps with risk levels—high-risk commands require approval. Rollback procedures if things go wrong. This isn't documentation—it's executable code ready to run."

**[ACTION: Show commands, risk badges, export options]**

---

### [2:10 - 2:35] VOICE INTERFACE (25 sec)

**[SCREEN: Voice commander visible]**

**VOICEOVER:**
> "During an incident, engineers need hands free. WardenXT has a voice interface."

**[ACTION: Click "Listen to Summary"]**

**[AUDIO: Browser TTS reads incident summary]**

**VOICEOVER (after TTS):**
> "Gemini generates natural summaries for text-to-speech. Perfect for on-call engineers on the move."

---

### [2:35 - 2:55] PREDICTIVE ANALYTICS (20 sec)

**[SCREEN: Navigate to /dashboard]**

**VOICEOVER:**
> "But the real innovation is prevention. WardenXT doesn't just react—it predicts."

**[ACTION: Show risk score gauge, trend chart]**

**VOICEOVER:**
> "Current risk score, historical trends, anomaly detection, and 24-72 hour forecasts. Gemini identifies patterns from past incidents to prevent future ones."

---

### [2:55 - 3:00] CLOSING (5 sec)

**[SCREEN: Dashboard or landing page]**

**VOICEOVER:**
> "WardenXT. From reactive firefighting to proactive prevention. Built with Gemini 3."

**[SCREEN: Logo + tagline]**

---

## TIMING BREAKDOWN

| Section | Start | End | Duration |
|---------|-------|-----|----------|
| Hook | 0:00 | 0:20 | 20 sec |
| Webhook + Data Flow | 0:20 | 0:55 | 35 sec |
| AI Analysis (WOW) | 0:55 | 1:40 | 45 sec |
| Runbook Generation | 1:40 | 2:10 | 30 sec |
| Voice Interface | 2:10 | 2:35 | 25 sec |
| Predictive Analytics | 2:35 | 2:55 | 20 sec |
| Closing | 2:55 | 3:00 | 5 sec |
| **TOTAL** | | | **3:00** |

---

## KEY MESSAGES TO HIT

1. **Problem:** $5K/minute, 45 min manual analysis
2. **Solution:** 4 seconds with Gemini
3. **Differentiator:** Reasoning transparency (not black box)
4. **Breadth:** 5 Gemini features (analysis, code gen, audio, predictions, voice)
5. **Production Ready:** Not a prototype

---

## RECORDING TIPS

1. **Pace:** Speak clearly but briskly—3 min is tight
2. **Pauses:** Minimize dead air, cut in editing
3. **Focus:** AI Analysis is the WOW moment—give it time
4. **Rehearse:** Practice 2-3 times before recording
5. **Backup:** Record sections separately if needed

---

## POST-RECORDING CHECKLIST

- [ ] Video is exactly 3:00 or less
- [ ] Audio is clear, no background noise
- [ ] All features visible and working
- [ ] Upload to YouTube (unlisted) or Loom
- [ ] Test video link works publicly
- [ ] Add to Devpost submission

---

*Script optimized for Gemini 3 Hackathon - 3 minute maximum*
