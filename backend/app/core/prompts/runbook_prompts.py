"""
Runbook Prompts
Specialized prompts for generating incident-specific runbooks using Gemini
"""

from typing import Dict, List, Any


def get_runbook_generation_prompt(
    incident_data: Dict[str, Any],
    focus_area: str = "all"
) -> str:
    """Generate comprehensive runbook creation prompt for Gemini

    Args:
        incident_data: Incident details including logs, metrics, root cause
        focus_area: Focus area - "all", "diagnostic", "remediation", "emergency_rollback"

    Returns:
        Formatted prompt string for Gemini
    """
    incident_id = incident_data.get("incident_id", "UNKNOWN")
    incident_type = incident_data.get("incident_type", "unknown")
    severity = incident_data.get("severity", "P3")
    title = incident_data.get("title", "Unknown Incident")
    root_cause = incident_data.get("root_cause", {})
    services_affected = incident_data.get("services_affected", [])
    duration_minutes = incident_data.get("duration_minutes", 0)

    # Get log snippets (last 20 lines)
    logs = incident_data.get("logs", [])
    log_sample = "\n".join([
        f"[{log.get('timestamp', 'N/A')}] {log.get('level', 'INFO')}: {log.get('message', '')}"
        for log in logs[-20:]
    ])

    # Get metrics
    metrics = incident_data.get("metrics", [])
    metrics_sample = "\n".join([
        f"{m.get('timestamp', 'N/A')}: CPU={m.get('cpu_percent', 0):.1f}% "
        f"Memory={m.get('memory_mb', 0):.0f}MB "
        f"Errors={m.get('error_rate', 0):.2f}"
        for m in metrics[-5:]
    ])

    services_list = ", ".join(services_affected) if services_affected else "Unknown"

    primary_cause = root_cause.get("primary", "Unknown root cause")
    contributing_factors = root_cause.get("contributing_factors", [])

    prompt = f"""You are an expert DevOps/SRE engineer creating an executable runbook for incident resolution.

## INCIDENT DETAILS

**Incident ID:** {incident_id}
**Type:** {incident_type}
**Severity:** {severity}
**Title:** {title}
**Duration:** {duration_minutes} minutes
**Services Affected:** {services_list}

## ROOT CAUSE ANALYSIS

**Primary Cause:** {primary_cause}

**Contributing Factors:**
{chr(10).join([f"- {factor}" for factor in contributing_factors]) if contributing_factors else "- None identified"}

## RECENT LOGS (Last 20 lines)

```
{log_sample if log_sample else "No logs available"}
```

## METRICS (Last 5 data points)

```
{metrics_sample if metrics_sample else "No metrics available"}
```

## YOUR TASK

Generate a complete, executable runbook for this incident. The runbook must contain actual shell commands (bash, kubectl, psql, docker, etc.) that can be executed to diagnose and remediate the issue.

**Focus Area:** {focus_area}

## OUTPUT REQUIREMENTS

Return a JSON object with this exact structure:

```json
{{
  "steps": [
    {{
      "step_number": 1,
      "category": "diagnostic | remediation | verification | rollback",
      "title": "Brief step title",
      "commands": [
        {{
          "command": "actual executable command",
          "description": "What this command does",
          "risk_level": "safe | medium | high",
          "expected_output": "What success looks like",
          "timeout_seconds": 30,
          "requires_approval": true
        }}
      ],
      "prerequisite_steps": [],
      "estimated_duration": "2 minutes"
    }}
  ],
  "warnings": ["Important warnings about execution"],
  "prerequisites": ["Required access/tools"]
}}
```

## COMMAND GUIDELINES

1. **Use Real Commands**: Generate actual executable commands (not pseudo-code)
2. **Safety First**:
   - Add `--dry-run` flags where supported
   - Include verification commands before destructive operations
   - Never use `rm -rf /`, `dd`, `mkfs`, etc.
3. **Be Specific**:
   - Use actual service names from the incident (e.g., "api-service", not "your-app")
   - Reference actual namespaces (e.g., "production", not "your-namespace")
   - Include specific file paths and configurations
4. **Risk Levels**:
   - **safe**: Read-only commands (kubectl get, SELECT, logs)
   - **medium**: State changes that are reversible (restart, scale)
   - **high**: Potentially dangerous (delete, rollback, config changes)

## RUNBOOK STRUCTURE

Include these sections (unless focus_area specifies otherwise):

### 1. DIAGNOSTIC STEPS (2-4 commands)
Commands to verify the issue exists:
- Check pod/container status
- Query databases for connection counts
- Examine logs for error patterns
- Verify metric anomalies

### 2. REMEDIATION STEPS (3-6 commands)
Commands to fix the root cause:
- Restart services with issues
- Scale deployments
- Rollback to previous versions
- Apply configuration fixes
- Clear caches or queues

### 3. VERIFICATION STEPS (2-3 commands)
Commands to confirm the fix worked:
- Re-check pod/container status
- Verify metrics returned to normal
- Test service health endpoints
- Confirm user impact reduced

### 4. ROLLBACK STEPS (2-4 commands)
Emergency recovery if fix fails:
- Revert configuration changes
- Restore previous deployment
- Emergency fallback procedures

## INCIDENT-SPECIFIC GUIDANCE

{get_incident_type_guidance(incident_type)}

## IMPORTANT

- Generate ONLY valid JSON (no markdown, no explanations outside JSON)
- All commands must be copy-paste ready
- Estimate durations realistically (seconds/minutes)
- Add clear warnings for high-risk operations
- Ensure prerequisite_steps reference earlier step numbers correctly

Generate the complete runbook now."""

    return prompt


