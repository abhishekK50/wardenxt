"""
Voice API Routes
Endpoints for voice-based interaction with WardenXT
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import Response
from typing import Dict, Optional
import base64

from app.models.voice import (
    VoiceQuery, VoiceResponse, VoiceCapabilitiesResponse,
    VoiceCapability, VoiceSummaryRequest
)
from app.core.gemini_audio import get_gemini_audio
from app.core.voice_commands import get_command_executor
from app.utils.audio import prepare_audio_for_gemini, convert_to_base64
from app.core.data_loader import DataLoader
from app.core.logging import get_logger
from app.auth.dependencies import get_optional_user

router = APIRouter(prefix="/voice", tags=["voice"])
logger = get_logger(__name__)

# Initialize services
gemini_audio = get_gemini_audio()
command_executor = get_command_executor()
data_loader = DataLoader()


@router.post("/query", response_model=VoiceResponse)
async def process_voice_query(
    audio: UploadFile = File(...),
    context: Optional[str] = None,
    current_user: dict = Depends(get_optional_user)
):
    """Process voice query: transcribe, understand, and generate response

    Args:
        audio: Audio file (WAV, MP3, WebM)
        context: Optional JSON context string
        current_user: Optional authenticated user

    Returns:
        Voice response with transcript, text, and audio
    """
    try:
        logger.info(
            "voice_query_received",
            extra_fields={
                "filename": audio.filename,
                "content_type": audio.content_type,
                "has_context": context is not None
            }
        )

        # Read audio data
        audio_data = await audio.read()

        # Prepare audio for Gemini
        prepared_audio, mime_type = prepare_audio_for_gemini(
            audio_data,
            audio.content_type
        )

        # Parse context if provided
        context_dict = None
        if context:
            import json
            try:
                context_dict = json.loads(context)
            except Exception as e:
                logger.warning("context_parse_failed", extra_fields={"error": str(e)})

        # Process voice query
        transcript, response_text, intent = gemini_audio.process_voice_query(
            prepared_audio,
            mime_type,
            context_dict
        )

        # Check if this is a command
        incident_ids = []
        action_taken = None

        if intent in ["command", "analyze"]:
            # Parse as command
            command = gemini_audio.parse_command(transcript)

            # Execute command
            result = await command_executor.execute_command(command, context_dict)

            if result.get("success"):
                response_text = result["response"]
                action_taken = result.get("action_taken")

                # Extract incident IDs from result
                if result.get("data") and "incident_ids" in result["data"]:
                    incident_ids = result["data"]["incident_ids"]
                elif result.get("data") and "incident_id" in result["data"]:
                    incident_ids = [result["data"]["incident_id"]]

        # Generate audio response
        try:
            audio_bytes = gemini_audio.generate_voice_response(response_text)
            audio_base64 = convert_to_base64(audio_bytes)
        except Exception as e:
            logger.error(
                "audio_generation_failed",
                extra_fields={"error": str(e)},
                exc_info=True
            )
            audio_base64 = None  # Return text-only response

        logger.info(
            "voice_query_completed",
            extra_fields={
                "transcript_length": len(transcript),
                "response_length": len(response_text),
                "has_audio": audio_base64 is not None,
                "incident_count": len(incident_ids)
            }
        )

        return VoiceResponse(
            transcript=transcript,
            response_text=response_text,
            audio_base64=audio_base64,
            action_taken=action_taken,
            incident_ids=incident_ids if incident_ids else None,
            confidence=0.9  # Default high confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "voice_query_failed",
            extra_fields={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process voice query: {str(e)}"
        )


@router.get("/speak/{incident_id}")
async def speak_incident_summary(
    incident_id: str,
    include_analysis: bool = True,
    voice_name: str = "Puck",
    current_user: dict = Depends(get_optional_user)
):
    """Generate voice summary of incident

    Args:
        incident_id: Incident to summarize
        include_analysis: Include AI analysis in summary
        voice_name: Voice to use (browser TTS will be used)

    Returns:
        JSON with summary text for browser TTS
    """
    try:
        logger.info(
            "voice_summary_requested",
            extra_fields={
                "incident_id": incident_id,
                "include_analysis": include_analysis,
                "voice": voice_name
            }
        )

        # Load incident
        try:
            # Check webhook incidents first
            from app.api.webhooks import webhook_incidents, webhook_incident_data
            if incident_id in webhook_incident_data:
                incident = webhook_incident_data[incident_id]
                summary_data = incident.summary
            else:
                incident = data_loader.load_incident(incident_id)
                summary_data = incident.summary
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {incident_id} not found"
            )

        # Generate summary text
        summary_text = f"{summary_data.title}. "
        summary_text += f"This is a {summary_data.severity} priority incident "
        summary_text += f"affecting {len(summary_data.services_affected)} services. "

        if summary_data.users_impacted:
            summary_text += f"Approximately {summary_data.users_impacted} users are impacted. "

        if summary_data.duration_minutes:
            hours = summary_data.duration_minutes // 60
            minutes = summary_data.duration_minutes % 60
            if hours > 0:
                summary_text += f"Duration: {hours} hours and {minutes} minutes. "
            else:
                summary_text += f"Duration: {minutes} minutes. "

        summary_text += f"Current status: {summary_data.status}. "

        if summary_data.root_cause and summary_data.root_cause.primary:
            summary_text += f"Root cause: {summary_data.root_cause.primary}. "

        # Add mitigation steps
        if summary_data.mitigation_steps and len(summary_data.mitigation_steps) > 0:
            summary_text += "Mitigation steps include: "
            summary_text += ". ".join(summary_data.mitigation_steps[:3]) + "."

        logger.info(
            "voice_summary_generated",
            extra_fields={
                "incident_id": incident_id,
                "summary_length": len(summary_text),
                "use_browser_tts": True
            }
        )

        # Return text for browser TTS (Gemini models don't support audio output)
        return {
            "incident_id": incident_id,
            "summary_text": summary_text,
            "use_browser_tts": True,
            "title": summary_data.title,
            "severity": summary_data.severity,
            "status": summary_data.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "voice_summary_failed",
            extra_fields={
                "incident_id": incident_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate voice summary: {str(e)}"
        )


@router.post("/command")
async def execute_voice_command(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_optional_user)
):
    """Execute voice command

    Args:
        audio: Audio file with command
        current_user: Optional authenticated user

    Returns:
        Command execution result
    """
    try:
        logger.info("voice_command_received", extra_fields={"filename": audio.filename})

        # Read and prepare audio
        audio_data = await audio.read()
        prepared_audio, mime_type = prepare_audio_for_gemini(audio_data, audio.content_type)

        # Transcribe
        transcript = gemini_audio.transcribe_audio(prepared_audio, mime_type)

        # Parse as command
        command = gemini_audio.parse_command(transcript)

        # Execute
        result = await command_executor.execute_command(command)

        logger.info(
            "voice_command_executed",
            extra_fields={
                "command_type": command.command,
                "success": result.get("success", False),
                "confidence": command.confidence
            }
        )

        return {
            "transcript": transcript,
            "command": command.command,
            "confidence": command.confidence,
            "result": result
        }

    except Exception as e:
        logger.error(
            "voice_command_failed",
            extra_fields={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute voice command: {str(e)}"
        )


@router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
async def get_voice_capabilities():
    """Get list of available voice commands

    Returns:
        List of voice capabilities
    """
    capabilities = [
        VoiceCapability(
            command="query_critical",
            examples=[
                "What's the most critical incident?",
                "Show me the worst incident",
                "What's the highest priority issue?"
            ],
            description="Find the most critical incident",
            parameters=[]
        ),
        VoiceCapability(
            command="query_by_severity",
            examples=[
                "Show me P1 incidents",
                "List all P0 issues",
                "What are the P2 incidents?"
            ],
            description="Filter incidents by severity",
            parameters=["severity"]
        ),
        VoiceCapability(
            command="analyze_incident",
            examples=[
                "Analyze incident 0001",
                "Run analysis on incident INC-2026-0001",
                "Investigate incident 0002"
            ],
            description="Trigger AI analysis on specific incident",
            parameters=["incident_id"]
        ),
        VoiceCapability(
            command="summarize_all",
            examples=[
                "Summarize all incidents",
                "Give me an overview",
                "What's the current status?"
            ],
            description="Get summary of all incidents",
            parameters=[]
        ),
        VoiceCapability(
            command="status_check",
            examples=[
                "How many incidents are being investigated?",
                "What's the current incident count?",
                "Show me investigating incidents"
            ],
            description="Check current incident status",
            parameters=[]
        ),
        VoiceCapability(
            command="time_based_query",
            examples=[
                "What happened today?",
                "Show me yesterday's incidents",
                "What happened this week?"
            ],
            description="Query incidents by time range",
            parameters=["time_range"]
        )
    ]

    return VoiceCapabilitiesResponse(
        capabilities=capabilities,
        total_commands=len(capabilities)
    )


@router.get("/health")
async def voice_health_check():
    """Health check for voice services

    Returns:
        Health status
    """
    try:
        # Test Gemini connection
        test_text = "Test"
        gemini_audio.client.models.generate_content(
            model=gemini_audio.model,
            contents=[{"role": "user", "parts": [{"text": test_text}]}]
        )

        return {
            "status": "healthy",
            "gemini_model": gemini_audio.model,
            "capabilities": ["transcription", "text_to_speech", "command_parsing"]
        }
    except Exception as e:
        logger.error("voice_health_check_failed", extra_fields={"error": str(e)}, exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }
