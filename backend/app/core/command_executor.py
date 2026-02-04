"""
Command Executor
Safely executes runbook commands with validation and safety checks
"""

import re
import subprocess
from typing import Tuple, Optional
from datetime import datetime

from app.models.runbook import RunbookCommand, ExecutionResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Blacklisted command patterns that should NEVER be executed
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',  # Recursive delete from root
    r'rm\s+-rf\s+\*',  # Delete everything
    r'dd\s+if=/dev/zero',  # Wipe disk
    r'dd\s+if=/dev/urandom',  # Wipe disk
    r'mkfs\.',  # Format filesystem
    r'iptables\s+-F',  # Flush firewall rules
    r'shutdown',  # System shutdown
    r'reboot',  # System reboot
    r'halt',  # System halt
    r'init\s+[06]',  # Runlevel shutdown/reboot
    r'chmod\s+-R\s+777',  # Dangerous permissions
    r'chown\s+-R\s+root',  # Change ownership to root
    r'DROP\s+DATABASE',  # Drop entire database
    r'DROP\s+TABLE',  # Drop table (without WHERE)
    r'TRUNCATE',  # Truncate table
    r'DELETE\s+FROM\s+\w+\s*;',  # Delete all rows (no WHERE clause)
    r'UPDATE\s+\w+\s+SET.*\s*;',  # Update all rows (no WHERE clause)
    r'curl.*\|\s*bash',  # Pipe curl to bash (security risk)
    r'wget.*\|\s*sh',  # Pipe wget to shell
    r'eval',  # Eval command (code injection risk)
    r'>+\s*/dev/sd[a-z]',  # Write directly to disk
    r'fdisk',  # Disk partitioning
    r'parted',  # Disk partitioning
]

# Commands that are considered safe (read-only operations)
SAFE_COMMANDS = [
    'kubectl get',
    'kubectl describe',
    'kubectl logs',
    'docker ps',
    'docker inspect',
    'docker logs',
    'systemctl status',
    'journalctl',
    'ps aux',
    'top',
    'htop',
    'netstat',
    'ss',
    'lsof',
    'df -h',
    'du -sh',
    'free -m',
    'uptime',
    'who',
    'last',
    'cat',
    'tail',
    'head',
    'less',
    'grep',
    'awk',
    'sed',
    'curl',
    'wget',
    'ping',
    'dig',
    'nslookup',
    'traceroute',
    'telnet',
    'nc',
    'SELECT',  # SQL SELECT (read-only)
    'SHOW',  # SQL SHOW
    'DESCRIBE',  # SQL DESCRIBE
    'EXPLAIN',  # SQL EXPLAIN
]


def validate_command_safety(command: str) -> Tuple[bool, str, str]:
    """Validate command for safety before execution

    Args:
        command: Command string to validate

    Returns:
        Tuple of (is_safe, risk_level, reason)
        - is_safe: Whether command is safe to execute
        - risk_level: "safe", "medium", "high"
        - reason: Explanation of safety assessment
    """
    try:
        command_lower = command.lower().strip()

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(
                    "dangerous_command_blocked",
                    extra_fields={"command": command, "pattern": pattern}
                )
                return (
                    False,
                    "high",
                    f"Command matches dangerous pattern: {pattern}. This command is blocked for safety."
                )

        # Check if command starts with a safe prefix
        is_safe_command = any(command_lower.startswith(safe_cmd.lower()) for safe_cmd in SAFE_COMMANDS)

        if is_safe_command:
            return (True, "safe", "Command is read-only and considered safe")

        # Check for commands that modify state but are acceptable with approval
        medium_risk_patterns = [
            r'kubectl apply',
            r'kubectl delete',
            r'kubectl scale',
            r'kubectl patch',
            r'kubectl rollout',
            r'systemctl restart',
            r'systemctl stop',
            r'systemctl start',
            r'docker restart',
            r'docker stop',
            r'docker start',
            r'git',
            r'npm',
            r'yarn',
            r'pip install',
            r'apt-get',
            r'yum',
            r'INSERT INTO',
            r'UPDATE.*WHERE',  # UPDATE with WHERE clause
            r'DELETE.*WHERE',  # DELETE with WHERE clause
        ]

        for pattern in medium_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return (
                    True,
                    "medium",
                    f"Command modifies system state. Requires approval."
                )

        # High-risk commands that need explicit confirmation
        high_risk_patterns = [
            r'kubectl delete deployment',
            r'kubectl delete service',
            r'kubectl delete namespace',
            r'rm ',
            r'mv ',
            r'chmod',
            r'chown',
            r'ALTER TABLE',
            r'CREATE DATABASE',
            r'DROP ',
        ]

        for pattern in high_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return (
                    True,
                    "high",
                    f"High-risk command that requires explicit confirmation (type 'EXECUTE')"
                )

        # Default: medium risk for unknown commands
        return (
            True,
            "medium",
            "Command not recognized as safe. Requires approval before execution."
        )

    except Exception as e:
        logger.error(
            "command_validation_failed",
            extra_fields={"command": command, "error": str(e)},
            exc_info=True
        )
        return (False, "high", f"Validation error: {str(e)}")


