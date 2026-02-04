# WardenXT Module 3 - Auto-Runbook Generation Testing Guide

## Overview

Module 3 implements automated runbook generation using Google Gemini AI. It creates executable remediation scripts, diagnostic procedures, rollback instructions, and verification steps for incident resolution.

## Prerequisites

Before testing:

1. **Backend Running**: `cd backend && uvicorn app.main:app --reload --port 8001`
2. **Frontend Running**: `cd frontend && npm run dev`
3. **Environment Variables Set**:
   - `GEMINI_API_KEY` in `backend/.env`
   - `NEXT_PUBLIC_API_URL=http://localhost:8001` in `frontend/.env.local`

## Features Implemented

### 1. Runbook Generation

**Endpoint**: `POST /api/runbooks/{incident_id}/generate`

Generates complete runbooks with:
- **Diagnostic Steps**: Commands to verify the issue exists
- **Remediation Steps**: Commands to fix the root cause
- **Verification Steps**: Commands to confirm the fix worked
- **Rollback Steps**: Emergency recovery procedures

### 2. Command Safety Validation

All commands are validated against:
- **Blacklist**: Dangerous patterns (rm -rf /, dd, mkfs, etc.)
- **Risk Levels**: safe, medium, high
- **Approval Requirements**: High-risk commands require typing "EXECUTE"

### 3. Command Execution

**Endpoint**: `POST /api/runbooks/{incident_id}/execute-step`

Features:
- **Dry Run Mode**: Simulates execution without running commands
- **Real Execution**: Requires explicit confirmation (disabled in demo)
- **Execution History**: All executions are logged

### 4. Frontend Components

- **RunbookPanel**: Accordion-style step display with syntax highlighting
- **CommandExecutionModal**: Safe execution with confirmation flows
- **ExecutionHistory**: Timeline of executed commands
- **RunbookExport**: Export runbook as Markdown

## Testing Steps

### Test 1: Generate Runbook via API

```bash
# Generate runbook for existing incident
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/generate \
  -H "Content-Type: application/json" \
  -d '{"focus_area": "all", "max_steps": 10}'
```

**Expected Response**:
```json
{
  "incident_id": "INC-2026-0002",
  "generated_at": "2026-01-30T...",
  "incident_type": "connection_pool_exhaustion",
  "severity": "P1",
  "steps": [
    {
      "step_number": 1,
      "category": "diagnostic",
      "title": "Verify Connection Pool Status",
      "commands": [...],
      "estimated_duration": "1 minute"
    }
  ],
  "total_steps": 4,
  "estimated_total_time": "5 minutes",
  "warnings": [...],
  "prerequisites": [...]
}
```

### Test 2: Get Cached Runbook

```bash
curl http://localhost:8001/api/runbooks/INC-2026-0002
```

### Test 3: Execute Step (Dry Run)

```bash
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/execute-step \
  -H "Content-Type: application/json" \
  -d '{
    "step_number": 1,
    "command_index": 0,
    "dry_run": true,
    "executed_by": "tester"
  }'
```

**Expected Response**:
```json
{
  "step_number": 1,
  "command_index": 0,
  "command": "kubectl get pods -n production | grep api-service",
  "success": true,
  "output": "NAME                          READY   STATUS    RESTARTS...",
  "executed_at": "2026-01-30T...",
  "executed_by": "tester",
  "dry_run": true,
  "duration_seconds": 0.05
}
```

### Test 4: Execute High-Risk Command

```bash
# Without confirmation - should fail
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/execute-step \
  -H "Content-Type: application/json" \
  -d '{
    "step_number": 2,
    "command_index": 0,
    "dry_run": false,
    "executed_by": "tester"
  }'

# With confirmation
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/execute-step \
  -H "Content-Type: application/json" \
  -d '{
    "step_number": 2,
    "command_index": 0,
    "dry_run": false,
    "confirmation_text": "EXECUTE",
    "executed_by": "tester"
  }'
```

### Test 5: Get Execution History

```bash
curl http://localhost:8001/api/runbooks/INC-2026-0002/history
```

