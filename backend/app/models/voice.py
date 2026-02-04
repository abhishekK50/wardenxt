"""
Voice Interface Models
Pydantic models for voice query and response handling
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class QueryType(str, Enum):
    """Type of voice query"""
    QUESTION = "question"  # User asking a question
    COMMAND = "command"    # User giving a command
    SUMMARY = "summary"    # User requesting a summary


class VoiceQuery(BaseModel):
    """Voice query request"""
    query_type: QueryType = QueryType.QUESTION
    context: Optional[Dict] = None  # Additional context (current page, filters, etc.)


class VoiceResponse(BaseModel):
    """Voice query response"""
    transcript: str = Field(..., description="What user said (transcribed)")
    response_text: str = Field(..., description="AI text response")
    audio_base64: Optional[str] = Field(None, description="Audio response in base64")
    action_taken: Optional[str] = Field(None, description="Action executed (if command)")
    incident_ids: Optional[List[str]] = Field(None, description="Related incident IDs")
    confidence: float = Field(default=1.0, description="Confidence in understanding query")


class VoiceCommand(BaseModel):
    """Parsed voice command"""
    command: str = Field(..., description="Command type (analyze, query, summarize)")
    parameters: Dict = Field(default_factory=dict, description="Command parameters")
    confidence: float = Field(..., description="Confidence in command understanding (0-1)")
    intent: str = Field(..., description="Interpreted user intent")


class VoiceCapability(BaseModel):
    """Available voice capability/command"""
    command: str = Field(..., description="Command name")
    examples: List[str] = Field(..., description="Example phrases")
    description: str = Field(..., description="What this command does")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")


class VoiceCapabilitiesResponse(BaseModel):
    """Response listing available voice capabilities"""
    capabilities: List[VoiceCapability]
    total_commands: int


class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "audio/wav"
    MP3 = "audio/mp3"
    WEBM = "audio/webm"
    OGG = "audio/ogg"


class VoiceSummaryRequest(BaseModel):
    """Request for voice summary of incident"""
    incident_id: str
    include_analysis: bool = Field(default=True, description="Include AI analysis in summary")
    voice_name: str = Field(default="Puck", description="Voice to use (Puck, Charon, Kore, Fenrir)")
