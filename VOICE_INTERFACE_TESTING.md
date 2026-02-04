# WardenXT Voice Interface - Testing Guide

## Overview

Module 2 implements a comprehensive voice interface powered by Google's Gemini 2.0 Flash model with multimodal audio capabilities. This guide covers end-to-end testing of all voice features.

## Prerequisites

Before testing, ensure:

1. **Backend Running**: `cd backend && uvicorn app.main:app --reload --port 8001`
2. **Frontend Running**: `cd frontend && npm run dev`
3. **Environment Variables Set**:
   - `GEMINI_API_KEY` in `backend/.env`
   - `NEXT_PUBLIC_API_URL=http://localhost:8001` in `frontend/.env.local`
4. **Microphone Access**: Browser must have microphone permissions
5. **Speaker/Headphones**: For audio playback testing

## Features Implemented

### 1. Voice Commander (Floating Microphone Button)

**Location**: Bottom-right corner of all dashboard pages

**Functionality**:
- Click to start recording (max 5 seconds)
- Auto-stops after 5 seconds or click again to stop early
- Sends audio to Gemini for transcription and command parsing
- Displays response in popup with optional audio playback
- Shows clickable incident IDs in responses

**Testing Steps**:

#### Test 1: Basic Voice Query
1. Navigate to dashboard (`http://localhost:3000/incidents`)
2. Click the microphone button (purple/pink gradient)
3. Wait for "Listening..." indicator
4. Say: "What are my active incidents?"
5. Verify:
   - Microphone button changes to "Recording..." with waveform animation
   - After 5 seconds, shows "Processing..." state
   - Popup appears with:
     - Transcript of your query
     - AI response with incident information
     - Play button for audio response
   - Incident IDs in response are clickable and navigate to detail page

#### Test 2: Severity-Specific Query
1. Click microphone button
2. Say: "Show me all P0 incidents"
3. Verify:
   - Response filters and shows only P0 incidents
   - Lists incident IDs and details
   - Audio summary plays when clicking play button

#### Test 3: Status Query
1. Click microphone button
2. Say: "What incidents are currently being investigated?"
3. Verify:
   - Response shows count of investigating incidents
   - Breaks down by severity (P0, P1, P2)
   - Lists up to 5 incident IDs

#### Test 4: Incident Summarization
1. Click microphone button
2. Say: "Summarize all incidents"
3. Verify:
   - Response includes total count
   - Breaks down by severity (P0, P1, P2, P3)
   - Shows count by status (investigating, resolved)

#### Test 5: Analysis Command
1. Click microphone button
2. Say: "Analyze incident zero zero zero one" (or any valid incident ID)
3. Verify:
   - Response confirms analysis is starting
   - Mentions 15-30 second duration
   - Explains that Gemini AI will analyze logs, metrics, and timeline

#### Test 6: Help Command
1. Click "?" button next to microphone
2. Verify help modal shows:
   - Available voice commands
   - Example phrases for each command type
   - Command categories (Query, Analysis, Status, Summarization)

### 2. Incident Card Audio Summaries

**Location**: Dashboard incident cards (`/incidents`)

**Functionality**:
- Each incident card has a speaker icon
- Click to play audio summary of that specific incident
- Shows loading spinner during playback
- Auto-stops when complete

**Testing Steps**:

#### Test 7: Play Individual Incident Summary
1. Navigate to incidents dashboard
2. Locate any incident card
3. Click the speaker icon (Volume2) on the right side of the card
4. Verify:
   - Icon changes to spinning loader
   - Audio plays summarizing the incident
   - Includes: incident ID, severity, services affected, status
   - Icon returns to speaker when finished
   - Click during playback to stop early

#### Test 8: Multiple Incident Playback
1. Play audio for one incident
2. While playing, click speaker on a different incident
3. Verify:
   - First audio stops
   - Second audio starts playing
   - Only one audio plays at a time

