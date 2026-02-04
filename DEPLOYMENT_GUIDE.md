# WardenXT Deployment Guide

## For Hackathon Submission

This guide covers deploying WardenXT for the Gemini 3 Hackathon submission.

---

## Option 1: Local Demo (Recommended for Video Recording)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/wardenxt.git
cd wardenxt
```

### Step 2: Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-api-key-here

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Step 3: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Run frontend
npm run dev
```

### Step 4: Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Step 5: Login
- Username: `admin`
- Password: `admin123`

---

## Option 2: Cloud Deployment (For Public Demo Link)

### Backend on Railway

1. **Create Railway Account**: https://railway.app

2. **New Project from GitHub**
   - Connect your GitHub repo
   - Select the `backend` folder as root

3. **Environment Variables**
   ```
   GEMINI_API_KEY=your-api-key
   APP_ENV=production
   CORS_ORIGINS=["https://your-frontend.vercel.app"]
   ```

4. **Deploy**
   - Railway auto-detects Python/FastAPI
   - Uses `Procfile` or `railway.toml`

5. **Get URL**: `https://wardenxt-backend.up.railway.app`

### Frontend on Vercel

1. **Create Vercel Account**: https://vercel.com

2. **Import GitHub Repo**
   - Select the `frontend` folder as root

3. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://wardenxt-backend.up.railway.app
   ```

4. **Deploy**
   - Vercel auto-detects Next.js
   - Build command: `npm run build`

5. **Get URL**: `https://wardenxt.vercel.app`

---

## Option 3: Docker Deployment

### Docker Compose (Full Stack)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - APP_ENV=production
      - CORS_ORIGINS=["http://localhost:3000"]
    volumes:
      - ./backend/data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8001
    depends_on:
      - backend
```

### Run with Docker
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

---

## Environment Variables Reference

### Backend (.env)

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional (with defaults)
APP_ENV=development
APP_DEBUG=true
JWT_SECRET_KEY=change-this-in-production
CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=sqlite:///./wardenxt.db

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
ANALYSIS_RATE_LIMIT=10
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Preparing for Public Demo

### 1. Remove Sensitive Data

Check these files have no real secrets:
- [ ] `.env` files not committed (in .gitignore)
- [ ] No hardcoded API keys in code
- [ ] `.env.example` has placeholder values only

### 2. Update README

Ensure README.md includes:
- [ ] Project description
- [ ] Setup instructions
- [ ] Demo credentials (admin/admin123)
- [ ] Screenshots

### 3. Make Repository Public

On GitHub:
1. Go to Settings → General
2. Scroll to "Danger Zone"
3. Click "Change visibility" → Public

### 4. Test Public Access

After deployment:
- [ ] Demo URL loads without login requirement
- [ ] Can login with demo credentials
- [ ] All features work (analysis, voice, runbooks)
- [ ] No CORS errors in console

---

## Demo Data Setup

The demo includes pre-generated incident data in:
```
data-generation/output/
├── INC-2026-0001/
│   ├── summary.json
│   ├── logs.jsonl
│   ├── metrics.jsonl
│   └── timeline.json
├── INC-2026-0002/
└── ...
```

To generate new demo data:
```bash
cd data-generation
python generate_all.py
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check .env file exists
cat .env
```

### Frontend build fails
```bash
# Clear cache
rm -rf node_modules .next
npm install
npm run build
```

### CORS errors
- Ensure `CORS_ORIGINS` in backend includes frontend URL
- Check no trailing slash in URLs

### Gemini API errors
- Verify API key is valid: https://makersuite.google.com/app/apikey
- Check rate limits not exceeded
- Ensure key has access to gemini-3-flash-preview

### Database errors
```bash
# Reset database
rm -f backend/wardenxt.db
# Restart backend (creates fresh DB)
```

---

## Quick Start Commands

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --port 8001 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Test webhook
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{"event_type":"incident.triggered","incident":{"title":"Test Alert","urgency":"high","service":{"name":"API"}}}'
```

---

## Submission Checklist

Before submitting to Devpost:

- [ ] Backend running and healthy (`/health` returns 200)
- [ ] Frontend accessible
- [ ] Login works (admin/admin123)
- [ ] AI analysis completes successfully
- [ ] Demo video recorded and uploaded
- [ ] GitHub repo is PUBLIC
- [ ] All Devpost fields filled

---

*Deployment guide for Gemini 3 Hackathon*