**Expected Response**:
```json
{
  "incident_id": "INC-2026-0002",
  "executions_count": 3,
  "history": [...],
  "successful_count": 2,
  "failed_count": 1,
  "dry_run_count": 2
}
```

### Test 6: Validate Runbook

```bash
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/validate
```

### Test 7: Clear Runbook Cache

```bash
curl -X DELETE http://localhost:8001/api/runbooks/INC-2026-0002
```

### Test 8: List All Cached Runbooks

```bash
curl http://localhost:8001/api/runbooks/
```

## Frontend Testing

### Test 9: Generate Runbook via UI

1. Navigate to `http://localhost:3000/incidents`
2. Click on any incident to open detail page
3. Click "Generate Runbook" button (orange gradient)
4. Wait for generation (< 5 seconds)
5. Verify:
   - Button changes to "Runbook Ready" with checkmark
   - RunbookPanel appears below AI Analysis section
   - Steps are organized by category (diagnostic, remediation, etc.)
   - Each step shows commands with syntax highlighting

### Test 10: Expand/Collapse Steps

1. Click on step header to expand
2. Verify commands are visible with:
   - Copy button
   - Execute button
   - Risk level badge
   - Expected output
3. Use "Expand All" / "Collapse All" buttons

### Test 11: Copy Command

1. Expand any step
2. Click "Copy" button on a command
3. Verify command is copied to clipboard
4. Icon should briefly turn green

### Test 12: Execute Command (Dry Run)

1. Click "Execute" on any command
2. CommandExecutionModal opens
3. Click "Dry Run" button
4. Verify:
   - Loading spinner while executing
   - Success message with output
   - Output shows simulated results
   - "DRY RUN" badge visible

### Test 13: Execute High-Risk Command

1. Find a command with "Risk: HIGH" badge
2. Click "Execute"
3. Modal shows red warning
4. Click "Execute for Real"
5. Verify:
   - Confirmation input appears
   - Type "EXECUTE" to enable button
   - Execution proceeds

### Test 14: Export Runbook

1. Click "Export" button in RunbookPanel header
2. Verify:
   - Markdown file downloads
   - File named `runbook-{incident_id}.md`
   - Contains all steps with commands
   - Includes checkboxes for tracking

### Test 15: View Execution History

1. Execute a few commands
2. Scroll to "Execution History" section
3. Verify:
   - Stats show correct counts
   - Timeline shows all executions
   - Filter buttons work (All/Successful/Failed)
   - Click to expand shows output

## Safety Validation Tests

### Test 16: Blocked Dangerous Commands

The following patterns should be blocked:

```bash
# These should return errors
rm -rf /
dd if=/dev/zero of=/dev/sda
mkfs.ext4 /dev/sda1
iptables -F
shutdown -h now
chmod -R 777 /
```

### Test 17: Safe Commands Pass

```bash
# These should be allowed (safe level)
kubectl get pods
docker ps
ps aux
tail -f /var/log/syslog
curl http://localhost/health
```

## Integration Tests

### Test 18: Webhook → Runbook Integration

1. Send webhook to create incident:
```bash
curl -X POST http://localhost:8001/api/webhooks/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incident.triggered",
    "incident": {
      "id": "PD-TEST-123",
      "title": "Database Connection Timeout",
      "urgency": "high",
      "status": "triggered",
      "service": {"name": "PostgreSQL"}
    }
  }'
```

2. Navigate to the new incident in UI
3. Generate runbook
4. Verify runbook is customized for database issues

### Test 19: Analysis → Runbook Correlation

1. Run AI Analysis on incident first
2. Then generate runbook
3. Verify runbook incorporates analysis insights

## Performance Tests

### Test 20: Generation Speed

1. Time runbook generation
2. Should complete in < 5 seconds
3. Multiple incident types tested

### Test 21: Caching

1. Generate runbook
2. Request same runbook again
3. Second request should be instant (cached)
4. Cache expires after 1 hour

## Error Handling Tests

### Test 22: Invalid Incident ID

