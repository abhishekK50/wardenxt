"""
Voice Command Parser
Parses natural language voice commands and maps them to actions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.models.voice import VoiceCommand
from app.core.gemini_audio import get_gemini_audio
from app.core.logging import get_logger
from app.core.data_loader import DataLoader

logger = get_logger(__name__)


class VoiceCommandExecutor:
    """Executes parsed voice commands"""

    def __init__(self):
        self.gemini_audio = get_gemini_audio()
        self.data_loader = DataLoader()

    async def execute_command(self, command: VoiceCommand, context: Dict = None) -> Dict[str, Any]:
        """Execute a parsed voice command

        Args:
            command: Parsed voice command
            context: Additional context

        Returns:
            Execution result with response text and data
        """
        try:
            logger.info(
                "voice_command_execution_started",
                extra_fields={
                    "command_type": command.command,
                    "confidence": command.confidence,
                    "parameters": str(command.parameters)
                }
            )

            # Route to appropriate handler
            if command.command == "query":
                result = await self._handle_query(command.parameters)
            elif command.command == "analyze":
                result = await self._handle_analyze(command.parameters)
            elif command.command == "summarize":
                result = await self._handle_summarize(command.parameters)
            elif command.command == "status":
                result = await self._handle_status(command.parameters)
            else:
                result = {
                    "success": False,
                    "response": f"I don't know how to handle the command: {command.command}",
                    "data": None
                }

            logger.info(
                "voice_command_execution_completed",
                extra_fields={"command_type": command.command, "success": result.get("success", False)}
            )

            return result

        except Exception as e:
            logger.error(
                "voice_command_execution_failed",
                extra_fields={
                    "command_type": command.command,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "success": False,
                "response": "I encountered an error executing your command.",
                "data": None,
                "error": str(e)
            }

    async def _handle_query(self, parameters: Dict) -> Dict[str, Any]:
        """Handle incident query commands

        Args:
            parameters: Query parameters (severity, status, time_range, etc.)

        Returns:
            Query results
        """
        try:
            # Load all incidents
            incident_ids = self.data_loader.list_incidents()

            # Also check webhook incidents
            from app.api.webhooks import webhook_incidents
            webhook_incident_ids = list(webhook_incidents.keys())
            all_incident_ids = incident_ids + webhook_incident_ids

            incidents = []
            for incident_id in all_incident_ids:
                try:
                    if incident_id in webhook_incident_ids:
                        from app.api.webhooks import webhook_incident_data
                        incident = webhook_incident_data[incident_id]
                        incidents.append(incident.summary)
                    else:
                        incident = self.data_loader.load_incident(incident_id)
                        incidents.append(incident.summary)
                except Exception:
                    continue

            # Filter by parameters
            filtered = incidents

            # Filter by severity
            if "severity" in parameters:
                severity = parameters["severity"].upper()
                filtered = [inc for inc in filtered if inc.severity == severity]

            # Filter by status
            if "status" in parameters:
                status = parameters["status"].upper()
                filtered = [inc for inc in filtered if inc.status == status]

            # Sort by severity (P0 first)
            severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            filtered.sort(key=lambda x: severity_order.get(x.severity, 999))

            # Generate response
            if not filtered:
                response = "I couldn't find any incidents matching your criteria."
                return {
                    "success": True,
                    "response": response,
                    "data": {"incidents": [], "count": 0}
                }

            # Get the most critical one
            top_incident = filtered[0]

            if "severity" in parameters or len(filtered) == 1:
                # Specific query - describe the top result
                response = (
                    f"The most critical incident is {top_incident.incident_id}, "
                    f"a {top_incident.severity} {top_incident.incident_type.replace('_', ' ')} "
                    f"affecting {len(top_incident.services_affected)} services. "
                    f"Status: {top_incident.status}."
                )
            else:
                # General query - give overview
                response = (
                    f"There are {len(filtered)} incidents. "
                    f"The most critical is {top_incident.incident_id}, "
                    f"a {top_incident.severity} incident affecting {len(top_incident.services_affected)} services."
                )

            return {
                "success": True,
                "response": response,
                "data": {
                    "incidents": [inc.incident_id for inc in filtered[:5]],
                    "count": len(filtered),
                    "top_incident": top_incident.incident_id
                }
            }

        except Exception as e:
            logger.error("query_execution_failed", extra_fields={"error": str(e)}, exc_info=True)
            return {
                "success": False,
                "response": "I encountered an error querying incidents.",
                "data": None,
                "error": str(e)
            }

    async def _handle_analyze(self, parameters: Dict) -> Dict[str, Any]:
        """Handle incident analysis commands

        Args:
            parameters: Analysis parameters (incident_id)

        Returns:
            Analysis trigger result
        """
        try:
            incident_id = parameters.get("incident_id")

            if not incident_id:
                return {
                    "success": False,
                    "response": "I need an incident ID to analyze. Please specify which incident.",
                    "data": None
                }

            # Normalize incident ID format
            if not incident_id.startswith("INC-"):
                # Try to parse "zero zero zero one" -> "INC-2026-0001"
                # For simplicity, assume recent incident
                incident_id = f"INC-2026-{incident_id.replace(' ', '')}"

            response = (
                f"I'm starting analysis of incident {incident_id}. "
                f"This will take about 15 to 30 seconds. "
                f"I'll use Gemini AI to analyze logs, metrics, and timeline data."
            )

            return {
                "success": True,
                "response": response,
                "data": {
                    "incident_id": incident_id,
                    "action": "analyze",
                    "status": "queued"
                },
                "action_taken": f"analyze_{incident_id}"
            }

        except Exception as e:
            logger.error("analyze_execution_failed", extra_fields={"error": str(e)}, exc_info=True)
            return {
                "success": False,
                "response": "I encountered an error starting the analysis.",
                "data": None,
                "error": str(e)
            }

    async def _handle_summarize(self, parameters: Dict) -> Dict[str, Any]:
        """Handle summarization commands

        Args:
            parameters: Summary parameters

        Returns:
            Summary result
        """
        try:
            # Load all incidents
            incident_ids = self.data_loader.list_incidents()

            # Also check webhook incidents
            from app.api.webhooks import webhook_incidents
            webhook_incident_ids = list(webhook_incidents.keys())
            all_incident_ids = incident_ids + webhook_incident_ids

            total = len(all_incident_ids)

            # Count by severity
            incidents = []
            for incident_id in all_incident_ids[:50]:  # Limit for performance
                try:
                    if incident_id in webhook_incident_ids:
                        from app.api.webhooks import webhook_incident_data
                        incident = webhook_incident_data[incident_id]
                        incidents.append(incident.summary)
                    else:
                        incident = self.data_loader.load_incident(incident_id)
                        incidents.append(incident.summary)
                except Exception:
                    continue

            p0_count = len([i for i in incidents if i.severity == "P0"])
            p1_count = len([i for i in incidents if i.severity == "P1"])
            p2_count = len([i for i in incidents if i.severity == "P2"])

            investigating = len([i for i in incidents if i.status in ["DETECTED", "INVESTIGATING"]])
            resolved = len([i for i in incidents if i.status in ["RESOLVED", "CLOSED"]])

            response = (
                f"You have {total} total incidents. "
                f"{p0_count} are P0, {p1_count} are P1, and {p2_count} are P2. "
                f"{investigating} are currently being investigated, "
                f"and {resolved} have been resolved."
            )

            return {
                "success": True,
                "response": response,
                "data": {
                    "total": total,
                    "by_severity": {"P0": p0_count, "P1": p1_count, "P2": p2_count},
                    "by_status": {"investigating": investigating, "resolved": resolved}
                }
            }

        except Exception as e:
            logger.error("summarize_execution_failed", extra_fields={"error": str(e)}, exc_info=True)
            return {
                "success": False,
                "response": "I encountered an error generating the summary.",
                "data": None,
                "error": str(e)
            }

    async def _handle_status(self, parameters: Dict) -> Dict[str, Any]:
        """Handle status query commands

        Args:
            parameters: Status parameters

        Returns:
            Status information
        """
        try:
            # Load all incidents
            incident_ids = self.data_loader.list_incidents()

            # Also check webhook incidents
            from app.api.webhooks import webhook_incidents
            webhook_incident_ids = list(webhook_incidents.keys())
            all_incident_ids = incident_ids + webhook_incident_ids

            incidents = []
            for incident_id in all_incident_ids[:50]:
                try:
                    if incident_id in webhook_incident_ids:
                        from app.api.webhooks import webhook_incident_data
                        incident = webhook_incident_data[incident_id]
                        incidents.append(incident.summary)
                    else:
                        incident = self.data_loader.load_incident(incident_id)
                        incidents.append(incident.summary)
                except Exception:
                    continue

            investigating = [i for i in incidents if i.status in ["DETECTED", "INVESTIGATING"]]

            count = len(investigating)
            p0 = len([i for i in investigating if i.severity == "P0"])
            p1 = len([i for i in investigating if i.severity == "P1"])
            p2 = len([i for i in investigating if i.severity == "P2"])

            if count == 0:
                response = "There are no incidents currently being investigated. All clear!"
            else:
                response = (
                    f"There are {count} incidents currently being investigated. "
                    f"{p0} are P0, {p1} are P1, and {p2} are P2 priority."
                )

            return {
                "success": True,
                "response": response,
                "data": {
                    "investigating": count,
                    "by_severity": {"P0": p0, "P1": p1, "P2": p2},
                    "incident_ids": [i.incident_id for i in investigating[:5]]
                }
            }

        except Exception as e:
            logger.error("status_execution_failed", extra_fields={"error": str(e)}, exc_info=True)
            return {
                "success": False,
                "response": "I encountered an error checking status.",
                "data": None,
                "error": str(e)
            }


# Global instance
_executor = None

def get_command_executor() -> VoiceCommandExecutor:
    """Get or create global command executor"""
    global _executor
    if _executor is None:
        _executor = VoiceCommandExecutor()
    return _executor