def execute_command(
    command: RunbookCommand,
    dry_run: bool = True,
    executed_by: str = "system"
) -> ExecutionResult:
    """Execute a runbook command

    Args:
        command: Command to execute
        dry_run: If True, simulates execution without running command
        executed_by: User or system executing the command

    Returns:
        ExecutionResult with output and status
    """
    start_time = datetime.utcnow()

    try:
        # Validate command safety
        is_safe, risk_level, safety_reason = validate_command_safety(command.command)

        if not is_safe:
            logger.error(
                "unsafe_command_blocked",
                extra_fields={"command": command.command, "reason": safety_reason}
            )
            return ExecutionResult(
                step_number=0,
                command=command.command,
                success=False,
                output="",
                error=f"Command blocked for safety: {safety_reason}",
                executed_at=datetime.utcnow().isoformat(),
                executed_by=executed_by,
                dry_run=dry_run,
                duration_seconds=0.0
            )

        # For dry-run, generate simulated output
        if dry_run:
            logger.info(
                "command_dry_run",
                extra_fields={
                    "command": command.command,
                    "risk_level": risk_level,
                    "executed_by": executed_by
                }
            )

            simulated_output = generate_simulated_output(command)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return ExecutionResult(
                step_number=0,
                command=command.command,
                success=True,
                output=simulated_output,
                error=None,
                executed_at=start_time.isoformat(),
                executed_by=executed_by,
                dry_run=True,
                duration_seconds=duration
            )

        # ACTUAL EXECUTION (disabled for hackathon demo - would be enabled in production)
        # In production, this would execute the command using subprocess
        logger.warning(
            "actual_execution_disabled",
            extra_fields={"command": command.command, "reason": "Hackathon demo mode"}
        )

        # For hackathon, treat all non-dry-run as dry-run with a warning
        simulated_output = generate_simulated_output(command)
        simulated_output = f"[DEMO MODE] Command would execute:\n{simulated_output}"

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return ExecutionResult(
            step_number=0,
            command=command.command,
            success=True,
            output=simulated_output,
            error=None,
            executed_at=start_time.isoformat(),
            executed_by=executed_by,
            dry_run=True,  # Always dry-run in demo mode
            duration_seconds=duration
        )

    except Exception as e:
        logger.error(
            "command_execution_failed",
            extra_fields={
                "command": command.command,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return ExecutionResult(
            step_number=0,
            command=command.command,
            success=False,
            output="",
            error=str(e),
            executed_at=start_time.isoformat(),
            executed_by=executed_by,
            dry_run=dry_run,
            duration_seconds=duration
        )


def generate_simulated_output(command: RunbookCommand) -> str:
    """Generate realistic simulated output for dry-run mode

    Args:
        command: Command to simulate

    Returns:
        Simulated command output
    """
    cmd = command.command.lower()

    # Kubernetes commands
    if 'kubectl get pods' in cmd:
        return """NAME                          READY   STATUS    RESTARTS   AGE
api-service-7d4b8f9c6-abc12   1/1     Running   0          5m
api-service-7d4b8f9c6-def34   1/1     Running   0          5m
api-service-7d4b8f9c6-ghi56   1/1     Running   0          5m"""

    elif 'kubectl describe pod' in cmd:
        return """Name:         api-service-7d4b8f9c6-abc12
Namespace:    production
Status:       Running
IP:           10.244.0.15
Containers:
  api:
    Image:          api-service:v3.2.1
    State:          Running
      Started:      2026-01-30 10:15:30
Events:           <none>"""

    elif 'kubectl logs' in cmd:
        return """2026-01-30 10:20:15 INFO Starting API server on port 8000
2026-01-30 10:20:16 INFO Connected to database: postgresql://...
2026-01-30 10:20:17 INFO Health check endpoint ready
2026-01-30 10:20:18 INFO Server ready to accept requests"""

    elif 'kubectl rollout undo' in cmd:
        return "deployment.apps/api-service rolled back"

    elif 'kubectl scale' in cmd:
        return "deployment.apps/api-service scaled"

    elif 'kubectl patch' in cmd:
        return "configmap/api-config patched"

    # Docker commands
    elif 'docker ps' in cmd:
        return """CONTAINER ID   IMAGE               STATUS         PORTS
a1b2c3d4e5f6   api-service:latest  Up 2 hours     0.0.0.0:8000->8000/tcp"""

    elif 'docker logs' in cmd:
        return """[2026-01-30 10:15:00] INFO: Starting container
[2026-01-30 10:15:01] INFO: Application ready"""

    # Database commands
    elif 'psql' in cmd and 'SELECT count' in cmd:
        if 'pg_stat_activity' in cmd:
            return """ count
-------
    45
(1 row)"""
        return """ count
-------
  1234
(1 row)"""

    elif 'psql' in cmd and 'SELECT' in cmd:
        return """ id | status | created_at
----+--------+------------
  1 | active | 2026-01-30
(1 row)"""

    # System commands
    elif 'systemctl status' in cmd:
        return """● api-service.service - API Service
   Loaded: loaded (/lib/systemd/system/api-service.service; enabled)
   Active: active (running) since Wed 2026-01-30 10:00:00 UTC; 2h ago"""

    elif 'systemctl restart' in cmd:
        return "Service restarted successfully"

    elif 'ps aux' in cmd:
        return """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
www-data  1234  2.5 15.3 987654 654321 ?     Ssl  10:00   0:45 /usr/bin/python3 app.py"""

    # Network commands
    elif 'ping' in cmd:
        return """PING api.example.com (1.2.3.4) 56(84) bytes of data.
64 bytes from 1.2.3.4: icmp_seq=1 ttl=64 time=0.5 ms
--- api.example.com ping statistics ---
1 packets transmitted, 1 received, 0% packet loss"""

    elif 'curl' in cmd:
        if 'health' in cmd:
            return '{"status": "healthy", "version": "3.2.1"}'
        return '{"success": true}'

    elif 'dig' in cmd:
        return """api.example.com.  300  IN  A  1.2.3.4"""

    # Default
    if command.expected_output:
        return command.expected_output

    return f"Command executed successfully:\n{command.command}\n\n[Simulated output for demo]"


def execute_command_real(command: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """Execute command using subprocess (production mode only)

    NOTE: This is disabled for hackathon demo. Would be enabled in production.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    # DISABLED FOR DEMO
    raise NotImplementedError(
        "Real command execution is disabled for hackathon demo. "
        "Use dry_run=True for simulated execution."
    )

    # Production implementation would be:
    # try:
    #     result = subprocess.run(
    #         command,
    #         shell=True,
    #         capture_output=True,
    #         text=True,
    #         timeout=timeout
    #     )
    #     return (result.returncode == 0, result.stdout, result.stderr)
    # except subprocess.TimeoutExpired:
    #     return (False, "", f"Command timeout after {timeout} seconds")
    # except Exception as e:
    #     return (False, "", str(e))