### 3. Incident Detail Page Audio Summary

**Location**: Individual incident detail page (`/incidents/[id]`)

**Functionality**:
- "Listen to Summary" button in header
- Plays comprehensive audio summary of the incident
- Can be stopped mid-playback

**Testing Steps**:

#### Test 9: Detailed Incident Audio Summary
1. Navigate to any incident detail page
2. Click "Listen to Summary" button (purple gradient, left of "AI Analysis")
3. Verify:
   - Button changes to "Stop Audio" with VolumeX icon
   - Audio plays with comprehensive incident summary
   - Summary includes:
     - Incident ID and severity
     - Services affected
     - Root cause summary
     - Duration and impact
     - Current status
   - Button returns to "Listen to Summary" when finished

#### Test 10: Stop Audio Mid-Playback
1. Click "Listen to Summary"
2. While audio is playing, click "Stop Audio"
3. Verify:
   - Audio stops immediately
   - Button returns to "Listen to Summary" state
   - Can click again to restart from beginning

### 4. Voice API Endpoints

**Testing with curl/Postman**:

#### Test 11: Voice Query API
```bash
# Record a .webm audio file using browser MediaRecorder
# Then test the endpoint:
curl -X POST http://localhost:8001/api/voice/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@test_query.webm"
```

Expected response:
```json
{
  "transcript": "What are my active incidents?",
  "response_text": "There are 3 incidents. The most critical is INC-2026-0001...",
  "audio_base64": "base64_encoded_audio_response",
  "action_taken": null,
  "incident_ids": ["INC-2026-0001", "INC-2026-0002"],
  "confidence": 0.95
}
```

#### Test 12: Speak Incident Summary API
```bash
curl -X GET http://localhost:8001/api/voice/speak/INC-2026-0001 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output incident_summary.wav
```

Expected result: `incident_summary.wav` file with audio summary

#### Test 13: Voice Capabilities API
```bash
curl -X GET http://localhost:8001/api/voice/capabilities \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:
```json
{
  "capabilities": [
    {
      "command": "query",
      "examples": ["What are my incidents?", "Show me P0 incidents"],
      "description": "Query and filter incidents",
      "parameters": ["severity", "status", "time_range"]
    },
    ...
  ],
  "total_commands": 4
}
```

## Supported Voice Commands

### Query Commands
- "What are my incidents?"
- "Show me all P0 incidents"
- "What P1 incidents do I have?"
- "List all active incidents"
- "Show me incidents being investigated"

### Analysis Commands
- "Analyze incident zero zero zero one"
- "Analyze incident INC-2026-0001"
- "Run analysis on the latest incident"

### Status Commands
- "What's the current status?"
- "What incidents are being investigated?"
- "Show me active incidents"

### Summarization Commands
- "Summarize all incidents"
- "Give me an overview"
- "What's the incident summary?"

## Expected Voice Responses

The AI will respond naturally using Gemini's voice synthesis. Example responses:

- **Query Response**: "There are 3 incidents. The most critical is INC-2026-0001, a P0 database outage affecting 5 services. Status: INVESTIGATING."

- **Analysis Response**: "I'm starting analysis of incident INC-2026-0001. This will take about 15 to 30 seconds. I'll use Gemini AI to analyze logs, metrics, and timeline data."

- **Status Response**: "There are 2 incidents currently being investigated. 1 is P0, 1 is P1, and 0 are P2 priority."

- **Summary Response**: "You have 4 total incidents. 1 is P0, 2 are P1, and 1 is P2. 2 are currently being investigated, and 2 have been resolved."

## Integration Testing

### Test 14: Webhook + Voice Integration
1. Send a webhook to create a new incident:
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "test-123",
      "title": "Test Database Outage",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "Database Service"}
    }
  }'
```

