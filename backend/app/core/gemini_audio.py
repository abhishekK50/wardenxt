"""
Gemini Audio Integration
Handles audio transcription and text-to-speech using Gemini 2.0 Flash
"""

import base64
import os
from typing import Dict, Tuple
from google import genai

from app.config import settings
from app.core.logging import get_logger
from app.models.voice import VoiceResponse, VoiceCommand

logger = get_logger(__name__)


class GeminiAudio:
    """Gemini audio processing client"""

    def __init__(self):
        """Initialize Gemini client with API key"""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        # Use the configured model from settings for text operations
        self.model = settings.gemini_model
        # For audio/TTS, we need a model that supports it - try gemini-2.0-flash
        self.audio_model = "gemini-2.0-flash"

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio to text using Gemini

        Args:
            audio_bytes: Raw audio data
            mime_type: Audio MIME type (audio/wav, audio/mp3, audio/webm)

        Returns:
            Transcribed text
        """
        try:
            logger.info("audio_transcription_started", extra_fields={"mime_type": mime_type})

            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Send to Gemini for transcription
            response = self.client.models.generate_content(
                model=self.model,
                contents={
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_b64
                            }
                        },
                        {
                            "text": "Transcribe this voice query about incident management. Return only the transcribed text, nothing else."
                        }
                    ]
                }
            )

            transcript = response.text.strip()
            logger.info(
                "audio_transcription_completed",
                extra_fields={"transcript_length": len(transcript)}
            )

            return transcript

        except Exception as e:
            logger.error(
                "audio_transcription_failed",
                extra_fields={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")

    def generate_voice_response(
        self,
        text: str,
        voice_name: str = "Puck"
    ) -> bytes:
        """Generate speech audio from text using Gemini

        Args:
            text: Text to convert to speech
            voice_name: Voice to use (Puck, Charon, Kore, Fenrir)

        Returns:
            Audio bytes (WAV format)
        """
        try:
            logger.info(
                "voice_generation_started",
                extra_fields={"text_length": len(text), "voice": voice_name}
            )

            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": f"Please read this incident summary aloud: {text}"}]
                    }
                ],
                config={
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": voice_name
                            }
                        }
                    }
                }
            )

            # Extract audio from response
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            audio_bytes = base64.b64decode(audio_data)

            logger.info(
                "voice_generation_completed",
                extra_fields={"audio_size_bytes": len(audio_bytes)}
            )

            return audio_bytes

        except Exception as e:
            logger.error(
                "voice_generation_failed",
                extra_fields={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            raise RuntimeError(f"Failed to generate voice: {str(e)}")

    def process_voice_query(
        self,
        audio_bytes: bytes,
        mime_type: str,
        context: Dict = None
    ) -> Tuple[str, str, str]:
        """Process voice query: transcribe, understand, and generate response

        Args:
            audio_bytes: Audio data
            mime_type: Audio MIME type
            context: Optional context (current page, filters, etc.)

        Returns:
            Tuple of (transcript, response_text, intent)
        """
        try:
            # Step 1: Transcribe audio
            transcript = self.transcribe_audio(audio_bytes, mime_type)

            if not transcript:
                return "", "I couldn't understand what you said. Please try again.", "unknown"

            logger.info(
                "voice_query_processing",
                extra_fields={"transcript": transcript, "has_context": context is not None}
            )

            # Step 2: Understand intent and generate response using Gemini
            context_str = ""
            if context:
                context_str = f"\n\nContext: {context}"

            prompt = f"""You are WardenXT, an AI-powered incident commander. A user has asked you a question via voice.

User's question: "{transcript}"{context_str}

Analyze the question and provide:
1. The type of query (question/command/summary)
2. A helpful, concise response (1-2 sentences for voice playback)
3. Any incident IDs mentioned (format: INC-YYYY-MMDD-XXXX)

Format your response as:
TYPE: [question/command/summary]
RESPONSE: [Your natural language response]
INCIDENTS: [Comma-separated list of incident IDs, or "none"]

Example:
TYPE: question
RESPONSE: The most critical incident right now is INC-2026-0001, a P0 database failure affecting 2400 users.
INCIDENTS: INC-2026-0001

Keep responses conversational and suitable for text-to-speech."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

            response_text = response.text.strip()

            # Parse response
            intent = "question"  # default
            answer = "I'm processing your request..."

            lines = response_text.split('\n')
            for line in lines:
                if line.startswith('TYPE:'):
                    intent = line.split(':', 1)[1].strip()
                elif line.startswith('RESPONSE:'):
                    answer = line.split(':', 1)[1].strip()

            logger.info(
                "voice_query_understood",
                extra_fields={"intent": intent, "response_length": len(answer)}
            )

            return transcript, answer, intent

        except Exception as e:
            logger.error(
                "voice_query_processing_failed",
                extra_fields={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            return (
                transcript if 'transcript' in locals() else "",
                "I encountered an error processing your request. Please try again.",
                "error"
            )

    def parse_command(self, transcript: str) -> VoiceCommand:
        """Parse transcribed text into structured command

        Args:
            transcript: Transcribed voice text

        Returns:
            Structured VoiceCommand
        """
        try:
            prompt = f"""Parse this voice command into a structured format:

Command: "{transcript}"

Extract:
1. Command type: analyze, query, summarize, status
2. Parameters: incident_id, severity, time_range, etc.
3. Confidence: 0.0-1.0 (how confident you are in understanding)
4. Intent: what the user wants to do

Return JSON format:
{{
    "command": "string",
    "parameters": {{}},
    "confidence": 0.0,
    "intent": "string"
}}

Examples:
"Analyze incident zero zero zero one" -> {{"command": "analyze", "parameters": {{"incident_id": "INC-2026-0001"}}, "confidence": 0.95, "intent": "Run AI analysis on specific incident"}}
"Show me P1 incidents" -> {{"command": "query", "parameters": {{"severity": "P1"}}, "confidence": 0.9, "intent": "Filter incidents by severity"}}
"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )

            import json
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            command_data = json.loads(response_text)

            return VoiceCommand(
                command=command_data.get('command', 'unknown'),
                parameters=command_data.get('parameters', {}),
                confidence=command_data.get('confidence', 0.5),
                intent=command_data.get('intent', 'Unknown intent')
            )

        except Exception as e:
            logger.error(
                "command_parsing_failed",
                extra_fields={"error": str(e), "transcript": transcript},
                exc_info=True
            )
            # Return low-confidence unknown command
            return VoiceCommand(
                command="unknown",
                parameters={},
                confidence=0.0,
                intent="Could not parse command"
            )


# Global instance
_gemini_audio = None

def get_gemini_audio() -> GeminiAudio:
    """Get or create global Gemini audio instance"""
    global _gemini_audio
    if _gemini_audio is None:
        _gemini_audio = GeminiAudio()
    return _gemini_audio
