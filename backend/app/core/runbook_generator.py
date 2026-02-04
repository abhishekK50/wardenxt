"""
Runbook Generator
Generates executable runbooks for incident remediation using Gemini AI
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.incident import Incident
from app.models.runbook import (
    Runbook,
    RunbookStep,
    RunbookCommand,
    RunbookValidationResult
)
from app.core.agent.gemini_client import get_gemini_client
from app.core.prompts.runbook_prompts import (
    get_runbook_generation_prompt,
    get_focused_prompt
)
from app.core.command_executor import validate_command_safety
from app.core.logging import get_logger

logger = get_logger(__name__)


class RunbookGenerator:
    """Generates executable runbooks using Gemini AI"""

    def __init__(self):
        self.gemini_client = get_gemini_client()

    async def generate_runbook(
        self,
        incident: Incident,
        focus_area: str = "all",
        max_steps: int = 10
    ) -> Runbook:
        """Generate complete runbook for incident remediation

        Args:
            incident: Incident to generate runbook for
            focus_area: Focus area - "all", "diagnostic", "remediation", "emergency_rollback"
            max_steps: Maximum number of steps to generate

        Returns:
            Generated Runbook

        Raises:
            ValueError: If runbook generation fails
        """
        try:
            logger.info(
                "runbook_generation_started",
                extra_fields={
                    "incident_id": incident.summary.incident_id,
                    "incident_type": incident.summary.incident_type,
                    "focus_area": focus_area
                }
            )

            # Prepare incident data for prompt
            incident_data = self._prepare_incident_data(incident)

            # Get appropriate prompt
            if focus_area in ["diagnostic", "emergency_rollback"]:
                prompt = get_focused_prompt(incident_data, focus_area)
            else:
                prompt = get_runbook_generation_prompt(incident_data, focus_area)

            # Generate runbook with Gemini
            logger.info("calling_gemini_for_runbook", extra_fields={"prompt_length": len(prompt)})

            response = await self.gemini_client.generate_content_async(prompt)
            response_text = response.text.strip()

            # Extract JSON from response (Gemini might wrap in markdown)
            runbook_data = self._extract_json_from_response(response_text)

            # Validate and construct runbook
            runbook = self._construct_runbook(
                incident.summary.incident_id,
                incident.summary.incident_type,
                incident.summary.severity,
                runbook_data,
                max_steps
            )

            # Validate runbook safety
            validation = self.validate_runbook(runbook)
            if not validation.is_valid:
                logger.warning(
                    "runbook_validation_failed",
                    extra_fields={
                        "incident_id": incident.summary.incident_id,
                        "issues": validation.issues
                    }
                )
                # Add validation warnings to runbook
                runbook.warnings.extend(validation.issues)

            logger.info(
                "runbook_generation_completed",
                extra_fields={
                    "incident_id": incident.summary.incident_id,
                    "steps_count": runbook.total_steps,
                    "estimated_time": runbook.estimated_total_time
                }
            )

            return runbook

        except Exception as e:
            logger.error(
                "runbook_generation_failed",
                extra_fields={
                    "incident_id": incident.summary.incident_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise ValueError(f"Failed to generate runbook: {str(e)}")

    def _prepare_incident_data(self, incident: Incident) -> Dict[str, Any]:
        """Prepare incident data for prompt generation

        Args:
            incident: Incident object

        Returns:
            Dictionary with incident data
        """
        return {
            "incident_id": incident.summary.incident_id,
            "incident_type": incident.summary.incident_type,
            "severity": incident.summary.severity,
            "title": incident.summary.title,
            "duration_minutes": incident.summary.duration_minutes,
            "services_affected": incident.summary.services_affected,
            "root_cause": {
                "primary": incident.summary.root_cause.primary,
                "secondary": incident.summary.root_cause.secondary,
                "contributing_factors": incident.summary.root_cause.contributing_factors or []
            },
            "logs": [
                {
                    "timestamp": log.timestamp,
                    "level": log.level,
                    "message": log.message
                }
                for log in incident.logs[-50:]  # Last 50 logs
            ],
            "metrics": [
                {
                    "timestamp": metric.timestamp,
                    "cpu_percent": metric.metrics.get("cpu_percent", 0),
                    "memory_mb": metric.metrics.get("memory_mb", 0),
                    "error_rate": metric.metrics.get("error_rate", 0)
                }
                for metric in incident.metrics[-10:]  # Last 10 metrics
            ]
        }

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response (may be wrapped in markdown)

        Args:
            response_text: Raw response from Gemini

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON cannot be extracted
        """
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract from markdown code blocks
            import re
            json_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
            matches = re.findall(json_pattern, response_text)

            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON object in the response
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, response_text)

            if matches:
                for match in matches:
                    try:
                        data = json.loads(match)
                        if "steps" in data:  # Validate it's our runbook format
                            return data
                    except json.JSONDecodeError:
                        continue

            logger.error("failed_to_extract_json", extra_fields={"response": response_text[:500]})
            raise ValueError("Could not extract valid JSON from Gemini response")

    def _construct_runbook(
        self,
        incident_id: str,
        incident_type: str,
        severity: str,
        runbook_data: Dict[str, Any],
        max_steps: int
    ) -> Runbook:
        """Construct Runbook object from Gemini response data

        Args:
            incident_id: Incident ID
            incident_type: Type of incident
            severity: Incident severity
            runbook_data: Parsed JSON from Gemini
            max_steps: Maximum steps to include

        Returns:
            Constructed Runbook object

        Raises:
            ValueError: If runbook data is invalid
        """
        try:
            # Parse steps
            steps_data = runbook_data.get("steps", [])
            if not steps_data:
                raise ValueError("No steps found in runbook data")

            steps = []
            for step_data in steps_data[:max_steps]:
                # Parse commands
                commands_data = step_data.get("commands", [])
                commands = [
                    RunbookCommand(
                        command=cmd.get("command", ""),
                        description=cmd.get("description", ""),
                        risk_level=cmd.get("risk_level", "medium"),
                        expected_output=cmd.get("expected_output"),
                        timeout_seconds=cmd.get("timeout_seconds", 30),
                        requires_approval=cmd.get("requires_approval", True)
                    )
                    for cmd in commands_data
                ]

                step = RunbookStep(
                    step_number=step_data.get("step_number", len(steps) + 1),
                    category=step_data.get("category", "remediation"),
                    title=step_data.get("title", f"Step {len(steps) + 1}"),
                    commands=commands,
                    prerequisite_steps=step_data.get("prerequisite_steps", []),
                    estimated_duration=step_data.get("estimated_duration", "1 minute")
                )
                steps.append(step)

            # Calculate total estimated time
            total_time = self._calculate_total_time(steps)

            # Get warnings and prerequisites
            warnings = runbook_data.get("warnings", [])
            prerequisites = runbook_data.get("prerequisites", [])

            runbook = Runbook(
                incident_id=incident_id,
                generated_at=datetime.utcnow().isoformat(),
                incident_type=incident_type,
                severity=severity,
                steps=steps,
                total_steps=len(steps),
                estimated_total_time=total_time,
                warnings=warnings,
                prerequisites=prerequisites
            )

            return runbook

        except Exception as e:
            logger.error(
                "runbook_construction_failed",
                extra_fields={"error": str(e), "runbook_data": runbook_data},
                exc_info=True
            )
            raise ValueError(f"Failed to construct runbook: {str(e)}")

    def _calculate_total_time(self, steps: List[RunbookStep]) -> str:
        """Calculate total estimated time from all steps

        Args:
            steps: List of runbook steps

        Returns:
            Total time string (e.g., "15 minutes")
        """
        total_minutes = 0

        for step in steps:
            duration = step.estimated_duration.lower()

            # Extract minutes from duration string
            if "second" in duration:
                # Convert seconds to minutes
                import re
                match = re.search(r'(\d+)\s*second', duration)
                if match:
                    seconds = int(match.group(1))
                    total_minutes += seconds / 60
            elif "minute" in duration:
                import re
                match = re.search(r'(\d+)\s*minute', duration)
                if match:
                    minutes = int(match.group(1))
                    total_minutes += minutes
            elif "hour" in duration:
                import re
                match = re.search(r'(\d+)\s*hour', duration)
                if match:
                    hours = int(match.group(1))
                    total_minutes += hours * 60

        # Round to nearest minute
        total_minutes = int(round(total_minutes))

        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minutes"
            return f"{hours} hour{'s' if hours != 1 else ''}"

    def validate_runbook(self, runbook: Runbook) -> RunbookValidationResult:
        """Validate runbook for safety and correctness

        Args:
            runbook: Runbook to validate

        Returns:
            Validation result with issues and warnings
        """
        issues = []
        warnings = []
        dangerous_commands = []

        for step in runbook.steps:
            for cmd_idx, command in enumerate(step.commands):
                # Validate command safety
                is_safe, risk_level, reason = validate_command_safety(command.command)

                if not is_safe:
                    issues.append(
                        f"Step {step.step_number}, Command {cmd_idx + 1}: {reason}"
                    )
                    dangerous_commands.append({
                        "step": step.step_number,
                        "command": command.command,
                        "reason": reason
                    })

                # Warn about high-risk commands
                if risk_level == "high" and not command.requires_approval:
                    warnings.append(
                        f"Step {step.step_number}: High-risk command should require approval"
                    )

                # Validate command is not empty
                if not command.command.strip():
                    issues.append(f"Step {step.step_number}: Empty command found")

        # Validate step order and prerequisites
        step_numbers = [step.step_number for step in runbook.steps]
        for step in runbook.steps:
            for prereq in step.prerequisite_steps:
                if prereq not in step_numbers:
                    warnings.append(
                        f"Step {step.step_number} references non-existent prerequisite step {prereq}"
                    )
                elif prereq >= step.step_number:
                    warnings.append(
                        f"Step {step.step_number} has invalid prerequisite {prereq} "
                        "(prerequisite must come before current step)"
                    )

        is_valid = len(issues) == 0

        return RunbookValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            dangerous_commands=dangerous_commands
        )


# Global instance
_runbook_generator = None


def get_runbook_generator() -> RunbookGenerator:
    """Get or create global runbook generator instance

    Returns:
        RunbookGenerator instance
    """
    global _runbook_generator
    if _runbook_generator is None:
        _runbook_generator = RunbookGenerator()
    return _runbook_generator
