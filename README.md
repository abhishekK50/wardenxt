# WardenXT - AI-Powered Incident Commander

[![Built with Gemini 3](https://img.shields.io/badge/Built%20with-Gemini%203-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)

> **From reactive firefighting to proactive prevention.** WardenXT uses Google Gemini 3 Flash to analyze critical incidents, predict failures before they occur, and generate executable remediation plans in seconds.

---

## 🤖 Gemini Integration

WardenXT leverages **five distinct Gemini 3 capabilities** to transform incident management:

**1. Root Cause Analysis (gemini-3-flash-preview)**
Gemini analyzes 10,000+ log entries in under 5 seconds, identifying root causes that would take engineers 45+ minutes manually. The model correlates timestamps, error patterns, and service dependencies with full reasoning transparency.

**2. Runbook Generation (Code Generation)**
One-click generation of executable bash, kubectl, and SQL commands. Gemini produces structured remediation scripts with risk-level tagging and approval gates for dangerous operations.

**3. Voice Transcription (gemini-2.0-flash)**
Hands-free incident investigation using audio input. Engineers query incidents naturally: "What's affecting the payment service?" Gemini transcribes and processes voice commands in real-time.

**4. Spoken Summaries (Text Generation)**
Gemini generates natural language incident briefings optimized for text-to-speech, enabling audio updates for on-call engineers.

**5. Predictive Analytics (Pattern Analysis)**
Historical incident patterns combined with current metrics enable 24-72 hour incident forecasting. Gemini identifies anomalies and recommends preventive actions before failures occur.

Gemini is central to every core feature—without it, WardenXT would require manual log analysis, static runbooks, and reactive-only responses. The integration demonstrates Gemini's versatility across text analysis, code generation, audio processing, and predictive reasoning.

---

## 🎯 Problem Statement

When P0/P1/P2 incidents hit production systems, engineering teams face three critical challenges:

1. **Information Overload**: Thousands of logs, metrics, and alerts to manually correlate during high-pressure situations
2. **Reactive Response**: Fighting fires instead of preventing them, leading to repeated incidents
3. **Tribal Knowledge**: Remediation steps locked in senior engineers' heads, unavailable at 3 AM

**WardenXT solves these with AI-powered intelligence**, turning hours of investigation into seconds of automated analysis.

---

## ✨ Key Features

### 🔍 AI Root Cause Analysis
Gemini 3 analyzes thousands of log entries, metrics, and events to identify root causes in seconds—not hours.

- **Log Correlation**: Automatically correlates logs across multiple services
- **Timeline Construction**: Builds incident timelines with key events highlighted
- **Reasoning Transparency**: Shows AI's reasoning process for every conclusion

### 🎤 Voice AI Commander
Natural language queries with spoken responses—hands-free incident investigation.

```
"What's the most critical incident right now?"
"Summarize the database outage from yesterday"
"What services are affected by INC-2024-0042?"
```

### 🛠️ Auto Runbook Generation
One-click generation of executable remediation scripts.

- **Diagnostic Commands**: bash, kubectl, SQL queries for investigation
- **Remediation Steps**: Step-by-step fix procedures with verification
- **Rollback Instructions**: Safe recovery paths if fixes fail
- **Export Formats**: Markdown, JSON, executable scripts

### 📊 Predictive Analytics
Forecast incidents 24-72 hours before they occur.

- **Risk Scoring**: Real-time 0-100 risk score with contributing factors
- **Pattern Analysis**: Historical incident pattern matching
- **Anomaly Detection**: Early warning signals from metrics and logs
- **What-If Simulation**: Test scenarios before making changes

### ⚡ Real-Time Ingestion
Webhook integration with your existing tools.

- **Supported Platforms**: PagerDuty, ServiceNow, Slack, Datadog, custom webhooks
- **Automatic Analysis**: AI analysis triggers on incident arrival
- **Live Feed**: Real-time incident status updates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       External Sources                           │
│    ServiceNow │ PagerDuty │ Slack │ Datadog │ Custom Webhooks   │
└────────────────────────────┬────────────────────────────────────┘
                             │ Webhooks
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WardenXT Backend (FastAPI)                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Webhook    │  │    Voice     │  │     Runbook          │  │
│  │   Ingestion  │  │      AI      │  │     Generator        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Google Gemini 3 Flash Integration              │  │
│  │    (Text Analysis │ Audio I/O │ Code Generation)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Predictive  │  │   Anomaly    │  │      Pattern         │  │
│  │  Analytics   │  │   Detection  │  │      Analysis        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               WardenXT Frontend (Next.js 14)                     │
│                                                                  │
│   Landing │ Incidents │ Dashboard │ Predictions │ Voice UI      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** for backend
- **Node.js 18+** for frontend
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/abhishekK50/wardenxt.git
cd wardenxt
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed

# Run the development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📁 Project Structure

```
wardenxt/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   │   ├── incidents.py   # Incident CRUD operations
│   │   │   ├── analysis.py    # AI analysis endpoints
│   │   │   ├── predictions.py # Predictive analytics
│   │   │   ├── voice.py       # Voice AI endpoints
│   │   │   ├── runbooks.py    # Runbook generation
│   │   │   └── webhooks.py    # Webhook ingestion
│   │   ├── core/              # Core business logic
│   │   │   ├── agent/         # Gemini AI agent
│   │   │   ├── pattern_analyzer.py
│   │   │   ├── risk_calculator.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── gemini_predictor.py
│   │   │   └── runbook_generator.py
│   │   ├── models/            # Pydantic models
│   │   └── main.py            # FastAPI application
│   ├── data/                  # Sample incident data
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml           # Railway deployment config
│
├── frontend/                   # Next.js Frontend
│   ├── app/
│   │   ├── components/        # React components
│   │   │   ├── RiskScoreGauge.tsx
│   │   │   ├── PredictionCard.tsx
│   │   │   ├── AnomalyAlert.tsx
│   │   │   ├── RunbookPanel.tsx
│   │   │   ├── VoiceCommander.tsx
│   │   │   └── ...
│   │   ├── incidents/         # Incident pages
│   │   ├── dashboard/         # Predictive dashboard
│   │   ├── page.tsx           # Landing page
│   │   └── layout.tsx         # Root layout
│   ├── lib/
│   │   └── api.ts             # API client
│   ├── package.json
│   └── vercel.json            # Vercel deployment config
│
└── README.md
```

---

## 🔌 API Endpoints

### Incidents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/incidents` | List all incidents |
| GET | `/api/incidents/{id}` | Get incident details |
| POST | `/api/incidents/{id}/status` | Update incident status |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analysis/{id}` | Get AI analysis for incident |
| POST | `/api/analysis/{id}/analyze` | Trigger new AI analysis |

### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predictions/forecast` | Get incident predictions |
| GET | `/api/predictions/risk-score` | Get current risk score |
| GET | `/api/predictions/anomalies` | Get detected anomalies |
| POST | `/api/predictions/simulate` | Run what-if simulation |

### Voice
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/voice/query` | Process voice query |
| GET | `/api/voice/summary/{id}` | Get audio summary |

### Runbooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/runbooks/generate/{id}` | Generate runbook for incident |
| GET | `/api/runbooks/{id}` | Get generated runbook |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/ingest` | Ingest incident from external source |
| POST | `/api/webhooks/pagerduty` | PagerDuty webhook endpoint |
| POST | `/api/webhooks/servicenow` | ServiceNow webhook endpoint |

---

## 🚢 Deployment

### Backend (Railway)

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository
3. Set environment variables:
   - `GEMINI_API_KEY`
   - `CORS_ORIGINS` (your frontend URL)
4. Deploy!

### Frontend (Vercel)

1. Import project on [Vercel](https://vercel.com)
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL` (your backend URL)
3. Deploy!

### Docker

```bash
# Backend
cd backend
docker build -t wardenxt-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key wardenxt-backend

# Frontend
cd frontend
docker build -t wardenxt-frontend .
docker run -p 3000:3000 wardenxt-frontend
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm run test
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| AI Analysis Response Time | < 5 seconds |
| Incident Prediction Accuracy | ~78% |
| Voice Query Processing | < 3 seconds |
| Runbook Generation | < 10 seconds |

---

## 🛣️ Roadmap

- [ ] **Multi-tenant Support**: Organization-level isolation
- [ ] **Custom ML Models**: Train on your incident data
- [ ] **Integration Hub**: More monitoring tool integrations
- [ ] **Mobile App**: iOS/Android companion apps
- [ ] **Slack Bot**: Direct Slack integration

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini 3** - For the incredible AI capabilities
- **FastAPI** - For the excellent Python web framework
- **Next.js** - For the amazing React framework
- **Vercel** & **Railway** - For seamless deployment

---

## 📬 Contact

- **Project Link**: [https://github.com/abhishekK50/wardenxt](https://github.com/abhishekK50/wardenxt)
- **Demo**: [https://wardenxt.vercel.app](https://wardenxt.vercel.app)

---

<p align="center">
  <b>Built with ❤️ for the Google Gemini 3 Hackathon</b>
  <br>
  <i>From reactive firefighting to proactive prevention</i>
</p>