def get_incident_type_guidance(incident_type: str) -> str:
    """Get incident-type-specific guidance for runbook generation

    Args:
        incident_type: Type of incident

    Returns:
        Guidance text for this incident type
    """
    guidance_map = {
        "database_outage": """
For database outages:
- Check connection pool status: `psql -c "SELECT count(*) FROM pg_stat_activity"`
- Look for long-running queries: `SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle'`
- Consider connection pool restart or scaling
- Verify database replication lag
- Check disk space: `df -h /var/lib/postgresql`
""",
        "memory_leak": """
For memory leaks:
- Check process memory: `ps aux --sort=-%mem | head`
- Get heap dump if Java: `jmap -dump:live,format=b,file=heap.bin <pid>`
- Restart service to reclaim memory
- Consider increasing memory limits
- Check for memory profiling tools
""",
        "high_latency": """
For high latency issues:
- Check network latency: `ping -c 5 <service>`
- Verify DNS resolution: `dig <service-url>`
- Check database query performance: `EXPLAIN ANALYZE <query>`
- Look for resource saturation (CPU, disk I/O)
- Consider scaling horizontally
""",
        "kubernetes_crashloop": """
For Kubernetes CrashLoopBackOff:
- Describe pod: `kubectl describe pod <pod-name> -n <namespace>`
- Check logs: `kubectl logs <pod-name> -n <namespace> --previous`
- Verify ConfigMap/Secret: `kubectl get configmap/secret -n <namespace>`
- Check resource limits: Look for OOMKilled in events
- Consider rolling back deployment: `kubectl rollout undo deployment/<name>`
""",
        "connection_pool_exhaustion": """
For connection pool exhaustion:
- Count active connections: Database-specific query
- Check for connection leaks in application logs
- Restart application to reset pool
- Consider increasing pool size (temporary fix)
- Rollback if issue started with recent deployment
""",
        "disk_full": """
For disk space issues:
- Check disk usage: `df -h`
- Find large files: `du -sh /var/* | sort -h`
- Clean up logs: `journalctl --vacuum-time=2d`
- Remove old docker images: `docker system prune -a`
- Expand volume if cloud-based
""",
        "api_timeout": """
For API timeout issues:
- Check service response time: `curl -o /dev/null -s -w 'Total: %{time_total}s\n' <url>`
- Verify upstream services: Health check endpoints
- Check for database slow queries
- Look for high CPU/memory usage
- Consider circuit breaker activation
""",
        "deployment_failure": """
For deployment failures:
- Check deployment status: `kubectl rollout status deployment/<name>`
- View recent events: `kubectl describe deployment/<name>`
- Rollback immediately: `kubectl rollout undo deployment/<name>`
- Check image availability: `docker pull <image>`
- Verify resource quotas: `kubectl describe resourcequota`
"""
    }

    return guidance_map.get(
        incident_type,
        """
For general incidents:
- Start with diagnostic commands to verify the issue
- Use safe, read-only commands first
- Gradually escalate to remediation steps
- Always include verification steps
- Provide rollback procedures
"""
    )


def get_focused_prompt(incident_data: Dict[str, Any], focus: str) -> str:
    """Generate focused runbook prompt for specific area

    Args:
        incident_data: Incident details
        focus: "diagnostic", "remediation", or "emergency_rollback"

    Returns:
        Focused prompt string
    """
    if focus == "diagnostic":
        return get_diagnostic_only_prompt(incident_data)
    elif focus == "emergency_rollback":
        return get_emergency_rollback_prompt(incident_data)
    else:
        return get_runbook_generation_prompt(incident_data, focus)


def get_diagnostic_only_prompt(incident_data: Dict[str, Any]) -> str:
    """Generate prompt for diagnostic commands only

    Args:
        incident_data: Incident details

    Returns:
        Diagnostic-focused prompt
    """
    base_prompt = get_runbook_generation_prompt(incident_data, "diagnostic")

    # Modify to focus only on diagnostics
    focused = base_prompt.replace(
        "Generate a complete, executable runbook",
        "Generate ONLY diagnostic commands (no remediation or rollback)"
    )
    focused = focused.replace(
        "Include these sections",
        "Include ONLY the diagnostic section"
    )

    return focused


def get_emergency_rollback_prompt(incident_data: Dict[str, Any]) -> str:
    """Generate prompt for emergency rollback only

    Args:
        incident_data: Incident details

    Returns:
        Emergency rollback prompt
    """
    incident_id = incident_data.get("incident_id", "UNKNOWN")
    services_affected = incident_data.get("services_affected", [])
    services_list = ", ".join(services_affected) if services_affected else "Unknown"

    prompt = f"""You are an expert DevOps/SRE engineer.

EMERGENCY SITUATION: Incident {incident_id} is affecting services: {services_list}

Generate IMMEDIATE ROLLBACK COMMANDS to restore service quickly.

Focus on:
1. Rolling back recent deployments
2. Restoring previous configurations
3. Emergency service restart procedures
4. Quick health verification

Return JSON with "steps" array containing 2-4 emergency rollback steps.
Each step must have:
- category: "rollback"
- Actual executable commands
- risk_level, description, expected_output
- estimated_duration

Generate ONLY rollback commands. Make them fast and safe."""

    return prompt
