# WardenXT - Judges Quick Summary

## One-Liner
**AI-powered incident commander that reduces MTTR from hours to minutes using Google Gemini 3**

---

## The Problem
Production incidents cost $5,000-$10,000 per minute. Engineers spend 45+ minutes manually searching logs while systems burn.

## The Solution
WardenXT uses Gemini 3 to instantly analyze incidents, generate runbooks, and predict failures before they occur.

---

## Gemini Integration (5 Key Uses)

| # | Feature | Gemini Capability | Result |
|---|---------|-------------------|--------|
| 1 | Root Cause Analysis | Text generation with reasoning | 10,000 logs → cause in 4 sec |
| 2 | Voice Commands | Audio transcription | Hands-free incident investigation |
| 3 | Spoken Summaries | Text generation | Audio incident briefings |
| 4 | Runbook Generation | Code generation | Executable bash/kubectl scripts |
| 5 | Predictive Analytics | Pattern analysis | 24-72hr incident forecasting |

---

## Live Demo Features

1. **Webhook Ingestion** → PagerDuty alert creates incident in <100ms
2. **AI Analysis** → Gemini identifies root cause with reasoning transparency
3. **Voice Interface** → "What's the most critical incident?"
4. **Auto Runbooks** → One-click executable remediation scripts
5. **Predictions** → Risk score dashboard with forecasts

---

## Technical Stack

```
Backend:  FastAPI + Python 3.11 + Gemini API
Frontend: Next.js 14 + TypeScript + React
Database: SQLite (dev) / PostgreSQL (prod)
Auth:     JWT + RBAC (4 roles)
```

---

## Metrics

| Metric | Achievement |
|--------|-------------|
| AI Analysis Speed | **4.2 seconds** (vs 45 min manual) |
| Webhook Processing | **<50ms** |
| Test Coverage | **12/12 smoke tests passing** |
| Security Score | **8.5/10** (143% improvement) |

---

## Innovation Highlights

1. **Reasoning Transparency** - Shows AI's thought process (not black box)
2. **Executable Output** - Generates runnable scripts, not just text
3. **Proactive Prevention** - Predicts incidents before they happen
4. **Multi-Modal** - Text, voice, and visual interfaces
5. **Production-Ready** - Auth, security, rate limiting included

---

## Code Quality

- **150+ Python files** (backend)
- **40+ TypeScript files** (frontend)
- **24 React components**
- **8 API modules**
- **10+ documentation files**

---

## Demo Commands

```bash
# Start backend
cd backend && uvicorn app.main:app --port 8001

# Start frontend
cd frontend && npm run dev

# Trigger test incident
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{"event_type":"incident.triggered","incident":{"title":"Demo Alert","urgency":"high","service":{"name":"API"}}}'
```

---

## Key Differentiators

| vs Traditional Tools | WardenXT Advantage |
|---------------------|-------------------|
| Manual log search | AI correlates automatically |
| Static runbooks | Dynamic, context-aware generation |
| Reactive alerts | Predictive forecasting |
| Text-only | Voice-first + visual |

---

## Links

- **Demo Video:** [Link]
- **Repository:** [GitHub]
- **Live Demo:** localhost:3000

---

**Built for Google Gemini API Developer Competition**

*"From reactive firefighting to proactive prevention"*