2. Wait 5 seconds for auto-analysis to complete
3. Click microphone and say: "What are my latest incidents?"
4. Verify response includes the newly created webhook incident
5. Click speaker icon on the webhook incident card
6. Verify audio summary plays

### Test 15: Voice → Detail Page → Audio Summary
1. Click microphone
2. Say: "What are my P0 incidents?"
3. Click on an incident ID in the response popup
4. Verify navigation to incident detail page
5. Click "Listen to Summary" button
6. Verify audio plays with full incident summary

## Troubleshooting

### Issue: Microphone Not Working
- **Check**: Browser permissions for microphone access
- **Solution**: Go to browser settings → Privacy → Microphone → Allow for localhost:3000

### Issue: No Audio Playback
- **Check**: Speaker/headphone connection
- **Check**: Browser console for audio playback errors
- **Solution**: Verify `GEMINI_API_KEY` is set and valid

### Issue: "Failed to load audio summary"
- **Check**: Backend server is running on port 8001
- **Check**: Incident exists (valid incident ID)
- **Solution**: Verify API connection in browser DevTools Network tab

### Issue: Voice Commands Not Recognized
- **Check**: Speaking clearly and not too fast
- **Check**: Microphone quality and background noise
- **Solution**: Try using exact command phrases from documentation

### Issue: CORS Errors
- **Check**: `NEXT_PUBLIC_API_URL` matches backend port
- **Check**: Backend CORS settings in `backend/.env`
- **Solution**: Ensure both frontend and backend are running

## Performance Testing

### Latency Benchmarks
- **Voice Query**: < 3 seconds (transcription + processing + TTS)
- **Incident Audio Summary**: < 2 seconds (first audio byte)
- **Voice Command Recognition**: < 1 second (transcription only)

### Audio Quality
- **Recording**: WebM/Opus codec at 48kHz
- **Playback**: WAV/PCM at 24kHz (Gemini output)
- **File Size**: ~50KB per 5-second recording

## Success Criteria

Module 2 is considered fully functional when:

✅ Voice Commander records and processes audio queries
✅ Gemini successfully transcribes voice input
✅ Natural language commands are parsed and executed
✅ Audio responses play with Gemini voice synthesis
✅ Incident IDs in responses are clickable
✅ Speaker icons play individual incident summaries
✅ Detail page "Listen to Summary" button works
✅ Voice API endpoints return correct responses
✅ Integration with webhook incidents works
✅ Error handling shows appropriate toast messages

## Demo Script

For hackathon demonstration:

1. **Start**: Show dashboard with multiple incidents
2. **Voice Query**: Click microphone, say "What are my P0 incidents?"
3. **Show Response**: Point out transcript accuracy and natural language response
4. **Play Audio**: Click play button to hear Gemini's voice response
5. **Click Incident**: Click an incident ID in the popup to navigate
6. **Audio Summary**: On detail page, click "Listen to Summary"
7. **Webhook Demo**: Send PagerDuty webhook, wait for auto-analysis
8. **Voice Follow-up**: Ask "What are my latest incidents?" to show webhook integration
9. **Card Audio**: Click speaker icon on incident card
10. **Conclude**: Show help modal with available commands

## Next Steps

After testing Module 2:
- Test Module 1 (Webhooks) integration
- Verify auto-analysis triggered by webhooks
- Test real PagerDuty/Slack webhook payloads
- Load test with multiple concurrent voice queries
- Test on different browsers (Chrome, Firefox, Safari)
- Test with various accents and speech patterns
- Deploy to production environment
- Add metrics and monitoring for voice usage

## Notes

- Voice interface requires HTTPS in production (browser security requirement)
- Gemini 2.0 Flash supports multiple voices (Puck, Charon, Kore, Fenrir, Aoede)
- Current implementation uses "Puck" voice (configurable)
- Audio format detection supports WAV, MP3, OGG, WebM
- Maximum audio file size: 10MB
- Auto-stop after 5 seconds prevents excessive recording