```bash
curl -X POST http://localhost:8001/api/runbooks/INVALID-ID/generate
```

**Expected**: 404 Not Found

### Test 23: Invalid Step Number

```bash
curl -X POST http://localhost:8001/api/runbooks/INC-2026-0002/execute-step \
  -H "Content-Type: application/json" \
  -d '{"step_number": 999, "dry_run": true}'
```

**Expected**: 404 Not Found

### Test 24: Missing Runbook

```bash
curl http://localhost:8001/api/runbooks/INC-NEVER-GENERATED
```

**Expected**: 404 "No runbook found. Generate one first."

## Demo Scenario

For hackathon demonstration:

1. **Open incident detail page** (INC-2026-0002)
2. **Click "Generate Runbook"** - show generation progress
3. **Runbook appears** with 4 steps
4. **Expand first diagnostic step** - show kubectl commands
5. **Click "Copy"** on a command
6. **Expand remediation step** - show rollback command
7. **Click "Execute"** → Modal appears
8. **Show warning** for medium/high risk
9. **Click "Dry Run"** - show simulated output
10. **Type "EXECUTE"** for high-risk command
11. **Show execution output** in real-time
12. **Step marked completed** (green checkmark)
13. **Click "Export"** - download Markdown
14. **Show downloaded file** in editor

## Success Criteria

Module 3 is complete when:

- ✅ "Generate Runbook" button appears on incident detail page
- ✅ Clicking button generates runbook in < 5 seconds
- ✅ Runbook contains diagnostic, remediation, verification, rollback steps
- ✅ Commands are actual executable bash/kubectl/psql commands
- ✅ Each command has description, risk level, expected output
- ✅ Can copy commands to clipboard
- ✅ Can execute commands with confirmation modal
- ✅ Execution history is logged
- ✅ Can export runbook as Markdown
- ✅ High-risk commands require typing "EXECUTE"
- ✅ Commands are validated before generation
- ✅ Runbook is cached and reusable

## Troubleshooting

### Issue: Runbook Generation Fails

**Check**:
- GEMINI_API_KEY is valid
- Backend logs for errors
- Incident exists and has data

### Issue: Commands Not Showing

**Check**:
- Frontend console for errors
- API response has `steps` array
- RunbookPanel component imported

### Issue: Execution Always Fails

**Check**:
- Command validation logs
- Command not on blacklist
- Proper JSON formatting

### Issue: Export Not Working

**Check**:
- Browser allows downloads
- No ad blocker interference
- Check console for errors

## Files Created for Module 3

**Backend**:
- [backend/app/models/runbook.py](backend/app/models/runbook.py) - Runbook data models
- [backend/app/core/command_executor.py](backend/app/core/command_executor.py) - Command execution and safety
- [backend/app/core/runbook_generator.py](backend/app/core/runbook_generator.py) - Gemini-powered generation
- [backend/app/core/prompts/runbook_prompts.py](backend/app/core/prompts/runbook_prompts.py) - Specialized prompts
- [backend/app/api/runbooks.py](backend/app/api/runbooks.py) - API endpoints

**Frontend**:
- [frontend/app/components/RunbookPanel.tsx](frontend/app/components/RunbookPanel.tsx) - Main runbook UI
- [frontend/app/components/CommandExecutionModal.tsx](frontend/app/components/CommandExecutionModal.tsx) - Execution modal
- [frontend/app/components/RunbookExport.tsx](frontend/app/components/RunbookExport.tsx) - Markdown export
- [frontend/app/components/ExecutionHistory.tsx](frontend/app/components/ExecutionHistory.tsx) - History timeline
- [frontend/lib/api.ts](frontend/lib/api.ts) - Updated with runbook methods
- [frontend/app/incidents/[id]/page.tsx](frontend/app/incidents/[id]/page.tsx) - Updated with runbook integration

## Next Steps

After Module 3:
1. Test all three modules together (Webhooks + Voice + Runbooks)
2. Create comprehensive demo video
3. Prepare hackathon presentation
4. Deploy to production environment
